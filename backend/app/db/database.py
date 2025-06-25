"""
This file contains the Database class, which manages an asyncpg connection
pool and provides higher-level database operations with session management.
"""

from pathlib import Path
from typing import Any, TypeVar

import asyncpg
from asyncpg.pool import Pool
from pydantic import BaseModel

from .schemas import (
    AcceleratorTypeInDB,
    CampaignInDB,
    DetectorInDB,
    FrameworkInDB,
    SampleInDB,
    SearchQuery,
)

T = TypeVar("T", bound=BaseModel)


class AsyncSessionContextManager:
    """
    Async context manager for acquiring and releasing a connection from the pool.
    """

    def __init__(self, pool: Pool):
        self._pool = pool
        self._connection: asyncpg.Connection | None = None

    async def __aenter__(self) -> asyncpg.Connection:
        """Acquires a connection from the pool and returns it."""
        self._connection = await self._pool.acquire()
        return self._connection

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Releases the connection back to the pool."""
        if self._connection:
            await self._pool.release(self._connection)


class Database:
    """
    Manages the connection pool and provides higher-level database operations.
    """

    _pool: Pool | None = None

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def setup(self) -> None:
        """
        Creates the connection pool. This should be called on application startup.
        """
        if self._pool:
            return
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.dsn, min_size=5, max_size=20
            )
            print("Database connection pool created successfully.")

            print("Creating schema..")
            schema_file = Path(__file__).parent / "fcc-physics-samples.sql"
            with open(schema_file, encoding="utf-8") as f:
                schema_sql = f.read()

            async with self.session() as conn:
                await conn.execute(schema_sql)

        except Exception as e:
            print(f"Error creating database connection pool: {e}")
            raise

    def session(self) -> AsyncSessionContextManager:
        """
        Provides a session context manager for raw database interactions.

        Usage:
            async with db.session() as conn:
                await conn.fetch(...)
        """
        if self._pool is None:
            raise RuntimeError(
                "Connection pool is not initialized. Call setup() first."
            )
        return AsyncSessionContextManager(self._pool)

    async def aclose(self) -> None:
        """
        Closes the connection pool. This should be called on application shutdown.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            print("Database connection pool closed.")

    async def search_samples(self, search_params: SearchQuery) -> list[SampleInDB]:
        """
        Dynamically search for samples based on multiple optional criteria.

        Args:
            search_params: A Pydantic model containing all possible search fields
                           and matching options (exact, fuzzy, regex).

        Returns:
            A list of matching samples.
        """
        # The base query joins all necessary tables for filtering
        base_query = """
            SELECT s.* FROM samples s
            LEFT JOIN detectors d ON s.detector_id = d.detector_id
            LEFT JOIN campaigns c ON s.campaign_id = c.campaign_id
            LEFT JOIN frameworks f ON s.framework_id = f.framework_id
            LEFT JOIN accelerator_types at ON s.accelerator_type_id = at.accelerator_type_id
        """
        conditions = []
        params: list[Any] = []

        # Map API-level field names to database columns
        search_fields = {
            "s.name": search_params.sample_name,
            "d.name": search_params.detector_name,
            "c.name": search_params.campaign_name,
            "f.name": search_params.framework_name,
            "at.name": search_params.accelerator_type_name,
            "s.metadata_search_text": search_params.metadata_contains,
        }

        # Helper to dynamically and safely add a condition and its parameters
        def add_condition(clause: str, *values: Any) -> None:
            """Formats a SQL clause with parameter placeholders and adds to lists."""
            # Substitute placeholders with actual PostgreSQL parameter indices ($1, $2, etc.)
            param_indices = [
                f"${i+1}" for i in range(len(params), len(params) + len(values))
            ]
            conditions.append(clause.format(*param_indices))
            params.extend(values)

        # Build conditions based on provided search parameters
        for column, value in search_fields.items():
            if value is not None:
                if search_params.exact_match:
                    # Case-insensitive exact match
                    add_condition(f"{column} ILIKE {{}}", value)
                elif search_params.use_fuzzy_search:
                    # Fuzzy match using trigram word similarity
                    add_condition(
                        f"word_similarity({{}}, {column}) > {{}}",
                        value,
                        search_params.similarity_threshold,
                    )
                else:
                    # Default to case-insensitive regex matching
                    add_condition(f"{column} ~* {{}}", value)

        # Construct the final query
        if not conditions:
            # If no filters, return all samples without expensive joins
            query = "SELECT * FROM samples ORDER BY sample_id"
        else:
            # If filters exist, append them to the base query with joins
            query = (
                base_query
                + " WHERE "
                + " AND ".join(conditions)
                + " ORDER BY s.sample_id"
            )

        async with self.session() as conn:
            records = await conn.fetch(query, *params)
            return [SampleInDB.model_validate(dict(record)) for record in records]

    # Higher-level database operations for Accelerator Types
    async def get_all_accelerator_types(self) -> list[AcceleratorTypeInDB]:
        """Fetch all accelerator types from the database."""
        async with self.session() as conn:
            records = await conn.fetch(
                "SELECT * FROM accelerator_types ORDER BY accelerator_type_id"
            )
            return [
                AcceleratorTypeInDB.model_validate(dict(record)) for record in records
            ]

    # Higher-level database operations for Frameworks
    async def get_all_frameworks(self) -> list[FrameworkInDB]:
        """Fetch all frameworks from the database."""
        async with self.session() as conn:
            records = await conn.fetch("SELECT * FROM frameworks ORDER BY framework_id")
            return [FrameworkInDB.model_validate(dict(record)) for record in records]

    # Higher-level database operations for Detectors
    async def get_all_detectors(self) -> list[DetectorInDB]:
        """Fetch all detectors from the database."""
        async with self.session() as conn:
            records = await conn.fetch("SELECT * FROM detectors ORDER BY detector_id")
            return [DetectorInDB.model_validate(dict(record)) for record in records]

    # Higher-level database operations for Campaigns
    async def get_all_campaigns(self) -> list[CampaignInDB]:
        """Fetch all campaigns from the database."""
        async with self.session() as conn:
            records = await conn.fetch("SELECT * FROM campaigns ORDER BY campaign_id")
            return [CampaignInDB.model_validate(dict(record)) for record in records]

    async def generate_schema_mapping(self) -> dict[str, str]:
        """
        Dynamically generates schema mapping by introspecting the database.

        Returns:
            A dictionary mapping logical field names to database column references.
        """
        mapping: dict[str, str] = {}

        async with self.session() as conn:
            # Get all tables and their columns
            tables = await conn.fetch("""
                SELECT
                    t.table_name,
                    array_agg(c.column_name) as columns
                FROM
                    information_schema.tables t
                JOIN
                    information_schema.columns c ON t.table_name = c.table_name
                WHERE
                    t.table_schema = 'public' AND
                    t.table_type = 'BASE TABLE' AND
                    t.table_name IN ('samples', 'detectors', 'campaigns', 'frameworks', 'accelerator_types')
                GROUP BY
                    t.table_name
            """)

            # Add basic mappings
            for record in tables:
                table = record["table_name"]
                for column in record["columns"]:
                    # For most tables, use table_name.column_name mapping
                    if column == "name":
                        # Special case for name columns - use logical names
                        if table == "samples":
                            mapping["name"] = f"{table}.{column}"
                        else:
                            # Remove 's' from end of table name for singular form
                            singular = table[:-1] if table.endswith("s") else table
                            mapping[singular] = f"{table}.{column}"
                    elif column == "metadata" and table == "samples":
                        mapping["metadata"] = f"{table}.{column}"
                    elif column == "metadata_search_text" and table == "samples":
                        mapping["metadata_search_text"] = f"{table}.{column}"

            return mapping
