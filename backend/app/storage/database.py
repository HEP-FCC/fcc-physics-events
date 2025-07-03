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
from app.models.dataset import DatasetCreate
from app.models.detector import DetectorCreate
from app.models.dropdown import DropdownItem
from app.models.stage import StageCreate

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

        Available fields for sorting:
        - Dataset fields: dataset_id, name, created_at, last_edited_at
        - Joined fields: detector_name, campaign_name, stage_name, accelerator_name
        - Metadata fields: metadata.* (any key in the JSONB metadata field)
        """
        logger.info("Generating static schema mapping for query parser.")
        return {
            "name": "d.name",
            "detector": "det.name",
            "campaign": "c.name",
            "stage": "s.name",
            "accelerator": "at.name",
            # This field allows querying specific keys within the JSONB object.
            "metadata": "d.metadata",
            # This virtual field allows full-text search on all metadata values.
            "metadata_text": "jsonb_values_to_text(d.metadata)",
            # Additional dataset fields available for sorting
            "dataset_id": "d.dataset_id",
            "created_at": "d.created_at",
            "last_edited_at": "d.last_edited_at",
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
                    stage_name = path_parts[6].replace("Events", "")
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
                stage_id = await self._get_or_create_entity(
                    conn, StageCreate, "stages", name=stage_name
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
                # Extract metadata and remove the process-name since it's stored in the name field
                metadata_dict = process_data.model_dump(by_alias=True)
                metadata_dict.pop(
                    "process-name", None
                )  # Remove process-name from metadata

                dataset_to_create = DatasetCreate(
                    name=process_data.process_name,
                    metadata=metadata_dict,
                    accelerator_id=accelerator_id,
                    stage_id=stage_id,
                    campaign_id=campaign_id,
                    detector_id=detector_id,
                )
                metadata_json = json.dumps(dataset_to_create.metadata)

                await conn.execute(
                    """
                    INSERT INTO datasets (name, accelerator_id, stage_id, campaign_id, detector_id, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (name) DO UPDATE
                    SET metadata = EXCLUDED.metadata,
                        accelerator_id = EXCLUDED.accelerator_id,
                        stage_id = EXCLUDED.stage_id,
                        campaign_id = EXCLUDED.campaign_id,
                        detector_id = EXCLUDED.detector_id,
                        last_edited_at = (NOW() AT TIME ZONE 'utc');
                    """,
                    dataset_to_create.name,
                    dataset_to_create.accelerator_id,
                    dataset_to_create.stage_id,
                    dataset_to_create.campaign_id,
                    dataset_to_create.detector_id,
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

    async def get_stages(
        self,
        accelerator_name: str | None = None,
        campaign_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all stages for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT s.stage_id as id, s.name FROM stages s"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            campaign_id = None
            detector_id = None

            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(
                    conn, "accelerators", accelerator_name
                )
                if accelerator_id is None:
                    return []  # No matching accelerator found

            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(
                    conn, "campaigns", campaign_name
                )
                if campaign_id is None:
                    return []  # No matching campaign found

            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(
                    conn, "detectors", detector_name
                )
                if detector_id is None:
                    return []  # No matching detector found

            if (
                accelerator_id is not None
                or campaign_id is not None
                or detector_id is not None
            ):
                query += " INNER JOIN datasets d ON s.stage_id = d.stage_id"

                if accelerator_id is not None:
                    conditions.append(f"d.accelerator_id = ${len(params) + 1}")
                    params.append(accelerator_id)

                if campaign_id is not None:
                    conditions.append(f"d.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)

                if detector_id is not None:
                    conditions.append(f"d.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY s.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_campaigns(
        self,
        accelerator_name: str | None = None,
        stage_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all campaigns for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT c.campaign_id as id, c.name FROM campaigns c"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            stage_id = None
            detector_id = None

            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(
                    conn, "accelerators", accelerator_name
                )
                if accelerator_id is None:
                    return []  # No matching accelerator found

            if stage_name is not None:
                stage_id = await self._get_entity_id_by_name(conn, "stages", stage_name)
                if stage_id is None:
                    return []  # No matching stage found

            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(
                    conn, "detectors", detector_name
                )
                if detector_id is None:
                    return []  # No matching detector found

            if (
                accelerator_id is not None
                or stage_id is not None
                or detector_id is not None
            ):
                query += " INNER JOIN datasets d ON c.campaign_id = d.campaign_id"

                if accelerator_id is not None:
                    conditions.append(f"d.accelerator_id = ${len(params) + 1}")
                    params.append(accelerator_id)

                if stage_id is not None:
                    conditions.append(f"d.stage_id = ${len(params) + 1}")
                    params.append(stage_id)

                if detector_id is not None:
                    conditions.append(f"d.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY c.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_detectors(
        self,
        accelerator_name: str | None = None,
        stage_name: str | None = None,
        campaign_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all detectors for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT det.detector_id as id, det.name FROM detectors det"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            accelerator_id = None
            stage_id = None
            campaign_id = None

            if accelerator_name is not None:
                accelerator_id = await self._get_entity_id_by_name(
                    conn, "accelerators", accelerator_name
                )
                if accelerator_id is None:
                    return []  # No matching accelerator found

            if stage_name is not None:
                stage_id = await self._get_entity_id_by_name(conn, "stages", stage_name)
                if stage_id is None:
                    return []  # No matching stage found

            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(
                    conn, "campaigns", campaign_name
                )
                if campaign_id is None:
                    return []  # No matching campaign found

            # Always consider accelerator filtering via direct relationship
            if accelerator_id is not None:
                conditions.append(f"det.accelerator_id = ${len(params) + 1}")
                params.append(accelerator_id)

            # For stage and campaign filtering, use datasets table
            if stage_id is not None or campaign_id is not None:
                query += " INNER JOIN datasets d ON det.detector_id = d.detector_id"

                if stage_id is not None:
                    conditions.append(f"d.stage_id = ${len(params) + 1}")
                    params.append(stage_id)

                if campaign_id is not None:
                    conditions.append(f"d.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY det.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_accelerators(
        self,
        stage_name: str | None = None,
        campaign_name: str | None = None,
        detector_name: str | None = None,
    ) -> list[DropdownItem]:
        """Gets all accelerators for the navigation dropdown, optionally filtered by other entities."""
        query = "SELECT DISTINCT a.accelerator_id as id, a.name FROM accelerators a"
        params: list[int] = []
        conditions: list[str] = []

        async with self.session() as conn:
            # Convert names to IDs if provided
            stage_id = None
            campaign_id = None
            detector_id = None

            if stage_name is not None:
                stage_id = await self._get_entity_id_by_name(conn, "stages", stage_name)
                if stage_id is None:
                    return []  # No matching stage found

            if campaign_name is not None:
                campaign_id = await self._get_entity_id_by_name(
                    conn, "campaigns", campaign_name
                )
                if campaign_id is None:
                    return []  # No matching campaign found

            if detector_name is not None:
                detector_id = await self._get_entity_id_by_name(
                    conn, "detectors", detector_name
                )
                if detector_id is None:
                    return []  # No matching detector found

            if (
                stage_id is not None
                or campaign_id is not None
                or detector_id is not None
            ):
                query += " INNER JOIN datasets d ON a.accelerator_id = d.accelerator_id"

                if stage_id is not None:
                    conditions.append(f"d.stage_id = ${len(params) + 1}")
                    params.append(stage_id)

                if campaign_id is not None:
                    conditions.append(f"d.campaign_id = ${len(params) + 1}")
                    params.append(campaign_id)

                if detector_id is not None:
                    conditions.append(f"d.detector_id = ${len(params) + 1}")
                    params.append(detector_id)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY a.name"

            records = await conn.fetch(query, *params)
            return [DropdownItem.model_validate(dict(record)) for record in records]

    async def get_datasets_by_ids(self, dataset_ids: list[int]) -> list[dict[str, Any]]:
        """
        Get datasets by their IDs with all details and related entity names.
        Returns a list of dictionaries with all dataset fields plus metadata flattened to top-level.
        """
        if not dataset_ids:
            return []

        # Create placeholders for the dataset IDs
        placeholders = ", ".join(f"${i+1}" for i in range(len(dataset_ids)))

        query = f"""
            SELECT
                d.dataset_id,
                d.name,
                d.accelerator_id,
                d.stage_id,
                d.campaign_id,
                d.detector_id,
                d.metadata,
                d.created_at,
                d.last_edited_at,
                a.name as accelerator_name,
                s.name as stage_name,
                c.name as campaign_name,
                det.name as detector_name
            FROM datasets d
            LEFT JOIN accelerators a ON d.accelerator_id = a.accelerator_id
            LEFT JOIN stages s ON d.stage_id = s.stage_id
            LEFT JOIN campaigns c ON d.campaign_id = c.campaign_id
            LEFT JOIN detectors det ON d.detector_id = det.detector_id
            WHERE d.dataset_id IN ({placeholders})
            ORDER BY d.dataset_id
        """

        async with self.session() as conn:
            records = await conn.fetch(query, *dataset_ids)

            result = []
            for record in records:
                # Convert record to dict
                dataset_dict = dict(record)

                # Extract and flatten metadata
                metadata_str = dataset_dict.pop("metadata", r"{}")
                metadata = json.loads(metadata_str)

                # Merge metadata keys into the main dictionary
                # If there's a conflict, the original dataset fields take precedence
                for key, value in metadata.items():
                    if key not in dataset_dict:
                        dataset_dict[key] = value

                result.append(dataset_dict)

            return result

    async def get_sorting_fields(self) -> dict[str, Any]:
        """
        Dynamically fetch available sorting fields from the database schema.
        Returns categorized lists of sortable fields based on the current database structure.
        """
        async with self.session() as conn:
            # Get dataset table columns
            dataset_columns_query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'datasets'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            dataset_columns = await conn.fetch(dataset_columns_query)

            # Get foreign key relationships from datasets table
            foreign_keys_query = """
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'datasets'
                AND tc.table_schema = 'public'
            """
            foreign_keys = await conn.fetch(foreign_keys_query)

            # Get common metadata fields by analyzing actual data
            metadata_fields_query = """
                SELECT DISTINCT jsonb_object_keys(metadata) as metadata_key
                FROM datasets
                WHERE metadata IS NOT NULL
                AND metadata != 'null'::jsonb
                ORDER BY metadata_key
                LIMIT 50
            """
            metadata_keys = await conn.fetch(metadata_fields_query)

            # Get nested metadata fields (one level deep)
            nested_metadata_query = """
                SELECT DISTINCT
                    parent_key || '.' || child_key as nested_key
                FROM (
                    SELECT
                        parent_key,
                        jsonb_object_keys(parent_value) as child_key
                    FROM (
                        SELECT
                            key as parent_key,
                            value as parent_value
                        FROM datasets, jsonb_each(metadata)
                        WHERE metadata IS NOT NULL
                        AND metadata != 'null'::jsonb
                        AND jsonb_typeof(value) = 'object'
                    ) nested_objects
                ) nested_keys
                ORDER BY nested_key
                LIMIT 50
            """
            nested_metadata_keys = await conn.fetch(nested_metadata_query)

            # Build the dataset fields list (excluding foreign keys and metadata)
            dataset_fields = []
            foreign_key_columns = set()

            # First, collect all foreign key column names
            for fk in foreign_keys:
                foreign_key_columns.add(fk["column_name"])

            # Now filter dataset columns
            for col in dataset_columns:
                col_name = col["column_name"]
                if col_name in foreign_key_columns:
                    # This is a foreign key column, skip it
                    continue
                elif col_name == "metadata":
                    # Skip metadata column
                    continue
                else:
                    # This is a regular dataset field
                    dataset_fields.append(col_name)

            # Build joined fields list dynamically from foreign key relationships
            joined_fields = []
            for fk in foreign_keys:
                fk_column = fk["column_name"]

                # Convert foreign key column name to corresponding joined field name
                # e.g., accelerator_id -> accelerator_name
                if fk_column.endswith("_id"):
                    base_name = fk_column[:-3]  # Remove '_id' suffix
                    joined_field_name = f"{base_name}_name"
                    joined_fields.append(joined_field_name)

            # Build metadata fields list with 'metadata.' prefix
            metadata_fields = [
                f"metadata.{row['metadata_key']}" for row in metadata_keys
            ]

            # Build nested metadata fields list
            nested_fields = [
                f"metadata.{row['nested_key']}" for row in nested_metadata_keys
            ]

            # Combine all fields into a single flat list
            all_fields = []
            all_fields.extend(dataset_fields)
            all_fields.extend(joined_fields)
            all_fields.extend(metadata_fields)
            all_fields.extend(nested_fields)

            # Sort alphabetically for better UX
            all_fields.sort()

            return {
                "fields": all_fields,
                "count": len(all_fields),
                "info": "All available fields for sorting. Use 'metadata.key' format for JSON fields.",
            }
