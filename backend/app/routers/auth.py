from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, RedirectResponse

from app.auth import cern_auth
from app.storage.database import Database
from app.utils import get_config, get_logger

logger = get_logger(__name__)
config = get_config()

router = APIRouter(prefix="", tags=["authentication"])

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
    server_metadata_url="https://auth.cern.ch/auth/realms/cern/.well-known/openid-configuration",
    client_id=config.get("general.CERN_CLIENT_ID", "client-id"),
    client_secret=config.get("general.CERN_CLIENT_SECRET"),
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
    """OAuth callback route for CERN authentication."""
    payload: dict[str, Any] = await oauth.cern.authorize_access_token(request)

    userinfo: dict[str, Any] = payload["userinfo"]
    # NOTE: User's can still have up to 1 day after being revoked permissions currently!
    if not cern_auth.has_user_access(userinfo):
        # Redirect to frontend with error
        frontend_url = config.get("general.FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}?error=access_denied")

    jwt_encoded_token = cern_auth.jwt_encode_token(payload["access_token"])

    # Store auth info in session for cookie-based authentication
    request.session["token"] = jwt_encoded_token
    request.session["user"] = {
        "given_name": userinfo["given_name"],
        "family_name": userinfo["family_name"],
        "preferred_username": userinfo.get("preferred_username"),
    }
    # Redirect back to frontend after successful authentication
    frontend_url = config.get("general.FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=frontend_url)


@router.get("/logout")
async def logout(request: Request) -> JSONResponse:
    """Get CERN SSO logout URL and clear session."""

    # Clear the session
    request.session.clear()

    # Return CERN SSO logout URL
    # TODO: FroGet this the well known endpoint
    cern_logout_url = (
        "https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/logout"
    )
    return JSONResponse(content={"logout_url": cern_logout_url})


@router.get("/session-status")
async def get_session_status(request: Request) -> JSONResponse:
    """Get current session authentication status."""
    token = request.session.get("token")
    user = request.session.get("user")

    if token and user:
        return JSONResponse(content={"authenticated": True, "user": user})
    else:
        return JSONResponse(content={"authenticated": False, "user": None})
