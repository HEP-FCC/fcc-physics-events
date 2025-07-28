"""
Production-ready authentication module for CERN SSO integration.
Handles JWT token validation, CERN OAuth introspection, and secure token management.
"""

import logging
from typing import Any

import httpx
import jwt
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils import get_config, get_logger

# Load configuration
logger = get_logger(__name__)
config = get_config()

# Get auth configuration
MIN_TOKEN_LENGTH = config.get("auth.min_token_length", 10)
CERN_OIDC_URL = config.get(
    "auth.cern_oidc_url",
    "https://auth.cern.ch/auth/realms/cern/.well-known/openid-configuration",
)
CERN_ISSUER = config.get("auth.cern_issuer", "https://auth.cern.ch/auth/realms/cern")


class CERNAuthenticator:
    """Production-ready CERN authentication handler with improved error handling and caching."""

    def __init__(self) -> None:
        self.cern_oidc_config: dict[str, Any] | None = None
        self.jwks_keys: dict[str, Any] | None = None
        self.config_cache_time: float = 0.0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def _fetch_with_retry(
        self, url: str, timeout: float = 10.0
    ) -> dict[str, Any]:
        """Fetch data from URL with retry logic using tenacity."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result

    async def get_jwks_keys(self) -> dict[str, Any]:
        oidc_config = await self._fetch_with_retry(CERN_OIDC_URL)
        return await self._fetch_with_retry(oidc_config["jwks_uri"])

    def _get_signing_key(self, kid: str, jwks: dict[str, Any]) -> str:
        """Extract and return the signing key for the given key ID."""
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return str(jwt.algorithms.RSAAlgorithm.from_jwk(key))
        raise Exception(f"Key ID {kid} not found in the JWS keys: {jwks}")

    async def introspect_token(self, token: str) -> dict[str, Any]:
        """Introspect a token using CERN's OAuth introspection endpoint."""
        oidc_config = await self._fetch_with_retry(CERN_OIDC_URL)

        introspection_endpoint = oidc_config["introspection_endpoint"]

        # TODO: post with retry, or rather better retrying client
        async with httpx.AsyncClient() as client:
            response = await client.post(
                introspection_endpoint,
                data={
                    "token": token,
                    "client_id": config.get("general.CERN_CLIENT_ID", ""),
                    "client_secret": config.get("general.CERN_CLIENT_SECRET", ""),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
            response.raise_for_status()
            user_data: dict[str, Any] = response.json()

            username = user_data.get("preferred_username", "unknown")
            if not user_data["active"]:
                # When CERN tokens become inactive, it's typically due to expiration
                raise jwt.ExpiredSignatureError(f"Auth token for user {username} has expired.")

            logger.info(f"Successfully introspected token for user: {username}")
            return user_data

    async def validate_user_from_token(self, token: str) -> dict[str, Any]:
        user_data = await self.introspect_token(token)
        return user_data

    def _normalize_bearer_token(self, token: str) -> str:
        """Remove Bearer prefix from token if present."""
        if token.lower().startswith("bearer "):
            return token[7:]
        return token

    @staticmethod
    def jwt_encode_token(
        token: str,
    ) -> str:
        payload = {"token": token}
        return jwt.encode(payload, config["general.SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def jwt_decode_token(jwt_encoded_token: str) -> str:
        payload: dict[str, str] = jwt.decode(
            jwt_encoded_token,
            config["general.SECRET_KEY"],
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": False},
        )
        return payload["token"]

    @staticmethod
    def has_user_access(user_data: dict[str, Any]) -> bool:
        """
        Check if the user has the required role for authorization.
        Returns True if user is authorized, False otherwise.
        """
        if not (required_role := config.get("general.REQUIRED_CERN_ROLE")):
            logger.warning(
                "No specific role required, allowing all authenticated users"
            )
            return True

        user_roles = user_data.get("cern_roles", [])
        return required_role in user_roles


# Global authenticator instance
cern_auth = CERNAuthenticator()
