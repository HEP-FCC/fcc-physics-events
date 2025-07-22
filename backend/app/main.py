"""
This is the main FastAPI application file, which orchestrates the API,
database connections, and data processing modules.
"""

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, Response

from app.auth import cern_auth
from app.gclql_query_parser import QueryParser
from app.models.dataset import DatasetUpdate
from app.routers import api as api_router
from app.routers import auth as auth_router
from app.routers import entities as entities_router
from app.routers import utility as utility_router
from app.storage.database import Database
from app.utils import Config, get_config, get_logger, setup_logging

security = HTTPBearer(auto_error=False)


async def get_and_validate_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get current user from bearer token with CERN validation."""
    try:
        jwt_token = cern_auth._normalize_bearer_token(credentials.credentials)
        # TODO: potentially jwt token?
        token = cern_auth.jwt_decode_token(jwt_token)
        user_data = await cern_auth.validate_user_from_token(token)

        return user_data
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Token validation failed. Error: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_and_validate_user_from_session(request: Request) -> dict[str, Any]:
    """Get current user from session cookie with CERN validation."""
    try:
        # Check if session has auth info
        token = request.session.get("token")
        user = request.session.get("user")

        if not token or not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please login.",
            )

        # Validate the token with CERN
        decoded_token = cern_auth.jwt_decode_token(token)
        user_data = await cern_auth.validate_user_from_token(decoded_token)

        return user_data
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during session validation: {e}")
        raise HTTPException(
            status_code=401,
            detail="Session validation failed. Please login again.",
        )


logger = get_logger(__name__)
config = get_config()

redirect_uri = config.get("general.CERN_REDIRECT_URI")


database = Database()
query_parser = QueryParser(database=database)


# Pydantic model for the entity IDs request
# TODO: move to models
class EntityIdsRequest(BaseModel):
    entity_ids: list[int]


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


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Handles application startup and shutdown events."""
    setup_logging()
    await database.setup(config.get("database"))
    await query_parser.setup()
    yield
    await database.aclose()


app = FastAPI(
    title="FCC Physics Events API",
    description="API for querying and managing FCC physics events.",
    lifespan=lifespan,
)


app.add_middleware(
    SessionMiddleware,
    secret_key=config.get("general.SECRET_KEY"),
    https_only=config.get("general.HTTPS_ONLY", "false").lower() == "true",
    same_site="lax",
    max_age=3600,
    session_cookie="fcc_physics_events_web",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        config.get("general.FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:3000",
        "https://fcc-physics-events-dev.web.cern.ch",
        "https://fcc-physics-events.web.cern.ch",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to log incoming requests."""
    try:
        response = await call_next(request)

        # Log the request after successful processing
        logger.info(
            f"[{response.status_code}] {request.method} {request.url.path} - {request.query_params}"
            if request.query_params
            else f"[{response.status_code}] {request.method} {request.url.path}"
        )

        return response
    except Exception as e:
        logger.error(f"Middleware error for {request.method} {request.url.path}: {e}")
        raise


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, _: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return a 500 response."""
    logger.error(
        f"Unhandled exception for {request.method} {request.url}", exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )


# Initialize router dependencies
auth_router.init_dependencies(database)
entities_router.init_dependencies(database, query_parser)
api_router.init_dependencies(database)

# Include routers
app.include_router(utility_router.router)
app.include_router(auth_router.router)
app.include_router(entities_router.router)
app.include_router(api_router.router)
