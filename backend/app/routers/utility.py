"""
Utility routes for the FCC Physics Events API.
Handles application status, testing, and root-level endpoints.
"""

from typing import Any

from fastapi import APIRouter

from app.utils import get_config, get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["utility"])

# Global reference to file watcher service (will be set by main.py)
file_watcher_service = None


def init_dependencies(file_watcher) -> None:
    """Initialize router dependencies."""
    global file_watcher_service
    file_watcher_service = file_watcher


@router.get("/")
async def read_root() -> dict[str, str]:
    """Root endpoint that returns basic application information."""
    logger.info("*** ROOT ENDPOINT CALLED ***")
    config = get_config()
    return {
        "message": "FCC Physics Events API",
        "version": "1.0.0",
        "app_title": config.get("app.title", "Data Explorer"),
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "fcc-physics-events-api"}


@router.get("/file-watcher/status")
async def file_watcher_status() -> dict[str, Any]:
    """Get the current status of the file watcher service."""
    if file_watcher_service is None:
        return {
            "status": "not_initialized",
            "message": "File watcher service not initialized",
        }

    return file_watcher_service.get_status()
