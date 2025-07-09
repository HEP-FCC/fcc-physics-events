"""
This is the main FastAPI application file, which orchestrates the API,
database connections, and data processing modules.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from app.config import get_config
from app.gclql_query_parser import QueryParser
from app.logging import get_logger
from app.models.dataset import DatasetUpdate, PaginatedDatasetSearchResponse
from app.models.dropdown import DropdownItem
from app.storage.database import Database

logger = get_logger()

config = get_config()
database = Database()
query_parser = QueryParser(database=database)


# Pydantic model for the dataset IDs request
class DatasetIdsRequest(BaseModel):
    dataset_ids: list[int]


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Handles application startup and shutdown events."""
    await database.setup(config.get("database", {}))
    await query_parser.setup()
    yield
    await database.aclose()


app = FastAPI(
    title="FCC Physics Datasets API",
    description="An API for querying and managing FCC physics simulation datasets.",
    version="1.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fcc-physics-events-dev.web.cern.ch",
        # "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Provides a simple welcome message for the API root."""
    return {"message": "Welcome to the FCC Physics Datasets API"}


@app.post("/authorized/upload-fcc-dict/", status_code=202)
async def upload_fcc_dictionary(file: UploadFile = File(...)) -> dict[str, str]:
    """Accepts and processes an FCC JSON dictionary with proper transaction handling."""
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only JSON files are accepted."
        )

    try:
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
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during import. No data was committed to the database: {e}",
        )


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

        count_query, search_query, search_query_params = query_parser.parse_query(
            q, sort_by=sort_by, sort_order=sort_order.lower()
        )

        return await database.perform_search(
            count_query, search_query, search_query_params, limit, offset
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid query: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during query execution: {e}"
        )


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
    try:
        return await database.get_stages(
            accelerator_name=accelerator_name,
            campaign_name=campaign_name,
            detector_name=detector_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while fetching stages: {e}"
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
    try:
        return await database.get_campaigns(
            accelerator_name=accelerator_name,
            stage_name=stage_name,
            detector_name=detector_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while fetching campaigns: {e}"
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
    try:
        return await database.get_detectors(
            accelerator_name=accelerator_name,
            stage_name=stage_name,
            campaign_name=campaign_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while fetching detectors: {e}"
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
    try:
        return await database.get_accelerators(
            stage_name=stage_name,
            campaign_name=campaign_name,
            detector_name=detector_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching accelerators: {e}",
        )


@app.post("/datasets/", response_model=list[dict[str, Any]])
async def get_datasets_by_ids(request: DatasetIdsRequest) -> Any:
    """
    Get datasets by their IDs with all details and metadata flattened to top-level keys.
    Takes a list of dataset IDs and returns a list of dataset information.
    """
    try:
        if not request.dataset_ids:
            return []

        datasets = await database.get_datasets_by_ids(request.dataset_ids)
        return datasets
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching datasets: {e}",
        )


@app.get("/sorting-fields/", response_model=dict[str, Any])
async def get_sorting_fields() -> dict[str, Any]:
    """
    Get available fields for sorting in the query endpoint.
    Returns a flat list of all sortable fields for easy UI consumption.
    """
    try:
        return await database.get_sorting_fields()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching sorting fields: {e}",
        )


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
    except Exception as e:
        logger.error(f"Error fetching dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching the dataset: {e}",
        )


@app.put("/authorized/datasets/{dataset_id}", response_model=dict[str, Any])
async def update_dataset(dataset_id: int, update_data: DatasetUpdate) -> Any:
    """
    Update a dataset with the provided data.
    Uses full replacement strategy - provide the complete updated dataset object.
    Only non-null fields in the update_data will be updated.
    """
    try:
        # Convert pydantic model to dict, excluding None values
        update_dict = update_data.model_dump(exclude_none=True)

        if not update_dict:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update"
            )

        updated_dataset = await database.update_dataset(dataset_id, update_dict)
        return updated_dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating the dataset: {e}",
        )


@app.get("/authorized/test")
async def test() -> Any:
    return "Test authorized API response."
