"""
Editor role management for the Database class.

Admin is never stored here -- it's granted entirely via CERN role/e-group
membership (see app.utils.auth_utils.get_user_role). This module only
manages "editor" grants, assignable by an admin in-app.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.storage.database import Database

from app.utils.logging_utils import get_logger

logger = get_logger()


async def list_editors(database: "Database") -> list[dict[str, Any]]:
    """List all users currently granted the editor role."""
    async with database.session() as conn:
        rows = await conn.fetch(
            "SELECT cern_username, granted_by, granted_at FROM user_roles "
            "WHERE role = 'editor' ORDER BY granted_at DESC"
        )
        return [dict(row) for row in rows]


async def grant_editor_role(
    database: "Database", cern_username: str, granted_by: str
) -> None:
    """Grant a user the editor role, or refresh who granted it if already set."""
    async with database.session() as conn:
        await conn.execute(
            """
            INSERT INTO user_roles (cern_username, role, granted_by)
            VALUES ($1, 'editor', $2)
            ON CONFLICT (cern_username)
            DO UPDATE SET granted_by = EXCLUDED.granted_by, granted_at = NOW()
            """,
            cern_username,
            granted_by,
        )
        logger.info(f"Granted editor role to '{cern_username}' (by '{granted_by}')")


async def revoke_editor_role(database: "Database", cern_username: str) -> bool:
    """Revoke a user's editor role. Returns True if a grant was actually removed."""
    async with database.session() as conn:
        result = await conn.execute(
            "DELETE FROM user_roles WHERE cern_username = $1 AND role = 'editor'",
            cern_username,
        )
        revoked = bool(result == "DELETE 1")
        if revoked:
            logger.info(f"Revoked editor role from '{cern_username}'")
        return revoked
