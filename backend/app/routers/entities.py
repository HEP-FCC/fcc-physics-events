"""
Entity and dataset routes for the FCC Physics Events API.
Handles CRUD operations for datasets and related entities.
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from app.gclql_query_parser import QueryParser
from app.models.generic import GenericEntityUpdate
from app.storage.database import Database
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["entities"])

# This will be injected from main.py
database: Database
query_parser: QueryParser


def init_dependencies(db: Database, qp: QueryParser) -> None:
    """Initialize dependencies for this router."""
    global database, query_parser
    database = db
    query_parser = qp


async def get_and_validate_user_from_session(request: Request) -> dict[str, Any]:
    """Get current user from session cookie with CERN validation."""
    from app.auth import cern_auth

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


class EntityRequest(BaseModel):
    """Request model for entity search"""

    filters: dict[str, str] = {}
    search: str = ""
    sort: str = "id"
    page: int = 1
    limit: int = 20


class EntityIdsRequest(BaseModel):
    """Request model for getting entities by IDs."""

    entity_ids: list[int]


@router.post("/upload-fcc-dict/", status_code=202)
async def upload_fcc_dict(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> dict[str, str]:
    """
    Upload and import FCC dictionary data.
    This endpoint handles file uploads for FCC dictionary imports.
    """
    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} uploading FCC dictionary file"
        )

        # Read file content
        content = await file.read()

        # Import the data
        async with database.session() as conn:
            await database.import_fcc_dict(conn, content)

        return {"message": "FCC dictionary imported successfully"}

    except Exception as e:
        logger.error(f"Failed to upload FCC dictionary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to import FCC dictionary: {str(e)}"
        )


@router.get("/query/", response_model=dict[str, Any])
async def execute_gclql_query(
    q: str,
    limit: int = Query(20, ge=20, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("last_edited_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
) -> Any:
    """
    Executes a GCLQL-style query against the database with pagination and sorting.
    Supports sorting by any entity field or metadata JSON field (e.g., 'metadata.key').
    """
    logger.info(
        f"*** /query/ endpoint called with q={q}, limit={limit}, offset={offset}"
    )
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


@router.post("/entities/", response_model=list[dict[str, Any]])
async def get_entities_by_ids(request: EntityIdsRequest) -> Any:
    """
    Get entities by their IDs with all details and metadata flattened to top-level keys.
    Takes a list of entity IDs and returns a list of entity information.
    """
    if not request.entity_ids:
        return []

    entities = await database.get_entities_by_ids(request.entity_ids)
    return entities


@router.get("/sorting-fields/", response_model=dict[str, Any])
async def get_sorting_fields() -> dict[str, Any]:
    """
    Get available fields for sorting in the query endpoint.
    Returns a flat list of all sortable fields for easy UI consumption.
    """
    result = await database.get_sorting_fields()
    return result


@router.get("/entities/{entity_id}", response_model=dict[str, Any])
async def get_entity_by_id(entity_id: int) -> Any:
    """
    Get a single entity by its ID with all details and metadata flattened to top-level keys.
    """
    try:
        entity = await database.get_entity_by_id(entity_id)
        if not entity:
            raise HTTPException(
                status_code=404, detail=f"Entity with ID {entity_id} not found"
            )
        return entity
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/entities/{entity_id}", response_model=dict[str, Any])
async def update_entity(
    entity_id: int,
    update_data: GenericEntityUpdate,
    _request: Request,
    user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> Any:
    """
    Update an entity with the provided data.
    Requires authentication via session cookie.
    """
    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} updating entity {entity_id}."
        )

        update_dict = update_data.model_dump(exclude_none=True)

        if not update_dict:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update"
            )

        updated_entity = await database.update_entity(entity_id, update_dict)
        return updated_entity
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session-status")
async def get_session_status(request: Request) -> dict[str, Any]:
    """Get current session authentication status."""
    token = request.session.get("token")
    user = request.session.get("user")

    if token and user:
        return {"authenticated": True, "user": user}
    else:
        return {"authenticated": False, "user": None}
