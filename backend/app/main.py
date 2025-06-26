import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from starlette.middleware.cors import CORSMiddleware

from app.gclql_query_parser import QueryParser

from .db.database import Database
from .db.schemas import (
    AcceleratorTypeInDB,
    CampaignInDB,
    DetectorInDB,
    FrameworkInDB,
    ProcessInDB,
    SearchQuery,
)
from .fcc_dict_parser import FccDictParser


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # noqa: ARG001
    await database.setup()
    await query_parser.setup(database)

    yield

    await database.aclose()


DB_DSN = os.environ.get(
    "DATABASE_URL",
    "postgres://fcc_user:fcc_password@localhost:5432/fcc_physics_samples",
)
database = Database(dsn=DB_DSN)
query_parser = QueryParser(database=database)
fcc_parser = FccDictParser(db=database)

app = FastAPI(
    title="FCC Physics Events",
    description="An API for querying FCC physics simulation sample data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the FCC Physics Events API"}


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), accelerator_type: str = "fcc-ee"):
    """
    Upload a JSON file with physics processes to be parsed and added to the database.

    Args:
        file: The JSON file to upload
        accelerator_type: The accelerator type name (default: fcc-ee)
    """
    if file.content_type != "application/json":
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a JSON file."
        )
    try:
        contents = await file.read()
        await fcc_parser.parse_and_insert(contents, accelerator_type)
        return {
            "message": f"Successfully uploaded and processed {file.filename} for {accelerator_type}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.get("/search/", response_model=list[ProcessInDB])
async def search_processes(
    query: SearchQuery = Depends(),
) -> list[ProcessInDB]:
    """
    Search for physics processes with optional filtering on various fields.

    This endpoint allows you to combine multiple search criteria. By default,
    it uses case-insensitive regular expressions for matching.

    - **To use fuzzy search:** set `use_fuzzy_search=true`.
    - **To use exact match:** set `exact_match=true`.

    Example a `curl` command for this endpoint:
    `curl -X 'GET' 'http://localhost:8000/search/?detector_name=IDEA.*' -H 'accept: application/json'`
    """
    return await database.search_processes(query)


@app.get("/accelerator-types/")
async def get_accelerator_types() -> list[AcceleratorTypeInDB]:
    """Fetch all accelerator types from the database."""
    return await database.get_all_accelerator_types()


@app.get("/frameworks/")
async def get_frameworks() -> list[FrameworkInDB]:
    """Fetch all simulation frameworks from the database."""
    return await database.get_all_frameworks()


@app.get("/campaigns/")
async def get_campaigns() -> list[CampaignInDB]:
    """Fetch all campaigns from the database."""
    return await database.get_all_campaigns()


@app.get("/detectors/")
async def get_detectors() -> list[DetectorInDB]:
    """Fetch all detectors from the database."""
    return await database.get_all_detectors()


@app.get("/gclql-query/")
async def gql_query(query: str) -> list[ProcessInDB]:
    """
    Execute a GCLQL query against the database.

    Args:
        query: A string containing the GCLQL query to execute

    Returns:
        A list of sample records matching the query

    Example:
        /gclql-query/?query=detector~"IDEA" AND campaign="Winter2023"
    """
    try:
        sql_query, params = query_parser.parse_query(query)
        print("QUERY:", sql_query)
        print("PARAMS:", params)
        async with database.session() as conn:
            records = await conn.fetch(sql_query, *params)
            return [ProcessInDB.model_validate(dict(record)) for record in records]
    except ValueError as e:
        print(e.with_traceback(e.__traceback__))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/processes/{process_id}/files")
async def get_process_files(process_id: int) -> dict[str, Any]:
    """
    Fetch just the files metadata for a specific process.

    This endpoint is optimized for retrieving the potentially large 'files' field
    from the process metadata separately from the main process data.
    """
    async with database.session() as conn:
        record = await conn.fetchrow(
            """
            SELECT
                p.process_id,
                p.name,
                p.metadata->'files' as files
            FROM processes p
            WHERE p.process_id = $1
            """,
            process_id
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Process with ID {process_id} not found"
            )

        return {
            "process_id": record["process_id"],
            "name": record["name"],
            "files": record["files"]
        }