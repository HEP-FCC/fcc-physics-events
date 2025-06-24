from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .database.connection import db
from .database.schemas import DetectorInDB

# from fastapi.routing import APIRoute
# def custom_generate_unique_id(route: APIRoute) -> str:
#     return f"{route.tags[0]}-{route.name}"


app = FastAPI(
    title="FCC Physics Events",
    # openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World!"}


@app.on_event("startup")
async def startup_db_client():
    await db.setup()


@app.on_event("shutdown")
async def shutdown_db_client():
    await db.aclose()


@app.get("/detectors/", response_model=list[DetectorInDB])
async def get_detectors() -> list[DetectorInDB]:
    """
    Fetch all detectors from the database.
    """
    async with db.session() as session:
        detectors = await session.fetch(
            "SELECT * FROM detectors ORDER BY detector_id", model=DetectorInDB
        )
        return detectors


@app.get("/detectors/fuzzy/", response_model=list[DetectorInDB])
async def get_detectors_by_fuzzy_name() -> list[DetectorInDB]:
    """
    Fetch detectors using fuzzy name matching.

    This endpoint demonstrates fuzzy searching with three examples:
    1. "Alpha" with similarity threshold 0.3
    2. "Beta Imagr" with similarity threshold 0.5 (misspelled deliberately)
    3. "Gamma" with similarity threshold 0.4
    """
    # Hardcoded examples
    examples: list[dict[str, float | str]] = [
        {"name": "Alpha_spectroscope", "similarity": 0.3},
        # {"name": "Beta Imagr", "similarity": 0.5},  # Misspelled deliberately
        {"name": "Gamma", "similarity": 0.4},
    ]

    results: list[DetectorInDB] = []

    async with db.session() as session:
        for example in examples:
            name = example["name"]
            similarity_threshold = example["similarity"]

            detectors = await session.fetch(
                """
                SELECT * FROM detectors
                WHERE similarity(name, $1) > $2
                ORDER BY similarity(name, $1) DESC
                """,
                name,
                similarity_threshold,
                model=DetectorInDB,
            )

            results.extend(detectors)

    return results
