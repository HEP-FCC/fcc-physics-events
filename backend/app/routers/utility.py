"""
Utility routes for the FCC Physics Events API.
Handles application status, testing, and root-level endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile

from app.utils import get_config, get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["utility"])

# Global references (will be set by main.py)
file_watcher_service: Any = None
database: Any = None


def init_dependencies(file_watcher, db=None) -> None:
    """Initialize router dependencies."""
    global file_watcher_service, database
    file_watcher_service = file_watcher
    database = db


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


@router.post("/upload-fcc-dict/")
async def upload_fcc_dict(file: UploadFile) -> dict[str, Any]:
    """Upload and import an FCC dictionary JSON file."""

    # Type check for the uploaded file
    if not isinstance(file, UploadFile):
        raise HTTPException(status_code=400, detail="Invalid file upload")

    if database is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    # Validate file type
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    try:
        # Read file content
        content = await file.read()

        if not content.strip():
            raise HTTPException(status_code=400, detail="File is empty")

        # Import using the database import function
        await database.import_fcc_dict(content)

        return {
            "status": "success",
            "message": f"Successfully imported FCC dictionary from {file.filename}",
            "filename": file.filename,
        }

    except ValueError as e:
        logger.error(f"Import validation error for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Import error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Import failed due to server error")
