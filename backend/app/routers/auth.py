from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, RedirectResponse

from app.auth import (
    extract_auth_cookies,
    get_logout_url,
    set_auth_cookies,
    try_refresh_token,
    validate_token_and_get_user,
)
from app.storage.database import Database
from app.utils import get_config, get_logger

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
    name="cern",
    server_metadata_url=CERN_OIDC_URL,
    client_id=CERN_CLIENT_ID,
    client_secret=CERN_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid email profile",
    },
)

redirect_uri = config.get("general.CERN_REDIRECT_URI")


@router.get("/login")
async def login(request: Request) -> Any:
    """Initiate OAuth login with CERN."""
    request.session.clear()
    return await oauth.cern.authorize_redirect(request, redirect_uri)


@router.get("/auth")
async def auth(request: Request) -> Any:
    """OAuth callback route for authentication."""

    if request.query_params.get("error"):
        error_description = request.query_params.get("error_description")
        logger.error(f"Error authenticating user: {error_description}")
        return JSONResponse(content={"error": error_description}, status_code=403)

    # Get required information from auth service callback URL
    state = request.query_params.get("state")
    params = {
        "code": request.query_params.get("code"),
        "state": state,
    }

    # Format the params with additional information required for auth service validation
    state_data = await oauth.cern.framework.get_state_data(request.session, state)
    await oauth.cern.framework.clear_state_data(request.session, state)
    params = oauth.cern._format_state_params(state_data, params)

    # Get the auth token object from the auth service
    token_data: dict[str, Any] = await oauth.cern.fetch_access_token(**params)

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
    """Get CERN SSO logout URL and clear session."""

    # Clear the session
    request.session.clear()

    # Get logout URL from well-known endpoints
    cern_logout_url = await get_logout_url()
    return JSONResponse(content={"logout_url": cern_logout_url})


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
        logger.error(error_message)
        return JSONResponse(
            content={"authenticated": False, "user": None}, status_code=200
        )

    try:
        # Validate tokens and get user info
        userinfo = await validate_token_and_get_user(
            access_token, id_token, nonce, oauth
        )
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
                    status_code=401,
                )

            # Parse the new token data to get user info using the correct approach
            data = {"token": new_token_data, "nonce": None}

            userinfo = await oauth.cern.parse_id_token(**data)
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
            return JSONResponse(
                content={"authenticated": False, "user": None}, status_code=403
            )
