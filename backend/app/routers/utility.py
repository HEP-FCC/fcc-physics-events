"""
Utility routes for the FCC Physics Events API.
Handles application status, testing, and root-level endpoints.
"""

from fastapi import APIRouter

from app.utils import get_config, get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["utility"])


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

