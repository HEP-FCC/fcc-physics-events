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
from app.config import get_config
from app.gclql_query_parser import QueryParser
from app.logging import get_logger, setup_logging
from app.models.dataset import DatasetUpdate, PaginatedDatasetSearchResponse
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
    return await oauth.cern.authorize_redirect(request, redirect_uri)


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

    # Store auth info in session for cookie-based authentication
    request.session["token"] = jwt_encoded_token
    request.session["user"] = {
        "given_name": userinfo["given_name"],
        "family_name": userinfo["family_name"],
        "preferred_username": userinfo.get("preferred_username"),
    }

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


@app.get("/logout")
async def logout(request: Request) -> JSONResponse:
    """Get CERN SSO logout URL and clear session."""
    # Clear the session
    request.session.clear()

    # Return CERN SSO logout URL
    cern_logout_url = (
        "https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/logout"
    )
    post_logout_redirect_uri = config.get(
        "general.FRONTEND_URL", "http://localhost:3000"
    )

    logout_url = (
        f"{cern_logout_url}?post_logout_redirect_uri={post_logout_redirect_uri}"
    )

    return JSONResponse(content={"logout_url": logout_url})


@app.get("/test")
async def test(creds: HTTPAuthorizationCredentials | None = Depends(security)) -> None:
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
    # user: dict[str, Any] = Depends(get_and_validate_user_from_token),
) -> dict[str, str]:
    """Accepts and processes an FCC JSON dictionary with proper transaction handling."""
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only JSON files are accepted."
        )

    try:
        # logger.info(
        #     f"User {user.get('preferred_username', 'unknown')} uploading FCC dictionary: {file.filename}"
        # )
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
    _request: Request,
    user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> Any:
    """
    Update a dataset with the provided data.
    Requires authentication via session cookie.
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


@app.get("/session-status")
async def get_session_status(request: Request) -> JSONResponse:
    """Get current session authentication status."""
    token = request.session.get("token")
    user = request.session.get("user")

    if token and user:
        return JSONResponse(content={"authenticated": True, "user": user})
    else:
        return JSONResponse(content={"authenticated": False, "user": None})


# TODO: logout button/api method


# =============================================================================
# SCHEMA-DRIVEN GENERIC API ENDPOINTS
# =============================================================================


class SearchRequest(BaseModel):
    """Request model for generic search"""

    filters: dict[str, str] = {}
    search: str = ""
    page: int = 1
    limit: int = 20


@app.get("/api/schema")
async def get_database_schema() -> Any:
    """
    Get the complete database schema configuration for frontend.
    This endpoint analyzes the database structure and returns configuration
    that allows the frontend to work with any database schema.
    """
    try:
        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            # Analyze the navigation structure based on the main table (datasets)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                "datasets"
            )

            # Fetch navigation configuration from database tables
            navigation_config = await _get_navigation_config_from_db(
                conn, navigation_analysis
            )

            # Build the response
            schema_config = {
                "tables": [navigation_analysis["main_table"]]
                + list(navigation_analysis["navigation_tables"].keys()),
                "main_table": navigation_analysis["main_table"],
                "foreign_keys": [
                    f"{key}_id"
                    for key in navigation_analysis["navigation_tables"].keys()
                ],
                "navigation_config": {
                    "order": navigation_config["order"],
                    "menu": navigation_config[
                        "config"
                    ],  # Only return what exists in DB
                },
                "mainTableSchema": {
                    "tableName": navigation_analysis["main_table"],
                    "primaryKey": navigation_analysis["main_table_schema"][
                        "primary_key"
                    ],
                    "nameColumn": "name",  # Datasets typically use 'name'
                    "columns": [
                        col["column_name"]
                        for col in navigation_analysis["main_table_schema"]["columns"]
                    ],
                },
                "navigationTables": navigation_analysis["navigation_tables"],
                "navigationOrder": navigation_config["order"],
                "navigation": navigation_config["config"],
                "appTitle": config.get("app.title", "Data Explorer"),
                "searchPlaceholder": config.get(
                    "app.search_placeholder", "Search datasets..."
                ),
            }

            return schema_config

    except Exception as e:
        logger.error(f"Failed to get database schema: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve database schema"
        )


async def _get_navigation_config_from_db(
    conn: Any, navigation_analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Fetch navigation configuration from database tables.
    Only retrieves display_order and derives everything else dynamically.
    """
    navigation_tables = {
        entity["key"]: entity["table_name"]
        for entity in navigation_analysis["navigation_entities"]
    }

    table_orders = []

    for key, table_name in navigation_tables.items():
        try:
            # Get the first record's display_order (assuming all records in a table have the same order)
            order_query = f"""
                SELECT display_order
                FROM {table_name}
                LIMIT 1
            """  # Safe because table_name comes from schema discovery

            order_result = await conn.fetchval(order_query)
            display_order = order_result if order_result is not None else 0

            table_orders.append((display_order, key))

        except Exception as e:
            logger.warning(f"Could not fetch display_order for table {table_name}: {e}")
            # Use index as fallback for ordering
            table_orders.append((len(table_orders) * 10, key))

    # Sort by display_order and return
    table_orders.sort(key=lambda x: x[0])
    ordered_keys = [key for _, key in table_orders]

    # Build minimal navigation config - frontend will derive colors, icons, labels
    navigation_configs = {}
    for i, key in enumerate(ordered_keys):
        entity_info = next(
            e for e in navigation_analysis["navigation_entities"] if e["key"] == key
        )
        navigation_configs[key] = {
            "columnName": entity_info["column_name"],
            "orderIndex": i,  # Frontend will use this to derive color from app config
        }

    return {"order": ordered_keys, "config": navigation_configs}


@app.get("/api/dropdown/{table_key}")
async def get_dropdown_items(
    table_key: str,
    filters: str = Query("", description="JSON string of filters to apply"),
) -> Any:
    """
    Get dropdown items for any navigation table based on schema discovery.
    This replaces table-specific endpoints like /stages/, /detectors/, etc.
    Returns only items that have related datasets.
    """
    import json

    try:
        # Parse filters
        filter_dict = {}
        if filters:
            filter_dict = json.loads(filters)

        # Get schema information to find the appropriate table
        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                "datasets"
            )

            if table_key not in navigation_analysis["navigation_tables"]:
                raise HTTPException(
                    status_code=404, detail=f"Navigation table '{table_key}' not found"
                )

            table_info = navigation_analysis["navigation_tables"][table_key]
            table_name = table_info["table_name"]
            primary_key = table_info["primary_key"]
            name_column = table_info["name_column"]

            # Build query that only returns items that have datasets
            # This ensures dropdowns only show relevant options
            query = f"""
                SELECT DISTINCT t.{primary_key} as id, t.{name_column} as name
                FROM {table_name} t
                INNER JOIN datasets d ON d.{table_key}_id = t.{primary_key}
            """

            params: list[Any] = []
            conditions: list[str] = []

            # Apply filters if provided
            if filter_dict:
                for filter_key, filter_value in filter_dict.items():
                    if filter_key.endswith("_name"):
                        # This is a filter by name, convert to ID
                        entity_key = filter_key.replace("_name", "")
                        if entity_key in navigation_analysis["navigation_tables"]:
                            filter_table_info = navigation_analysis[
                                "navigation_tables"
                            ][entity_key]
                            filter_table_name = filter_table_info["table_name"]
                            filter_name_column = filter_table_info["name_column"]
                            filter_pk = filter_table_info["primary_key"]

                            # Get the ID for this filter value
                            id_result = await conn.fetchval(
                                f"SELECT {filter_pk} FROM {filter_table_name} WHERE {filter_name_column} = $1",
                                filter_value,
                            )

                            if id_result:
                                # Add filter condition to the query
                                conditions.append(
                                    f"d.{entity_key}_id = ${len(params) + 1}"
                                )
                                params.append(id_result)
                    else:
                        # Direct filter by ID
                        if filter_key.endswith("_id"):
                            conditions.append(f"d.{filter_key} = ${len(params) + 1}")
                            params.append(filter_value)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY t.{name_column}"

            # Execute the query
            rows = await conn.fetch(query, *params)

            # Convert to the expected format
            items = [{"id": row["id"], "name": row["name"]} for row in rows]

            return {"data": items}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in filters parameter")
    except Exception as e:
        logger.error(f"Failed to get dropdown items for {table_key}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load {table_key} options"
        )


@app.post("/api/search")
async def search_datasets_generic(request: SearchRequest) -> Any:
    """
    Generic search endpoint that works with any database schema.
    Automatically handles joins based on schema discovery.
    """
    try:
        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                "datasets"
            )

            # Build the base query
            main_table = navigation_analysis["main_table"]
            query_parts = ["SELECT d.*"]

            # Add joins for navigation tables to get names
            join_parts = []
            for entity in navigation_analysis["navigation_entities"]:
                table_alias = entity["key"][0]  # Use first letter as alias
                referenced_table = entity["referenced_table"]
                column_name = entity["column_name"]
                name_column = navigation_analysis["navigation_tables"][entity["key"]][
                    "name_column"
                ]

                query_parts.append(
                    f", {table_alias}.{name_column} as {entity['key']}_name"
                )
                join_parts.append(
                    f"LEFT JOIN {referenced_table} {table_alias} ON d.{column_name} = {table_alias}.{navigation_analysis['navigation_tables'][entity['key']]['primary_key']}"
                )

            query_parts.append(f" FROM {main_table} d")
            query_parts.extend(join_parts)

            # Build WHERE conditions
            conditions: list[str] = []
            params: list[Any] = []

            # Add filter conditions
            for filter_key, filter_value in request.filters.items():
                if filter_key.endswith("_name"):
                    # Filter by navigation entity name
                    entity_key = filter_key.replace("_name", "")
                    if entity_key in navigation_analysis["navigation_tables"]:
                        table_alias = entity_key[0]
                        name_column = navigation_analysis["navigation_tables"][
                            entity_key
                        ]["name_column"]
                        conditions.append(
                            f"{table_alias}.{name_column} = ${len(params) + 1}"
                        )
                        params.append(filter_value)

            # Add search condition if provided
            if request.search:
                # Search in dataset name and description
                search_condition = "("
                search_conditions = []

                # Search in main table text fields
                for col in navigation_analysis["main_table_schema"]["columns"]:
                    if any(
                        text_type in col["data_type"].lower()
                        for text_type in ["text", "varchar", "character"]
                    ):
                        search_conditions.append(
                            f"d.{col['column_name']} ILIKE ${len(params) + 1}"
                        )

                if search_conditions:
                    search_condition += " OR ".join(search_conditions) + ")"
                    conditions.append(search_condition)
                    params.append(f"%{request.search}%")

            # Combine query parts
            query = "".join(query_parts)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Add ordering
            query += f" ORDER BY d.{navigation_analysis['main_table_schema']['primary_key']} DESC"

            # Count query for pagination
            count_query = query.replace(
                "SELECT d.*"
                + "".join(query_parts[1 : query_parts.index(f" FROM {main_table} d")]),
                "SELECT COUNT(*)",
            )

            # Execute count query
            total = await conn.fetchval(count_query, *params) or 0

            # Add pagination
            offset = (request.page - 1) * request.limit
            paginated_query = (
                f"{query} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            )

            # Execute main query
            rows = await conn.fetch(paginated_query, *params, request.limit, offset)

            # Convert to dictionaries
            items = [dict(row) for row in rows]

            return {"total": total, "items": items}

    except Exception as e:
        logger.error(f"Failed to perform generic search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.post("/api/import/{table_key}")
async def import_data_generic(
    table_key: str,
    _data: dict[str, Any],
    user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> Any:
    """
    Generic data import endpoint that works with any table based on schema discovery.
    """
    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} importing data to {table_key}"
        )

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            if table_key == "main":
                # Handle main table import (datasets)
                # For now, delegate to existing import logic
                raise HTTPException(
                    status_code=501,
                    detail="Main table import not yet implemented via generic endpoint",
                )
            else:
                # Handle navigation table import
                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure("datasets")
                )

                if table_key not in navigation_analysis["navigation_tables"]:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_key}' not found"
                    )

                table_info = navigation_analysis["navigation_tables"][table_key]
                table_name = table_info["table_name"]

                # Basic validation and insertion logic would go here
                # For now, return a placeholder response
                return {
                    "status": "success",
                    "message": f"Import to {table_name} would be processed here",
                }

    except Exception as e:
        logger.error(f"Failed to import data to {table_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed for {table_key}")


@app.post("/api/validate/{table_key}")
async def validate_data_generic(table_key: str, data: dict[str, Any]) -> Any:
    """
    Generic data validation endpoint that works with any table based on schema discovery.
    """
    try:
        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            if table_key == "main":
                table_metadata = await schema_discovery.get_table_metadata("datasets")
            else:
                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure("datasets")
                )
                if table_key not in navigation_analysis["navigation_tables"]:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_key}' not found"
                    )

                table_info = navigation_analysis["navigation_tables"][table_key]
                table_metadata = await schema_discovery.get_table_metadata(
                    table_info["table_name"]
                )

            if not table_metadata:
                raise HTTPException(
                    status_code=404, detail=f"Table metadata not found for {table_key}"
                )

            # Perform basic validation
            validation_errors = []

            # Check required fields
            for column in table_metadata["columns"]:
                if not column["is_nullable"] and column["column_name"] not in data.get(
                    "data", {}
                ):
                    validation_errors.append(
                        f"Required field '{column['column_name']}' is missing"
                    )

            # Check data types (basic validation)
            for field, _value in data.get("data", {}).items():
                column_info = next(
                    (
                        col
                        for col in table_metadata["columns"]
                        if col["column_name"] == field
                    ),
                    None,
                )
                if column_info:
                    # Add basic type validation here
                    pass

            return {"valid": len(validation_errors) == 0, "errors": validation_errors}

    except Exception as e:
        logger.error(f"Failed to validate data for {table_key}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Validation failed for {table_key}"
        )
