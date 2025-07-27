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


async def get_and_validate_authorized_user_from_session(
    request: Request,
) -> dict[str, Any]:
    """Get current user from session cookie with CERN validation and check for 'authorized' role."""
    from app.auth import cern_auth

    try:
        # First validate the session like the regular function
        user_data = await get_and_validate_user_from_session(request)

        # Now check if user has the "authorized" role for this specific operation
        if not cern_auth.has_user_access(user_data):
            raise HTTPException(
                status_code=403,
                detail="Access denied. This operation requires 'authorized' role.",
            )

        return user_data
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authorized user validation: {e}")
        raise HTTPException(
            status_code=403,
            detail="Authorization check failed.",
        )


class EntityRequest(BaseModel):
    """Request model for entity search"""

    filters: dict[str, str] = {}
    search: str = ""
    sort: str = "id"
    page: int = 1
    limit: int = 25


class EntityIdsRequest(BaseModel):
    """Request model for getting entities by IDs."""

    entity_ids: list[int]


class DeleteEntitiesRequest(BaseModel):
    """Request model for deleting entities by IDs."""

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
    limit: int = Query(25, ge=20, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("last_edited_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
) -> Any:
    """
    Executes a GCLQL-style query against the database with infinite scroll support and sorting.
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


@router.get("/download-filtered/", response_model=list[dict[str, Any]])
async def download_filtered_entities(
    q: str,
    sort_by: str = Query("last_edited_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: 'asc' or 'desc'"),
) -> Any:
    """
    Download all entities matching the given query filter.
    This endpoint returns all results without pagination for download purposes.
    """
    logger.info(
        f"*** /download-filtered/ endpoint called with q={q}, sort_by={sort_by}, sort_order={sort_order}"
    )
    try:
        # Validate sort_order parameter
        if sort_order.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400, detail="sort_order must be 'asc' or 'desc'"
            )

        logger.debug("DOWNLOAD_QUERY_STRING: %s", q)

        count_query, search_query, search_query_params = query_parser.parse_query(
            q, sort_by=sort_by, sort_order=sort_order.lower()
        )

        logger.debug("DOWNLOAD_COUNT_QUERY: %s", count_query)
        logger.debug("DOWNLOAD_SEARCH_QUERY: %s", search_query)
        logger.debug("DOWNLOAD_SEARCH_QUERY_PARAMS: %s", search_query_params)

        # Get all results by using a very large limit
        result = await database.perform_search(
            count_query, search_query, search_query_params, limit=999999, offset=0
        )

        # Return only the items array for download
        return result.get("items", [])

    except ValueError as e:
        logger.error("Invalid download query", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid query: {e}")


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


class MetadataLockRequest(BaseModel):
    """Request model for locking/unlocking metadata fields."""

    field_name: str
    locked: bool


@router.put("/entities/{entity_id}/metadata/lock", response_model=dict[str, Any])
async def update_metadata_lock(
    entity_id: int,
    lock_request: MetadataLockRequest,
    _request: Request,
    # user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> Any:
    """
    Update the lock state of a metadata field.
    Requires authentication via session cookie.
    """
    try:
        # logger.info(
        #     f"User {user.get('preferred_username', 'unknown')} updating lock state for field '{lock_request.field_name}' "
        #     f"on entity {entity_id} to {'locked' if lock_request.locked else 'unlocked'}."
        # )

        # Get current entity to check if it exists and get current metadata
        current_entity = await database.get_entity_by_id(entity_id)
        if not current_entity:
            raise HTTPException(
                status_code=404, detail=f"Entity with ID {entity_id} not found"
            )

        # Get current metadata or initialize empty dict
        current_metadata = current_entity.get("metadata", {})
        if isinstance(current_metadata, str):
            import json

            current_metadata = json.loads(current_metadata)
        elif current_metadata is None:
            current_metadata = {}

        logger.info(f"Current metadata before lock update: {current_metadata}")
        logger.info(
            f"Current lock fields: {[k for k in current_metadata.keys() if '__lock__' in k]}"
        )

        # Create lock field name using the convention: __{key}__lock__
        lock_field_name = f"__{lock_request.field_name}__lock__"

        # Update lock state
        if lock_request.locked:
            # Set lock to True
            current_metadata[lock_field_name] = True
            logger.info(
                f"Locking field '{lock_request.field_name}' by setting {lock_field_name} = True"
            )
        else:
            # Remove lock field when unlocking (saves storage space)
            if lock_field_name in current_metadata:
                current_metadata.pop(lock_field_name, None)
                logger.info(
                    f"Unlocking field '{lock_request.field_name}' by removing {lock_field_name}"
                )
            else:
                logger.info(f"Field '{lock_request.field_name}' was already unlocked")

        logger.info(f"Updated metadata keys: {list(current_metadata.keys())}")
        logger.info(
            f"Final lock fields: {[k for k in current_metadata.keys() if '__lock__' in k]}"
        )

        # Update the entity with only the lock field that changed
        if lock_request.locked:
            # Only pass the new lock field
            lock_update = {lock_field_name: True}
        else:
            # For unlock, pass a special indicator to remove the field
            lock_update = {lock_field_name: None}  # None will indicate removal

        update_data = {"metadata": lock_update}
        logger.info(f"Sending update_data to database: {update_data}")
        await database.update_entity(entity_id, update_data)

        return {
            "success": True,
            "message": f"Field '{lock_request.field_name}' {'locked' if lock_request.locked else 'unlocked'} successfully",
            "field_name": lock_request.field_name,
            "locked": lock_request.locked,
            "entity_id": entity_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating metadata lock: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/entities/", response_model=dict[str, Any])
async def delete_entities(
    request: DeleteEntitiesRequest,
    # user: dict[str, Any] = Depends(get_and_validate_authorized_user_from_session),
) -> dict[str, Any]:
    """
    Delete entities by their IDs. Only users with 'authorized' role can perform this operation.

    This endpoint:
    - Validates user authentication and authorization (requires 'authorized' role)
    - Accepts a list of entity IDs for bulk deletion
    - Returns detailed results including success/failure counts
    - Handles foreign key constraints gracefully
    - Provides clear error messages for different failure scenarios
    """
    try:
        # logger.info(
        #     f"User {user.get('preferred_username', 'unknown')} requesting deletion of entities: {request.entity_ids}"
        # )

        if not request.entity_ids:
            raise HTTPException(
                status_code=400, detail="No entity IDs provided for deletion"
            )

        # Validate entity IDs are positive integers
        invalid_ids = [entity_id for entity_id in request.entity_ids if entity_id <= 0]
        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity IDs (must be positive integers): {invalid_ids}",
            )

        # Call the database delete method
        result = await database.delete_entities_by_ids(request.entity_ids)

        logger.info(
            # f"Delete operation completed for user {user.get('preferred_username', 'unknown')}: "
            f"{result['deleted_count']} deleted, {result['not_found_count']} not found"
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle business logic errors (like foreign key constraints)
        logger.error(f"Business logic error during entity deletion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during entity deletion: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error occurred during deletion"
        )


@router.get("/session-status")
async def get_session_status(request: Request) -> dict[str, Any]:
    """Get current session authentication status."""
    token = request.session.get("token")
    user = request.session.get("user")

    if token and user:
        return {"authenticated": True, "user": user}
    else:
        return {"authenticated": False, "user": None}
