import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.gclql_query_parser import QueryParser

from .db.database import Database
from .db.schemas import (
    AcceleratorTypeInDB,
    CampaignInDB,
    DetectorInDB,
    FrameworkInDB,
    SampleInDB,
    SearchQuery,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # noqa: ARG001
    await database.setup()
    await query_parser.setup(database)

    yield

    await database.aclose()


# Initialize database connection
DB_DSN = os.environ.get(
    "DATABASE_URL",
    "postgres://fcc_user:fcc_password@localhost:5432/fcc_physics_samples",
)
database = Database(dsn=DB_DSN)
query_parser = QueryParser(database=database)

# Initialize FastAPI app
app = FastAPI(
    title="FCC Physics Events",
    description="An API for querying FCC physics simulation sample data.",
    version="1.0.0",
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Endpoints
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the FCC Physics Events API"}


@app.get("/search/", response_model=list[SampleInDB])
async def search_samples(
    query: SearchQuery = Depends(),
) -> list[SampleInDB]:
    """
    Search for physics samples with optional filtering on various fields.

    This endpoint allows you to combine multiple search criteria. By default,
    it uses case-insensitive regular expressions for matching.

    - **To use fuzzy search:** set `use_fuzzy_search=true`.
    - **To use exact match:** set `exact_match=true`.

    Example a `curl` command for this endpoint:
    `curl -X 'GET' 'http://localhost:8000/search/?detector_name=IDEA.*' -H 'accept: application/json'`
    """
    return await database.search_samples(query)


# Endpoints for populating UI elements (e.g., dropdowns)
@app.get("/accelerator-types/", response_model=list[AcceleratorTypeInDB])
async def get_accelerator_types() -> list[AcceleratorTypeInDB]:
    """Fetch all accelerator types from the database."""
    return await database.get_all_accelerator_types()


@app.get("/frameworks/", response_model=list[FrameworkInDB])
async def get_frameworks() -> list[FrameworkInDB]:
    """Fetch all simulation frameworks from the database."""
    return await database.get_all_frameworks()


@app.get("/campaigns/", response_model=list[CampaignInDB])
async def get_campaigns() -> list[CampaignInDB]:
    """Fetch all campaigns from the database."""
    return await database.get_all_campaigns()


@app.get("/detectors/", response_model=list[DetectorInDB])
async def get_detectors() -> list[DetectorInDB]:
    """Fetch all detectors from the database."""
    return await database.get_all_detectors()


@app.get("/gql-query/", response_model=list[SampleInDB])
async def gql_query() -> list[SampleInDB]:
    # Hardcoded query example
    query = 'detector~"IDEA" AND campaign="Winter2023"'

    try:
        sql, params = query_parser.parse_query(query)

        async with database.session() as conn:
            records = await conn.fetch(sql, *params)
            return [SampleInDB.model_validate(dict(record)) for record in records]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
