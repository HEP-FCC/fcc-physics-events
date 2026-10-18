"""
Admin-only user role management routes for the Dataset Metadata Interface (DaMI) API.

Admin itself is never managed here -- it's granted entirely via CERN
role/e-group membership. These endpoints only manage "editor" grants.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.storage.database import Database
from app.utils.auth_utils import AuthDependency
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# This will be injected from main.py
database: Database


def init_dependencies(db: Database) -> None:
    """Initialize dependencies for this router."""
    global database
    database = db


class EditorGrantRequest(BaseModel):
    """Request model for granting/revoking the editor role."""

    cern_username: str


@router.get("/editors", response_model=list[dict[str, Any]])
async def list_editors(
    _user: dict[str, Any] = Depends(AuthDependency("admin")),
) -> list[dict[str, Any]]:
    """List all users currently granted the editor role."""
    return await database.list_editors()


@router.post("/editors", status_code=status.HTTP_204_NO_CONTENT)
async def grant_editor(
    grant_request: EditorGrantRequest,
    user: dict[str, Any] = Depends(AuthDependency("admin")),
) -> None:
    """Grant a user the editor role."""
    granted_by = user.get("preferred_username", "unknown")
    await database.grant_editor_role(grant_request.cern_username, granted_by)


@router.delete("/editors/{cern_username}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_editor(
    cern_username: str,
    _user: dict[str, Any] = Depends(AuthDependency("admin")),
) -> None:
    """Revoke a user's editor role."""
    revoked = await database.revoke_editor_role(cern_username)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{cern_username}' does not currently have the editor role.",
        )
