"""
Dedicated refresh token endpoint for OAuth 2.0 token refresh with rotation.
Implements RFC 9700 security best practices for refresh token handling.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.auth import (
    AUTH_COOKIE_PREFIX,
    extract_auth_cookies,
    set_auth_cookies,
    try_refresh_token,
)
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["authentication"])


class TokenRefreshError(Exception):
    """Custom exception for token refresh failures."""

    pass


@router.post("/refresh-auth-token")
async def refresh_auth_token(request: Request, response: Response) -> dict[str, Any]:
    """
    Dedicated endpoint for OAuth 2.0 token refresh with cookie management.

    Implements refresh token rotation as per RFC 9700 OAuth 2.0 Security Best Practices:
    - Validates refresh token from secure httpOnly cookie
    - Performs token refresh with automatic rotation
    - Updates all authentication cookies (access_token, refresh_token, id_token)
    - Provides clear error responses for frontend handling

    Returns:
        Success response with token metadata, or 401 if refresh fails

    Raises:
        HTTPException: 401 if no refresh token or refresh fails
    """
    try:
        logger.debug("Processing token refresh request")

        # Step 1: Extract refresh token from secure cookies
        try:
            auth_data = extract_auth_cookies(request.cookies)
            refresh_token = auth_data["refresh_token"]
            logger.debug("Successfully extracted refresh token from cookies")
        except Exception as e:
            logger.info(f"No valid refresh token found in cookies: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "no_refresh_token",
                    "message": "No refresh token available. Please re-authenticate.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Step 2: Attempt token refresh with CERN OIDC
        try:
            new_token_data = await try_refresh_token(refresh_token)

            if new_token_data is None:
                # Refresh token is inactive/invalid
                logger.info("Refresh token is inactive or invalid")
                raise TokenRefreshError("Refresh token is no longer valid")

            logger.debug("Successfully refreshed tokens from CERN OIDC")

        except TokenRefreshError:
            raise  # Re-raise our custom exception
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
            raise TokenRefreshError(f"Token refresh failed: {str(e)}")

        # Step 3: Update cookies with new tokens (including id_token)
        try:
            set_auth_cookies(
                response=response,
                access_token=new_token_data.get("access_token", ""),
                refresh_token=new_token_data.get("refresh_token", ""),
                id_token=new_token_data.get("id_token", ""),
                max_age=36000,  # 10 hours
            )

            print("TEST:", new_token_data)

            logger.info(
                "Successfully updated authentication cookies with refreshed tokens"
            )

            # Step 4: Return success response with token metadata
            return {
                "status": "success",
                "message": "Tokens refreshed successfully",
                "expires_in": new_token_data.get("expires_in", 3600),
                "token_type": "Bearer",
                "scope": new_token_data.get("scope", "openid email profile"),
            }

        except Exception as e:
            logger.error(f"Failed to set authentication cookies: {e}", exc_info=True)
            raise TokenRefreshError(
                f"Failed to update authentication cookies: {str(e)}"
            )

    except TokenRefreshError as e:
        # Clear all authentication cookies on refresh failure
        logger.info(f"Token refresh failed, clearing cookies: {e}")

        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-access-token")
        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-refresh-token")
        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-id-token")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "refresh_failed",
                "message": "Token refresh failed. Please re-authenticate.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error in refresh endpoint: {e}", exc_info=True)

        # Clear cookies on unexpected errors too
        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-access-token")
        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-refresh-token")
        response.delete_cookie(f"{AUTH_COOKIE_PREFIX}-id-token")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "message": "An unexpected error occurred during token refresh.",
            },
        )
