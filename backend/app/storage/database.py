"""
This file contains the Database class, which manages an asyncpg connection
pool and provides higher-level PostgreSQL database functions, including
data import logic.
"""

import json
from pathlib import Path
from typing import Any, TypeVar

import asyncpg
from asyncpg.pool import Pool
from pydantic import BaseModel

from app.config import Config
from app.fcc_dict_parser import ProcessCollection
from app.logging import get_logger
from app.models.accelerator import AcceleratorCreate
from app.models.campaign import CampaignCreate
from app.models.detector import DetectorCreate
from app.models.dropdown import DropdownItem
from app.models.framework import FrameworkCreate
from app.models.process import ProcessCreate

logger = get_logger()
T = TypeVar("T", bound=BaseModel)


class AsyncSessionContextManager:
    """Async context manager for acquiring and releasing a connection from the pool."""

    def __init__(self, pool: Pool):
        self._pool = pool
        self._connection: asyncpg.Connection | None = None

    async def __aenter__(self) -> asyncpg.Connection:
        self._connection = await self._pool.acquire()
        return self._connection

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._connection:
            await self._pool.release(self._connection)


class Database:
    """Manages the connection pool and provides higher-level database functions."""

    _pool: Pool | None = None

    async def setup(self, config: Config) -> None:
        """Creates the connection pool and initializes the database."""
        if self._pool:
            return
        try:
            logger.info("Setting up the database...")
            connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
            self._pool = await asyncpg.create_pool(
                dsn=connection_string, min_size=5, max_size=20
            )
            logger.info("Database connection pool created successfully.")

            logger.info("Applying database schema...")
            schema_file = config.get(
                "schema_file", Path(__file__).parent / "database.sql"
            )
            with open(schema_file, encoding="utf-8") as f:
                schema_sql = f.read()
            async with self.session() as conn:
                await conn.execute(schema_sql)
            logger.info("Database setup successfully.")
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise

    def session(self) -> AsyncSessionContextManager:
        """Provides a session context manager for raw database interactions."""
        if self._pool is None:
            raise RuntimeError(
                "Connection pool is not initialized. Call setup() first."
            )
        return AsyncSessionContextManager(self._pool)

    async def aclose(self) -> None:
        """Closes the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed.")

    async def generate_schema_mapping(self) -> dict[str, str]:
        """
        Generates a static schema mapping for the query parser.

        This is more robust than database introspection for a fixed query structure.
        It maps logical query fields to their aliased SQL counterparts.
        """
        logger.info("Generating static schema mapping for query parser.")
        return {
            "name": "p.name",
            "detector": "d.name",
            "campaign": "c.name",
            "campaign_name": "c.name",
            "framework": "f.name",
            "framework_name": "f.name",
            "accelerator": "at.name",
            # This virtual field allows full-text search on all metadata values.
            "metadata_text": "jsonb_values_to_text(p.metadata)",
            # This field allows querying specific keys within the JSONB object.
            "metadata": "p.metadata",
        }

    async def _get_or_create_entity(
        self, conn: asyncpg.Connection, model: type[T], table_name: str, **kwargs: Any
    ) -> int:
        """Generic function to get an entity by name or create it."""
        name = kwargs.get("name")
        if not name:
            raise ValueError("A 'name' is required to find or create an entity.")

        id_column = f"{table_name.rstrip('s')}_id"
        query = f"SELECT {id_column} FROM {table_name} WHERE name = $1"

        record = await conn.fetchrow(query, name)
        if record:
            return int(record[id_column])

        instance = model(**kwargs)
        data = instance.model_dump(exclude_unset=True)
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f"${i+1}" for i in range(len(data)))

        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING {id_column}"

        new_id = await conn.fetchval(insert_query, *data.values())
        if new_id is None:
            raise RuntimeError(
                f"Failed to create or find entity in {table_name} with name {name}"
            )
        return int(new_id)

    async def import_fcc_dict(self, json_content: bytes) -> None:
        """Parses JSON content and upserts the data into the database."""
        try:
            raw_data = json.loads(json_content)
            collection = ProcessCollection.model_validate(raw_data)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format") from e

        async with self.session() as conn:
            for process_data in collection.processes:
                logger.info(f"Processing: {process_data.process_name}")
                path_parts = Path(process_data.path).parts
                try:
                    accelerator_name = path_parts[4]
                    framework_name = path_parts[6].replace("Events", "")
                    campaign_name = path_parts[7]
                    detector_name = path_parts[8]
                except IndexError:
                    logger.warning(
                        f"Could not parse path for {process_data.process_name}. Skipping."
                    )
                    continue

                accelerator_id = await self._get_or_create_entity(
                    conn,
                    AcceleratorCreate,
                    "accelerators",
                    name=accelerator_name,
                    description=f"Accelerator for {accelerator_name.upper()} collisions",
                )
                framework_id = await self._get_or_create_entity(
                    conn, FrameworkCreate, "frameworks", name=framework_name
                )
                campaign_id = await self._get_or_create_entity(
                    conn, CampaignCreate, "campaigns", name=campaign_name
                )
                detector_id = await self._get_or_create_entity(
                    conn,
                    DetectorCreate,
                    "detectors",
                    name=detector_name,
                    accelerator_id=accelerator_id,
                )
                process_to_create = ProcessCreate(
                    name=process_data.process_name,
                    metadata=process_data.model_dump(by_alias=True, exclude={"path"}),
                    accelerator_id=accelerator_id,
                    framework_id=framework_id,
                    campaign_id=campaign_id,
                    detector_id=detector_id,
                )
                metadata_json = json.dumps(process_to_create.metadata)

                await conn.execute(
                    """
                    INSERT INTO processes (name, accelerator_id, framework_id, campaign_id, detector_id, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (name) DO UPDATE
                    SET metadata = EXCLUDED.metadata,
                        accelerator_id = EXCLUDED.accelerator_id,
                        framework_id = EXCLUDED.framework_id,
                        campaign_id = EXCLUDED.campaign_id,
                        detector_id = EXCLUDED.detector_id;
                    """,
                    process_to_create.name,
                    process_to_create.accelerator_id,
                    process_to_create.framework_id,
                    process_to_create.campaign_id,
                    process_to_create.detector_id,
                    metadata_json,
                )
        logger.info("Successfully parsed and inserted all data.")

    async def _get_entity_id_by_name(
        self, conn: asyncpg.Connection, table_name: str, name: str
    ) -> int | None:
        """Helper function to get an entity ID by name."""
        id_column = f"{table_name.rstrip('s')}_id"
        query = f"SELECT {id_column} FROM {table_name} WHERE name = $1"
        
        record = await conn.fetchrow(query, name)
        return int(record[id_column]) if record else None

    async def get_frameworks(
        self,
        accelerator_name: str | None = None,
        campaign_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all frameworks for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT f.framework_id as id, f.name FROM frameworks f"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            campaign_id = None
            detector_id = None
            
            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(conn, "accelerators", accelerator_name)
                if accelerator_id is None:
                    return []  # No matching accelerator found
            
            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(conn, "campaigns", campaign_name)
                if campaign_id is None:
                    return []  # No matching campaign found
            
            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(conn, "detectors", detector_name)
                if detector_id is None:
                    return []  # No matching detector found

            if accelerator_id is not None or campaign_id is not None or detector_id is not None:
                query += " INNER JOIN processes p ON f.framework_id = p.framework_id"
                
                if accelerator_id is not None:
                    conditions.append(f"p.accelerator_id = ${len(params) + 1}")
                    params.append(accelerator_id)
                
                if campaign_id is not None:
                    conditions.append(f"p.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)
                
                if detector_id is not None:
                    conditions.append(f"p.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY f.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_campaigns(
        self,
        accelerator_name: str | None = None,
        framework_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all campaigns for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT c.campaign_id as id, c.name FROM campaigns c"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            framework_id = None
            detector_id = None
            
            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(conn, "accelerators", accelerator_name)
                if accelerator_id is None:
                    return []  # No matching accelerator found
            
            if framework_name is not None:
                framework_id = await self._get_entity_id_by_name(conn, "frameworks", framework_name)
                if framework_id is None:
                    return []  # No matching framework found
            
            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(conn, "detectors", detector_name)
                if detector_id is None:
                    return []  # No matching detector found

            if accelerator_id is not None or framework_id is not None or detector_id is not None:
                query += " INNER JOIN processes p ON c.campaign_id = p.campaign_id"
                
                if accelerator_id is not None:
                    conditions.append(f"p.accelerator_id = ${len(params) + 1}")
                    params.append(accelerator_id)
                
                if framework_id is not None:
                    conditions.append(f"p.framework_id = ${len(params) + 1}")
                    params.append(framework_id)
                
                if detector_id is not None:
                    conditions.append(f"p.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY c.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_detectors(
        self,
        accelerator_name: str | None = None,
        framework_name: str | None = None,
        campaign_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all detectors for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT d.detector_id as id, d.name FROM detectors d"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            framework_id = None
            campaign_id = None
            
            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(conn, "accelerators", accelerator_name)
                if accelerator_id is None:
                    return []  # No matching accelerator found
            
            if framework_name is not None:
                framework_id = await self._get_entity_id_by_name(conn, "frameworks", framework_name)
                if framework_id is None:
                    return []  # No matching framework found
            
            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(conn, "campaigns", campaign_name)
                if campaign_id is None:
                    return []  # No matching campaign found

            # Always consider accelerator filtering via direct relationship
            if accelerator_id is not None:
                conditions.append(f"d.accelerator_id = ${len(params) + 1}")
                params.append(accelerator_id)

            # For framework and campaign filtering, use processes table
            if framework_id is not None or campaign_id is not None:
                query += " INNER JOIN processes p ON d.detector_id = p.detector_id"
                
                if framework_id is not None:
                    conditions.append(f"p.framework_id = ${len(params) + 1}")
                    params.append(framework_id)
                
                if campaign_id is not None:
                    conditions.append(f"p.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY d.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_accelerators(
        self,
        framework_name: str | None = None,
        campaign_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all accelerators for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT a.accelerator_id as id, a.name FROM accelerators a"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            framework_id = None
            campaign_id = None
            detector_id = None
            
            if framework_name is not None:
                framework_id = await self._get_entity_id_by_name(conn, "frameworks", framework_name)
                if framework_id is None:
                    return []  # No matching framework found
            
            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(conn, "campaigns", campaign_name)
                if campaign_id is None:
                    return []  # No matching campaign found
            
            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(conn, "detectors", detector_name)
                if detector_id is None:
                    return []  # No matching detector found

            if framework_id is not None or campaign_id is not None or detector_id is not None:
                query += " INNER JOIN processes p ON a.accelerator_id = p.accelerator_id"
                
                if framework_id is not None:
                    conditions.append(f"p.framework_id = ${len(params) + 1}")
                    params.append(framework_id)
                
                if campaign_id is not None:
                    conditions.append(f"p.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)
                
                if detector_id is not None:
                    conditions.append(f"p.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY a.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]
