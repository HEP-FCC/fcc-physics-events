"""
This is the main FastAPI application file, which orchestrates the API,
database connections, and data processing modules.
"""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from authlib.integrations.starlette_client import OAuth
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse, RedirectResponse, Response

from app.auth import cern_auth
from app.config import get_config
from app.gclql_query_parser import QueryParser
from app.logging import get_logger, setup_logging
from app.models.dataset import DatasetUpdate, PaginatedDatasetSearchResponse
from app.models.dropdown import DropdownItem
from app.storage.database import Database

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


logger = get_logger(__name__)
config = get_config()

redirect_uri = config.get("general.CERN_REDIRECT_URI")


database = Database()
query_parser = QueryParser(database=database)


# Pydantic model for the dataset IDs request
# TODO: move to models
class DatasetIdsRequest(BaseModel):
    dataset_ids: list[int]


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


@app.get("/login")
async def login(request: Request) -> Any:
    """Initiate OAuth login with CERN."""
    request.session.clear()
    return await oauth.cern.authorize_redirect(request, redirect_uri)  # type: ignore


@app.get("/auth")
async def auth(request: Request) -> JSONResponse:
    """OAuth callback route for CERN authentication."""
    payload: dict[str, Any] = await oauth.cern.authorize_access_token(request)

    userinfo: dict[str, Any] = payload["userinfo"]
    # TODO: User's can still have up to 1 day after eing revoked permissions currently!
    if not cern_auth.has_user_access(userinfo):
        return JSONResponse(
            content={
                "error": "No bueno. User doesn't have required role to access this resource."
            }
        )

    jwt_encoded_token = cern_auth.jwt_encode_token(payload["access_token"])
    return JSONResponse(
        content={
            "token": jwt_encoded_token,
            "user": {
                "given_name": userinfo["given_name"],
                "family_name": userinfo["family_name"],
                "preferred_username": userinfo.get("preferred_username"),
            },
        }
    )


# TODO: logout button/api method


@app.get("/test")
async def test(creds=Depends(security)) -> None:
    # token = "eyJfc3RhdGVfY2Vybl9DYW9pa0Fma2JCM2tkWjllQTNvNHBqZzNjY1hKM2UiOiB7ImRhdGEiOiB7InJlZGlyZWN0X3VyaSI6ICJodHRwOi8vbG9jYWxob3N0OjMwMDAvYXV0aC1jYWxsYmFjayIsICJub25jZSI6ICJhMDBIeEc1a1pLem5wb0tIOExrRCIsICJ1cmwiOiAiaHR0cHM6Ly9hdXRoLmNlcm4uY2gvYXV0aC9yZWFsbXMvY2Vybi9wcm90b2NvbC9vcGVuaWQtY29ubmVjdC9hdXRoP3Jlc3BvbnNlX3R5cGU9Y29kZSZjbGllbnRfaWQ9ZmNjLXBoeXNpY3MtZXZlbnRzLXdlYiZyZWRpcmVjdF91cmk9aHR0cCUzQSUyRiUyRmxvY2FsaG9zdCUzQTMwMDAlMkZhdXRoLWNhbGxiYWNrJnNjb3BlPW9wZW5pZCtlbWFpbCtwcm9maWxlJnN0YXRlPUNhb2lrQWZrYkIza2RaOWVBM280cGpnM2NjWEozZSZub25jZT1hMDBIeEc1a1pLem5wb0tIOExrRCJ9LCAiZXhwIjogMTc1Mjc0MDU5OS4wMDI1Njk3fX0=.aHik5w.qDJJ17PyY-aYinR5XiV3wVfzqt8"
    # token = cern_auth.jwt_decode_token(jwt_encoded_token)
    print(creds)

    # request.query_params = {
    #     "state": "TKSXSpvfgy9QnOCXD16ItlGybN9KNK",
    #     "code": "3deef8dd-3068-4fa6-980b-d447df9e4071.fa7fb49d-0882-4f5a-9c73-22bb55d1adb8.344a5f4d-9e0d-473b-96b6-a504919aaf47",
    # }
    # print(await oauth.cern.authorize_access_token(request))


@app.get("/")
async def root() -> list[dict[str, set[str]]]:
    url_list = [{route.path: route.methods} for route in app.routes]  # type: ignore
    return url_list


@app.post("/upload-fcc-dict/", status_code=202)
async def upload_fcc_dictionary(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(get_and_validate_user_from_token),
) -> dict[str, str]:
    """Accepts and processes an FCC JSON dictionary with proper transaction handling."""
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only JSON files are accepted."
        )

    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} uploading FCC dictionary: {file.filename}"
        )
        contents = await file.read()
        await database.import_fcc_dict(contents)
        return {
            "message": f"Successfully processed {file.filename}. All data has been committed to the database."
        }
    except ValueError as e:
        logger.error(f"Validation error processing {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Data validation error: {e}")
    except RuntimeError as e:
        logger.error(f"Import failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {e}")


@app.get("/query/", response_model=PaginatedDatasetSearchResponse)
async def execute_gclql_query(
    q: str,
    limit: int = Query(20, ge=20, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("dataset_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order: 'asc' or 'desc'"),
) -> Any:
    """
    Executes a GCLQL-style query against the database with pagination and sorting.
    Supports sorting by any dataset field or metadata JSON field (e.g., 'metadata.key').
    """
    try:
        # Validate sort_order parameter
        if sort_order.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400, detail="sort_order must be 'asc' or 'desc'"
            )

        logger.debug("QUERY_STRING: %s", q)

        count_query, search_query, search_query_params = query_parser.parse_query(
            q, sort_by=sort_by, sort_order=sort_order.lower()
        )

        logger.debug("COUNT_QUERY: %s", count_query)
        logger.debug("SEARCH_QUERY: %s", search_query)
        logger.debug("SEARCH_QUERY_PARAMS: %s", search_query_params)

        return await database.perform_search(
            count_query, search_query, search_query_params, limit, offset
        )

    except ValueError as e:
        logger.error("Invalid query", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid query: {e}")


@app.get("/stages/", response_model=list[DropdownItem])
async def get_stages(
    accelerator_name: str | None = Query(
        None, description="Filter by accelerator name"
    ),
    campaign_name: str | None = Query(None, description="Filter by campaign name"),
    detector_name: str | None = Query(None, description="Filter by detector name"),
) -> Any:
    """
    Get all available stages for the navigation dropdown.
    Optionally filter by accelerator, campaign, or detector.
    """
    return await database.get_stages(
        accelerator_name=accelerator_name,
        campaign_name=campaign_name,
        detector_name=detector_name,
    )


@app.get("/campaigns/", response_model=list[DropdownItem])
async def get_campaigns(
    accelerator_name: str | None = Query(
        None, description="Filter by accelerator name"
    ),
    stage_name: str | None = Query(None, description="Filter by stage name"),
    detector_name: str | None = Query(None, description="Filter by detector name"),
) -> Any:
    """
    Get all available campaigns for the navigation dropdown.
    Optionally filter by accelerator, stage, or detector.
    """
    return await database.get_campaigns(
        accelerator_name=accelerator_name,
        stage_name=stage_name,
        detector_name=detector_name,
    )


@app.get("/detectors/", response_model=list[DropdownItem])
async def get_detectors(
    accelerator_name: str | None = Query(
        None, description="Filter by accelerator name"
    ),
    stage_name: str | None = Query(None, description="Filter by stage name"),
    campaign_name: str | None = Query(None, description="Filter by campaign name"),
) -> Any:
    """
    Get all available detectors for the navigation dropdown.
    Optionally filter by accelerator, stage, or campaign.
    """
    return await database.get_detectors(
        accelerator_name=accelerator_name,
        stage_name=stage_name,
        campaign_name=campaign_name,
    )


@app.get("/accelerators/", response_model=list[DropdownItem])
async def get_accelerators(
    stage_name: str | None = Query(None, description="Filter by stage name"),
    campaign_name: str | None = Query(None, description="Filter by campaign name"),
    detector_name: str | None = Query(None, description="Filter by detector name"),
) -> Any:
    """
    Get all available accelerators for the navigation dropdown.
    Optionally filter by stage, campaign, or detector.
    """
    return await database.get_accelerators(
        stage_name=stage_name,
        campaign_name=campaign_name,
        detector_name=detector_name,
    )


@app.post("/datasets/", response_model=list[dict[str, Any]])
async def get_datasets_by_ids(request: DatasetIdsRequest) -> Any:
    """
    Get datasets by their IDs with all details and metadata flattened to top-level keys.
    Takes a list of dataset IDs and returns a list of dataset information.
    """
    if not request.dataset_ids:
        return []

    datasets = await database.get_datasets_by_ids(request.dataset_ids)
    return datasets


@app.get("/sorting-fields/", response_model=dict[str, Any])
async def get_sorting_fields() -> dict[str, Any]:
    """
    Get available fields for sorting in the query endpoint.
    Returns a flat list of all sortable fields for easy UI consumption.
    """
    result = await database.get_sorting_fields()
    return result


@app.get("/datasets/{dataset_id}", response_model=dict[str, Any])
async def get_dataset_by_id(dataset_id: int) -> Any:
    """
    Get a single dataset by its ID with all details and metadata flattened to top-level keys.
    """
    try:
        dataset = await database.get_dataset_by_id(dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=404, detail=f"Dataset with ID {dataset_id} not found"
            )
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/datasets/{dataset_id}", response_model=dict[str, Any])
async def update_dataset(
    dataset_id: int,
    update_data: DatasetUpdate,
    user: dict[str, Any] = Depends(get_and_validate_user_from_token),
) -> Any:
    """
    Update a dataset with the provided data.
    Requires authentication via JWT token.
    """
    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} updating dataset {dataset_id}."
        )

        update_dict = update_data.model_dump(exclude_none=True)

        if not update_dict:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update"
            )

        updated_dataset = await database.update_dataset(dataset_id, update_dict)
        return updated_dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
