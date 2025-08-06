from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse

from app.auth import (
    clear_auth_cookies,
    extract_auth_cookies,
    get_logout_url,
    set_auth_cookies,
    try_refresh_token,
    validate_token_and_get_user,
)
from app.storage.database import Database
from app.utils import get_config, get_logger
from app.utils.errors import ErrorTypes, server_error, unauthenticated_error

logger = get_logger(__name__)
config = get_config()

router = APIRouter(prefix="", tags=["authentication"])
FRONTEND_URL = config.get("general.FRONTEND_URL")
AUTH_COOKIE_PREFIX = f"{config.get('general.COOKIE_PREFIX')}-auth"
CERN_CLIENT_ID = config.get("general.CERN_CLIENT_ID")
CERN_CLIENT_SECRET = config.get("general.CERN_CLIENT_SECRET")
CERN_OIDC_URL = config.get("auth.cern_oidc_url")

# This will be injected from main.py
database: Database


def init_dependencies(db: Database) -> None:
    """Initialize dependencies for this router."""
    global database
    database = db


# OAuth setup
oauth = OAuth()
oauth.register(
    name="provider",
    server_metadata_url=CERN_OIDC_URL,
    client_id=CERN_CLIENT_ID,
    client_secret=CERN_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid email profile",
    },
)

redirect_uri = config.get("general.CERN_REDIRECT_URI")


class TokenRefreshError(Exception):
    """Custom exception for token refresh failures."""

    pass


@router.post("/refresh-auth-token")
async def refresh_auth_token(request: Request, response: Response) -> JSONResponse:
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
            raise unauthenticated_error(
                error_type=ErrorTypes.NO_REFRESH_TOKEN,
                message="No refresh token available. Please re-authenticate.",
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
                access_token=new_token_data["access_token"],
                refresh_token=new_token_data["refresh_token"],
                id_token=new_token_data["id_token"],
                max_age=new_token_data["expires_in"],
            )

            logger.info(
                "Successfully updated authentication cookies with refreshed tokens"
            )

            # Step 4: Return success response with token metadata
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Tokens refreshed successfully",
                },
            )

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

        raise unauthenticated_error(
            error_type=ErrorTypes.REFRESH_FAILED,
            message="Token refresh failed. Please re-authenticate.",
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

        raise server_error(
            error_type=ErrorTypes.INTERNAL_ERROR,
            message="An unexpected error occurred during token refresh.",
        )


@router.get("/login")
async def login(request: Request) -> Any:
    """Initiate OAuth login with CERN."""
    request.session.clear()
    return await oauth.provider.authorize_redirect(request, redirect_uri)


@router.get("/auth")
async def auth(request: Request) -> Any:
    """OAuth callback route for authentication."""

    if request.query_params.get("error"):
        error_description = request.query_params.get("error_description")
        logger.error(f"Error authenticating user: {error_description}")
        return JSONResponse(
            content={"error": error_description}, status_code=status.HTTP_403_FORBIDDEN
        )

    # Get required information from auth service callback URL
    state = request.query_params.get("state")
    params = {
        "code": request.query_params.get("code"),
        "state": state,
    }

    # Format the params with additional information required for auth service validation
    state_data = await oauth.provider.framework.get_state_data(request.session, state)
    await oauth.provider.framework.clear_state_data(request.session, state)
    params = oauth.provider._format_state_params(state_data, params)

    # Get the auth token object from the auth service
    token_data: dict[str, Any] = await oauth.provider.fetch_access_token(**params)

    # We redirect user to the frontend's main page after successful login
    response = RedirectResponse(url=FRONTEND_URL)

    # Set all cookies required for authentication and token management
    set_auth_cookies(
        response,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        id_token=token_data["id_token"],
        # nonce=state_data["nonce"],
    )

    return response


@router.get("/logout")
async def logout(request: Request) -> JSONResponse:
    """Clear all authentication cookies, session, and get CERN SSO logout URL."""

    # Clear the session
    request.session.clear()

    # Get logout URL from well-known endpoints
    cern_logout_url = await get_logout_url()

    # Create response with logout URL
    response = JSONResponse(content={"logout_url": cern_logout_url})

    # Clear all authentication cookies using helper function
    clear_auth_cookies(response)

    return response


@router.get("/session-status")
async def get_session_status(request: Request) -> JSONResponse:
    """Get current session authentication status."""

    logger.debug("Received cookies: %s", request.cookies)

    try:
        # Extract and decode authentication cookies
        auth_data = extract_auth_cookies(request.cookies)
        access_token = auth_data["access_token"]
        refresh_token = auth_data["refresh_token"]
        id_token = auth_data["id_token"]
        # nonce = auth_data["nonce"]
    except Exception as e:
        error_message = f"""Failed to parse and validate required auth cookies.
            Most likely user is not authenticated so we are returning status code 200: {e}"""
        logger.warning(error_message)
        return JSONResponse(
            content={"authenticated": False, "user": None},
            status_code=status.HTTP_200_OK,
        )

    try:
        # Validate tokens and get user info
        userinfo = await validate_token_and_get_user(access_token, id_token, oauth)
        return JSONResponse(content={"authenticated": True, "user": userinfo})
    except Exception as e:
        logger.info(
            f"Failed to validate authentication of the user. Going to try refreshing their token now. Error: {e}"
        )

        # Try to refresh the token to see if we might get a valid token first before failing to authenticate
        try:
            new_token_data = await try_refresh_token(refresh_token)
            if new_token_data is None:
                # Token refresh failed due to inactive/invalid token
                return JSONResponse(
                    content={"authenticated": False, "user": None},
                    status_code=status.HTTP_401_UNAUTHORIZED,
                )

            # Parse the new token data to get user info using the correct approach
            data = {"token": new_token_data, "nonce": None}

            userinfo = await oauth.provider.parse_id_token(**data)
            logger.debug("Received userinfo from refreshed token: %s", userinfo)

            # Create the response and set the new cookies
            response = JSONResponse(content={"authenticated": True, "user": userinfo})
            set_auth_cookies(
                response,
                access_token=new_token_data["access_token"],
                refresh_token=new_token_data["refresh_token"],
                id_token=new_token_data["id_token"],
                # nonce=nonce,
            )

            return response

        except Exception as e:
            logger.info(
                f"Failed to refresh auth token, user is not authenticated. Error: {e}"
            )

            # Use proper error response for authentication failures
            raise unauthenticated_error(
                error_type=ErrorTypes.SESSION_ERROR,
                message="Session validation failed - unable to refresh expired tokens",
                user_message="Your session has expired and could not be refreshed. Please log in again.",
            )
