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
from app.models.process import ProcessWithDetails
from app.storage.database import Database

config = get_config()
database = Database()
query_parser = QueryParser(database=database)


# Pydantic model for the paginated response, ensuring a consistent data contract
class PaginatedResponse(BaseModel):
    total: int
    items: list[ProcessWithDetails]


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    """Handles application startup and shutdown events."""
    await database.setup(config.get("database", {}))
    await query_parser.setup()
    yield
    await database.aclose()


app = FastAPI(
    title="FCC Physics Events API",
    description="An API for querying and managing FCC physics simulation sample data.",
    version="1.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Provides a simple welcome message for the API root."""
    return {"message": "Welcome to the FCC Physics Events API"}


@app.post("/upload-fcc-dict/", status_code=202)
async def upload_fcc_dictionary(file: UploadFile = File(...)) -> dict[str, str]:
    """Accepts and processes an FCC JSON dictionary."""
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        contents = await file.read()
        await database.import_fcc_dict(contents)
        return {"message": f"Successfully queued {file.filename} for processing."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )


@app.get("/query/", response_model=PaginatedResponse)
async def execute_gclql_query(
    q: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)
) -> Any:
    """
    Executes a GCLQL-style query against the database with pagination.
    """
    try:
        base_query, count_query, params = query_parser.parse_query(q)

        async with database.session() as conn:
            # First, get the total count of matching records for pagination controls
            total_records = await conn.fetchval(count_query, *params)
            total = total_records if total_records is not None else 0

            # Then, get the paginated results for the current page
            paginated_query = f"{base_query} ORDER BY p.process_id LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            records = await conn.fetch(paginated_query, *params, limit, offset)

            items = [
                ProcessWithDetails.model_validate(dict(record)) for record in records
            ]

            return PaginatedResponse(total=total, items=items)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid query: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred during query execution: {e}"
        )
