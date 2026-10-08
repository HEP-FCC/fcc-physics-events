"""
Health check routes for the Universal Metadata Browser API.
/healthz is used by the Kubernetes probes, /readyz by external monitoring.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, status
from starlette.responses import JSONResponse

from app.storage.database import Database
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="", tags=["health"])

# This will be injected from main.py
database: Database

# Maximum time the readiness check waits for the database
READINESS_DB_TIMEOUT_SECONDS = 2

# Paths of the health check endpoints, excluded from the request logging
HEALTH_PATHS = ("/healthz", "/readyz")


def init_dependencies(db: Database) -> None:
    """Initialize dependencies for this router."""
    global database
    database = db


@router.api_route("/healthz", methods=["GET", "HEAD"])
async def healthz() -> Any:
    """
    Liveness check, reports whether the application process is running.
    Intentionally does not check the database, to avoid restarting the pod
    during database outages.
    """
    return {"status": "ok"}


@router.api_route("/readyz", methods=["GET", "HEAD"])
async def readyz() -> Any:
    """
    Readiness check, reports whether the application can serve requests,
    which requires a working database connection. Not used as a Kubernetes
    readiness probe, so that the single pod keeps serving errors during
    database outages instead of being removed from the service.
    """
    try:
        async with asyncio.timeout(READINESS_DB_TIMEOUT_SECONDS):
            async with database.session() as conn:
                await conn.fetchval("SELECT 1")
    except Exception as e:
        logger.warning(f"Readiness check failed: {type(e).__name__}: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable"},
        )

    return {"status": "ok"}
