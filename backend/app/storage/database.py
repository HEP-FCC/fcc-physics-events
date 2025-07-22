"""
This file contains the Database class, which manages an asyncpg connection
pool and provides higher-level PostgreSQL database functions, including
data import logic.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import asyncpg
from asyncpg.pool import Pool
from pydantic import BaseModel

from app.fcc_dict_parser import DatasetCollection
from app.models.accelerator import AcceleratorCreate
from app.models.campaign import CampaignCreate
from app.models.dataset import (
    DatasetCreate,
)
from app.models.detector import DetectorCreate
from app.models.stage import StageCreate
from app.utils import Config, get_config, get_logger

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

            # Use advisory lock to prevent concurrent schema application from multiple workers
            async with self.session() as conn:
                # Use a consistent advisory lock ID for this application
                # This prevents multiple workers from applying schema simultaneously
                await conn.execute("SELECT pg_advisory_lock(1234567890)")
                try:
                    # Check if our application schema has been applied by looking for our custom function
                    # This is more reliable than checking for tables since the public schema always exists
                    schema_applied = await conn.fetchval("""
                        SELECT EXISTS(
                            SELECT 1 FROM pg_proc p
                            JOIN pg_namespace n ON p.pronamespace = n.oid
                            WHERE n.nspname = 'public'
                            AND p.proname = 'jsonb_values_to_text'
                        )
                    """)

                    if not schema_applied:
                        logger.info(
                            "Application schema not found, applying schema (this worker won the race)..."
                        )
                        async with conn.transaction():
                            await conn.execute(schema_sql)
                        logger.info("Database schema applied successfully")
                    else:
                        logger.info(
                            "Application schema already exists, skipping schema application..."
                        )
                finally:
                    # Release advisory lock
                    await conn.execute("SELECT pg_advisory_unlock(1234567890)")

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
        Generates a dynamic schema mapping for the query parser based on database schema.

        This method analyzes the database structure and creates mappings for:
        - Dataset fields: dataset_id, name, created_at, last_edited_at
        - Dynamic joined fields: {entity}_name for each navigation entity
        - Metadata fields: metadata.* (any key in the JSONB metadata field)
        """
        logger.info("Generating dynamic schema mapping for query parser.")

        # Add dynamic mappings for navigation entities
        try:
            from app.schema_discovery import get_schema_discovery

            config = get_config()
            main_table = config["application"]["main_table"]

            async with self.session() as conn:
                # Get the primary key column dynamically
                primary_key_column = await self._get_main_table_primary_key(
                    conn, main_table
                )

                # Base mapping for dataset fields and special fields
                mapping = {
                    "name": "d.name",
                    "metadata": "d.metadata",
                    "metadata_text": "jsonb_values_to_text(d.metadata)",
                    primary_key_column: f"d.{primary_key_column}",
                    "created_at": "d.created_at",
                    "last_edited_at": "d.last_edited_at",
                }

                schema_discovery = await get_schema_discovery(conn)
                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure(main_table)
                )

                # Generate aliases using the same logic as the query parser
                used_aliases = {"d"}
                for entity_key, table_info in navigation_analysis[
                    "navigation_tables"
                ].items():
                    name_column = table_info["name_column"]

                    # Generate unique alias using same logic as QueryParser
                    alias = self._generate_unique_alias(entity_key, used_aliases)
                    used_aliases.add(alias)

                    # Add mapping for entity field
                    mapping[entity_key] = f"{alias}.{name_column}"

        except Exception as e:
            logger.error(f"Failed to generate dynamic schema mapping: {e}")
            # Fallback to empty mapping for navigation entities if schema discovery fails

        return mapping

    def _generate_unique_alias(self, entity_key: str, used_aliases: set[str]) -> str:
        """Generate a unique alias for a table, avoiding conflicts. Same logic as QueryParser."""
        # Start with first 3-4 characters
        base_alias = entity_key[:3] if len(entity_key) > 3 else entity_key

        # If already used, try first 4 characters
        if base_alias in used_aliases and len(entity_key) > 3:
            base_alias = entity_key[:4]

        # If still conflicts, add number suffix
        if base_alias in used_aliases:
            counter = 1
            while f"{base_alias}{counter}" in used_aliases:
                counter += 1
            base_alias = f"{base_alias}{counter}"

        return base_alias

    async def _get_main_table_primary_key(
        self, conn: asyncpg.Connection, main_table: str
    ) -> str:
        """Get the primary key column name for the main table."""
        query = """
            SELECT column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.table_constraints tc
                ON kcu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND kcu.table_name = $1
            AND kcu.table_schema = 'public'
            ORDER BY kcu.ordinal_position
            LIMIT 1
        """
        result = await conn.fetchval(query, main_table)
        if not result:
            # Fallback to convention-based naming
            table_singular = main_table.rstrip("s")
            return f"{table_singular}_id"
        return result

    async def _get_or_create_entity(
        self, conn: asyncpg.Connection, model: type[T], table_name: str, **kwargs: Any
    ) -> int:
        """Generic function to get an entity by name or create it within a transaction."""
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

        try:
            new_id = await conn.fetchval(insert_query, *data.values())
            if new_id is None:
                raise RuntimeError(
                    f"Failed to create entity in {table_name} with name {name}"
                )
            return int(new_id)
        except asyncpg.UniqueViolationError:
            # Handle race condition where another transaction created the entity
            record = await conn.fetchrow(query, name)
            if record:
                return int(record[id_column])
            raise RuntimeError(
                f"Failed to create or find entity in {table_name} with name {name}"
            )

    async def import_fcc_dict(self, json_content: bytes) -> None:
        """Parses JSON content and upserts the data into the database with proper transaction handling."""
        try:
            raw_data = json.loads(json_content)
            collection = DatasetCollection.model_validate(raw_data)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format") from e
        except Exception as e:
            raise ValueError(f"Invalid data format: {e}") from e

        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            # Use an explicit transaction for all operations
            async with conn.transaction():
                processed_count = 0
                failed_count = 0

                for idx, dataset_data in enumerate(collection.processes):
                    try:
                        # Generate a fallback name if process_name is missing
                        dataset_name = dataset_data.process_name
                        if not dataset_name:
                            # Create a unique fallback name using timestamp and index
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            short_uuid = str(uuid.uuid4())[:8]
                            dataset_name = (
                                f"unnamed_dataset_{timestamp}_{short_uuid}_{idx}"
                            )
                            logger.warning(
                                f"Dataset at index {idx} has no process_name. Using fallback name: {dataset_name}"
                            )

                        logger.info(f"Processing: {dataset_name}")

                        # Initialize foreign key IDs to None
                        accelerator_id = None
                        stage_id = None
                        campaign_id = None
                        detector_id = None

                        # Try to parse path components if path is available
                        if dataset_data.path:
                            try:
                                path_parts = Path(dataset_data.path).parts
                                accelerator_name = (
                                    path_parts[4] if len(path_parts) > 4 else None
                                )
                                stage_name = (
                                    path_parts[6].replace("Events", "")
                                    if len(path_parts) > 6
                                    else None
                                )
                                campaign_name = (
                                    path_parts[7] if len(path_parts) > 7 else None
                                )
                                detector_name = (
                                    path_parts[8] if len(path_parts) > 8 else None
                                )

                                # Only create entities if the names are valid (not None or empty)
                                if accelerator_name and accelerator_name.strip():
                                    accelerator_id = await self._get_or_create_entity(
                                        conn,
                                        AcceleratorCreate,
                                        "accelerators",
                                        name=accelerator_name.strip(),
                                    )

                                if stage_name and stage_name.strip():
                                    stage_id = await self._get_or_create_entity(
                                        conn,
                                        StageCreate,
                                        "stages",
                                        name=stage_name.strip(),
                                    )

                                if campaign_name and campaign_name.strip():
                                    campaign_id = await self._get_or_create_entity(
                                        conn,
                                        CampaignCreate,
                                        "campaigns",
                                        name=campaign_name.strip(),
                                    )

                                if (
                                    detector_name
                                    and detector_name.strip()
                                    and accelerator_id
                                ):
                                    detector_id = await self._get_or_create_entity(
                                        conn,
                                        DetectorCreate,
                                        "detectors",
                                        name=detector_name.strip(),
                                        accelerator_id=accelerator_id,
                                    )

                            except (IndexError, AttributeError) as e:
                                logger.warning(
                                    f"Could not parse path components for {dataset_name}: {e}. "
                                    f"Will store dataset with null foreign key references."
                                )
                        else:
                            logger.warning(
                                f"Dataset {dataset_name} has no path. Will store with null foreign key references."
                            )

                        # Get all metadata excluding process_name
                        metadata_dict = dataset_data.get_all_metadata()

                        # Handle potential name conflicts in the database
                        final_name = dataset_name
                        conflict_counter = 1
                        while True:
                            try:
                                dataset_to_create = DatasetCreate(
                                    name=final_name,
                                    metadata=metadata_dict,
                                    accelerator_id=accelerator_id,
                                    stage_id=stage_id,
                                    campaign_id=campaign_id,
                                    detector_id=detector_id,
                                )
                                metadata_json = json.dumps(dataset_to_create.metadata)

                                query = f"""
                                    INSERT INTO {main_table} (name, accelerator_id, stage_id, campaign_id, detector_id, metadata)
                                    VALUES ($1, $2, $3, $4, $5, $6)
                                    ON CONFLICT (name) DO UPDATE
                                    SET metadata = EXCLUDED.metadata,
                                        accelerator_id = EXCLUDED.accelerator_id,
                                        stage_id = EXCLUDED.stage_id,
                                        campaign_id = EXCLUDED.campaign_id,
                                        detector_id = EXCLUDED.detector_id,
                                        last_edited_at = (NOW() AT TIME ZONE 'utc');
                                    """

                                await conn.execute(
                                    query,
                                    dataset_to_create.name,
                                    dataset_to_create.accelerator_id,
                                    dataset_to_create.stage_id,
                                    dataset_to_create.campaign_id,
                                    dataset_to_create.detector_id,
                                    metadata_json,
                                )
                                processed_count += 1
                                break  # Success, exit the retry loop
                            except Exception as e:
                                if (
                                    "duplicate key value violates unique constraint"
                                    in str(e).lower()
                                ):
                                    # Name conflict, try with a different name
                                    final_name = (
                                        f"{dataset_name}_conflict_{conflict_counter}"
                                    )
                                    conflict_counter += 1
                                    logger.warning(
                                        f"Name conflict for {dataset_name}, trying {final_name}"
                                    )
                                    if conflict_counter > 10:  # Prevent infinite loops
                                        logger.error(
                                            f"Too many name conflicts for {dataset_name}, skipping"
                                        )
                                        failed_count += 1
                                        break
                                else:
                                    # Some other error, re-raise it
                                    raise
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to process dataset at index {idx}: {e}")
                        # Continue processing other datasets within the same transaction

                if failed_count > 0:
                    logger.warning(
                        f"Import completed with {failed_count} failures out of {processed_count + failed_count} total datasets"
                    )
                else:
                    logger.info(
                        f"Successfully processed all {processed_count} datasets"
                    )

                # If more than half of the datasets failed, consider it a critical failure
                total_datasets = processed_count + failed_count
                if total_datasets > 0 and failed_count > (total_datasets / 2):
                    raise RuntimeError(
                        f"Import failed: {failed_count}/{total_datasets} datasets could not be processed"
                    )

        logger.info("Import transaction completed successfully")

    async def _get_entity_id_by_name(
        self, conn: asyncpg.Connection, table_name: str, name: str
    ) -> int | None:
        """Helper function to get an entity ID by name."""
        id_column = f"{table_name.rstrip('s')}_id"
        query = f"SELECT {id_column} FROM {table_name} WHERE name = $1"

        record = await conn.fetchrow(query, name)
        return int(record[id_column]) if record else None

    async def get_entities_by_ids(self, entity_ids: list[int]) -> list[dict[str, Any]]:
        """
        Get entities by their IDs with all details and related entity names.
        Returns a list of dictionaries with all entity fields plus metadata flattened to top-level.
        """
        if not entity_ids:
            return []

        config = get_config()
        main_table = config["application"]["main_table"]

        # Build dynamic query with navigation tables
        try:
            from app.schema_discovery import get_schema_discovery

            async with self.session() as conn:
                # Get the primary key column dynamically
                primary_key_column = await self._get_main_table_primary_key(
                    conn, main_table
                )

                schema_discovery = await get_schema_discovery(conn)
                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure(main_table)
                )

                # Build SELECT fields dynamically
                select_fields = [
                    f"d.{primary_key_column}",
                    "d.name",
                    "d.metadata",
                    "d.created_at",
                    "d.last_edited_at",
                ]

                # Build JOIN clauses dynamically
                joins = [f"FROM {main_table} d"]
                used_aliases = {"d"}

                for entity_key, table_info in navigation_analysis[
                    "navigation_tables"
                ].items():
                    table_name = table_info["table_name"]
                    primary_key = table_info["primary_key"]
                    name_column = table_info["name_column"]

                    # Generate unique alias
                    alias = self._generate_unique_alias(entity_key, used_aliases)
                    used_aliases.add(alias)

                    # Add foreign key field to SELECT
                    select_fields.append(f"d.{entity_key}_id")

                    # Add name field to SELECT
                    select_fields.append(f"{alias}.{name_column} as {entity_key}_name")

                    # Add JOIN clause
                    joins.append(
                        f"LEFT JOIN {table_name} {alias} ON d.{entity_key}_id = {alias}.{primary_key}"
                    )

                query = f"""
                    SELECT {', '.join(select_fields)}
                    {' '.join(joins)}
                    WHERE d.{primary_key_column} = ANY($1)
                    ORDER BY d.{primary_key_column}
                """

        except Exception as e:
            logger.error(f"Failed to build dynamic query: {e}")
            # Fallback to simpler query without navigation joins
            # We still need to get the primary key for the fallback
            async with self.session() as conn:
                primary_key_column = await self._get_main_table_primary_key(
                    conn, main_table
                )

            query = f"""
                SELECT d.*
                FROM {main_table} d
                WHERE d.{primary_key_column} = ANY($1)
                ORDER BY d.{primary_key_column}
            """

        async with self.session() as conn:
            records = await conn.fetch(query, entity_ids)

            result = []
            for record in records:
                # Convert record to dict
                entity_dict = dict(record)

                # Extract and flatten metadata
                metadata_str = entity_dict.pop("metadata", r"{}")
                metadata = json.loads(metadata_str)

                # Merge metadata keys into the main dictionary
                # If there's a conflict, the original entity fields take precedence
                for key, value in metadata.items():
                    if key not in entity_dict:
                        entity_dict[key] = value

                result.append(entity_dict)

            return result

    async def get_entity_by_id(self, entity_id: int) -> dict[str, Any] | None:
        """
        Get a single entity by ID with all details and related entity names.
        Returns None if entity is not found.
        """
        entities = await self.get_entities_by_ids([entity_id])
        return entities[0] if entities else None

    async def update_entity(
        self, entity_id: int, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update an entity with the provided data using full replacement strategy.
        Returns the updated entity with all details.
        """
        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            # Get the primary key column dynamically
            primary_key_column = await self._get_main_table_primary_key(
                conn, main_table
            )

            async with conn.transaction():
                # First check if entity exists
                existing_check = await conn.fetchval(
                    f"SELECT {primary_key_column} FROM {main_table} WHERE {primary_key_column} = $1",
                    entity_id,
                )
                if not existing_check:
                    raise ValueError(f"Entity with ID {entity_id} not found")

                # Prepare update fields and values
                update_fields = []
                values = []
                param_count = 0

                # Always update last_edited_at
                update_fields.append("last_edited_at = (NOW() AT TIME ZONE 'utc')")

                # Handle each potential field update
                if "name" in update_data and update_data["name"] is not None:
                    param_count += 1
                    update_fields.append(f"name = ${param_count}")
                    values.append(update_data["name"])

                if "accelerator_id" in update_data:
                    param_count += 1
                    update_fields.append(f"accelerator_id = ${param_count}")
                    values.append(update_data["accelerator_id"])

                if "stage_id" in update_data:
                    param_count += 1
                    update_fields.append(f"stage_id = ${param_count}")
                    values.append(update_data["stage_id"])

                if "campaign_id" in update_data:
                    param_count += 1
                    update_fields.append(f"campaign_id = ${param_count}")
                    values.append(update_data["campaign_id"])

                if "detector_id" in update_data:
                    param_count += 1
                    update_fields.append(f"detector_id = ${param_count}")
                    values.append(update_data["detector_id"])

                if "metadata" in update_data:
                    param_count += 1
                    update_fields.append(f"metadata = ${param_count}")
                    # Convert metadata dict to JSON string
                    metadata_json = (
                        json.dumps(update_data["metadata"])
                        if update_data["metadata"] is not None
                        else None
                    )
                    values.append(metadata_json)

                if not update_fields:
                    # Only last_edited_at was updated
                    query = f"""
                        UPDATE {main_table}
                        SET last_edited_at = (NOW() AT TIME ZONE 'utc')
                        WHERE {primary_key_column} = ${param_count + 1}
                    """
                    values.append(entity_id)
                else:
                    # Build the complete update query
                    param_count += 1
                    update_clause = ", ".join(update_fields)
                    query = f"""
                        UPDATE {main_table}
                        SET {update_clause}
                        WHERE {primary_key_column} = ${param_count}
                    """
                    values.append(entity_id)

                try:
                    await conn.execute(query, *values)
                    logger.info(f"Successfully updated entity {entity_id}")
                except asyncpg.UniqueViolationError as e:
                    if "name" in str(e):
                        raise ValueError(
                            f"An entity with the name '{update_data.get('name')}' already exists"
                        )
                    raise ValueError(f"Update failed due to constraint violation: {e}")
                except asyncpg.ForeignKeyViolationError as e:
                    raise ValueError(f"Update failed due to invalid reference: {e}")

                # Return the updated entity
                updated_entity = await self.get_entity_by_id(entity_id)
                if not updated_entity:
                    raise RuntimeError(f"Failed to retrieve updated entity {entity_id}")

                return updated_entity

    async def get_sorting_fields(self) -> dict[str, Any]:
        """
        Dynamically fetch available sorting fields from the database schema.
        Returns categorized lists of sortable fields based on the current database structure.
        """
        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            # Get dataset table columns
            dataset_columns_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{main_table}'
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """
            dataset_columns = await conn.fetch(dataset_columns_query)

            # Get foreign key relationships from main table
            foreign_keys_query = f"""
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
                AND tc.table_name = '{main_table}'
                AND tc.table_schema = 'public'
            """
            foreign_keys = await conn.fetch(foreign_keys_query)

            # Get common metadata fields by analyzing actual data
            metadata_fields_query = f"""
                SELECT DISTINCT jsonb_object_keys(metadata) as metadata_key
                FROM {main_table}
                WHERE metadata IS NOT NULL
                AND metadata != 'null'::jsonb
                ORDER BY metadata_key
                LIMIT 50
            """
            metadata_keys = await conn.fetch(metadata_fields_query)

            # Get nested metadata fields (one level deep)
            nested_metadata_query = f"""
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
                        FROM {main_table}, jsonb_each(metadata)
                        WHERE metadata IS NOT NULL
                        AND metadata != 'null'::jsonb
                        AND jsonb_typeof(value) = 'object'
                    ) nested_objects
                ) nested_keys
                ORDER BY nested_key
                LIMIT 50
            """
            nested_metadata_keys = await conn.fetch(nested_metadata_query)

            # Build the dataset fields (excluding foreign keys and metadata)
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

    async def perform_search(
        self,
        count_query: str,
        search_query: str,
        params: list[Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        async with self.session() as conn:
            total_records = await conn.fetchval(count_query, *params) or 0

            # Then, get the paginated results for the current page
            paginated_query = (
                f"{search_query} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            )
            records = await conn.fetch(paginated_query, *params, limit, offset)

            # Convert records to dictionaries and parse JSON metadata
            items = []
            for record in records:
                item_dict = dict(record)

                # Parse metadata JSON string to object if it exists
                if "metadata" in item_dict and item_dict["metadata"]:
                    try:
                        item_dict["metadata"] = json.loads(item_dict["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        # If parsing fails, keep as string or set to empty dict
                        item_dict["metadata"] = {}
                else:
                    item_dict["metadata"] = {}

                items.append(item_dict)

            return {"total": total_records, "items": items}

    async def import_generic_data(
        self,
        navigation_entities: dict[str, list[dict[str, Any]]],
        main_entities: list[dict[str, Any]],
        main_table: str,
    ) -> bool:
        """
        Generic data import function that can work with any schema.

        Args:
            navigation_entities: Dict mapping table names to lists of entity dicts
            main_entities: List of main entity dicts
            main_table: Name of the main table

        Returns:
            True if import succeeded, False otherwise
        """
        try:
            async with self.session() as conn:
                # Use an explicit transaction for all operations
                async with conn.transaction():
                    # First, import navigation/lookup entities
                    navigation_id_map = {}

                    for table_name, entities in navigation_entities.items():
                        logger.info(
                            f"Importing {len(entities)} records into {table_name}"
                        )
                        navigation_id_map[table_name] = {}

                        for entity_data in entities:
                            if (
                                not isinstance(entity_data, dict)
                                or "name" not in entity_data
                            ):
                                continue

                            name = entity_data["name"]
                            try:
                                # Create or get existing entity
                                entity_id = await self._get_or_create_generic_entity(
                                    conn, table_name, entity_data
                                )
                                navigation_id_map[table_name][name] = entity_id
                            except Exception as e:
                                logger.error(
                                    f"Failed to import {name} into {table_name}: {e}"
                                )

                    # Then import main table entities
                    logger.info(
                        f"Importing {len(main_entities)} records into {main_table}"
                    )

                    processed_count = 0
                    failed_count = 0

                    for idx, entity_data in enumerate(main_entities):
                        try:
                            await self._import_main_entity_generic(
                                conn, main_table, entity_data, navigation_id_map
                            )
                            processed_count += 1
                        except Exception as e:
                            failed_count += 1
                            logger.error(
                                f"Failed to process {main_table} entity at index {idx}: {e}"
                            )

                    if failed_count > 0:
                        logger.warning(
                            f"Import completed with {failed_count} failures out of {processed_count + failed_count} total entities"
                        )
                    else:
                        logger.info(
                            f"Successfully processed all {processed_count} entities"
                        )

            logger.info("Generic data import completed")
            return failed_count == 0

        except Exception as e:
            logger.error(f"Generic data import failed: {e}")
            return False

    async def _get_or_create_generic_entity(
        self, conn: asyncpg.Connection, table_name: str, entity_data: dict[str, Any]
    ) -> int:
        """Get or create a generic entity and return its ID."""
        name = entity_data["name"]

        # Simple primary key mapping - this could be made more dynamic later
        primary_key_map = {
            "authors": "author_id",
            "genres": "genre_id",
            "publishers": "publisher_id",
            "libraries": "library_id",
            "collections": "collection_id",
            "series": "series_id",
            "books": "book_id",
        }

        primary_key = primary_key_map.get(table_name)
        if not primary_key:
            raise ValueError(f"No primary key mapping found for table {table_name}")

        # Check if entity exists
        check_query = f"SELECT {primary_key} FROM {table_name} WHERE name = $1"
        existing_record = await conn.fetchrow(check_query, name)

        if existing_record:
            return existing_record[primary_key]

        # Create new entity
        columns = []
        values = []
        placeholders = []

        for i, (key, value) in enumerate(entity_data.items(), 1):
            if key != primary_key:  # Skip primary key as it's auto-generated
                columns.append(key)
                values.append(value)
                placeholders.append(f"${i}")

        insert_query = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING {primary_key}
        """

        result = await conn.fetchrow(insert_query, *values)
        if result:
            return result[primary_key]

        raise RuntimeError(f"Failed to create entity in {table_name} with name {name}")

    async def _import_main_entity_generic(
        self,
        conn: asyncpg.Connection,
        main_table: str,
        entity_data: dict[str, Any],
        navigation_id_map: dict[str, dict[str, int]],
    ) -> None:
        """Import a main entity with navigation relationships."""
        name = entity_data.get("name")
        if not name:
            raise ValueError("Main entity must have a name")

        # Simple primary key mapping - this could be made more dynamic later
        primary_key_map = {
            "authors": "author_id",
            "genres": "genre_id",
            "publishers": "publisher_id",
            "libraries": "library_id",
            "collections": "collection_id",
            "series": "series_id",
            "books": "book_id",
        }

        primary_key = primary_key_map.get(main_table)
        if not primary_key:
            raise ValueError(f"No primary key mapping found for table {main_table}")

        # Prepare the data for insertion
        columns = []
        values = []
        placeholders = []

        # Process each field in entity_data
        for i, (key, value) in enumerate(entity_data.items(), 1):
            if key == primary_key:  # Skip auto-generated primary key
                continue

            # Check if this is a navigation reference (ends with _name)
            if key.endswith("_name") and value:
                # Convert name reference to ID reference
                table_prefix = key[:-5]  # Remove "_name" suffix

                # Find matching table in navigation_id_map
                matching_table = None
                for nav_table in navigation_id_map:
                    if nav_table.startswith(table_prefix) or table_prefix in nav_table:
                        matching_table = nav_table
                        break

                if matching_table and value in navigation_id_map[matching_table]:
                    # Add the ID column instead of the name column
                    id_column = f"{table_prefix}_id"
                    columns.append(id_column)
                    values.append(navigation_id_map[matching_table][value])
                    placeholders.append(f"${i}")
            else:
                # Handle regular fields
                if key == "metadata" and isinstance(value, dict):
                    # Convert metadata dict to JSON string
                    columns.append(key)
                    values.append(json.dumps(value))
                    placeholders.append(f"${i}")
                elif key not in ["metadata"] or not isinstance(value, dict):
                    # Regular field
                    columns.append(key)
                    values.append(value)
                    placeholders.append(f"${i}")

        # Insert or update the entity
        if columns:
            upsert_query = f"""
                INSERT INTO {main_table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (name) DO UPDATE SET
                {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'name'])},
                last_edited_at = (NOW() AT TIME ZONE 'utc')
            """

            await conn.execute(upsert_query, *values)

    async def get_dropdown_items(
        self,
        table_key: str,
        main_table: str,
        navigation_analysis: dict[str, Any],
        filter_dict: dict[str, str] = None,
    ) -> dict[str, Any]:
        """
        Get dropdown items for any navigation table based on schema discovery.
        Returns only items that have related datasets.
        """
        if filter_dict is None:
            filter_dict = {}

        async with self.session() as conn:
            if table_key not in navigation_analysis["navigation_tables"]:
                raise ValueError(f"Navigation table '{table_key}' not found")

            table_info = navigation_analysis["navigation_tables"][table_key]
            table_name = table_info["table_name"]
            primary_key = table_info["primary_key"]
            name_column = table_info["name_column"]

            # Build query that only returns items that have datasets
            query = f"""
                SELECT DISTINCT t.{primary_key} as id, t.{name_column} as name
                FROM {table_name} t
                INNER JOIN {main_table} d ON d.{table_key}_id = t.{primary_key}
            """

            params: list[Any] = []
            conditions: list[str] = []

            # Apply filters if provided
            if filter_dict:
                for filter_key, filter_value in filter_dict.items():
                    if filter_key.endswith("_name"):
                        # This is a filter by name, convert to ID
                        entity_key = filter_key.replace("_name", "")
                        if entity_key in navigation_analysis["navigation_tables"]:
                            filter_table_info = navigation_analysis[
                                "navigation_tables"
                            ][entity_key]
                            filter_table_name = filter_table_info["table_name"]
                            filter_name_column = filter_table_info["name_column"]
                            filter_pk = filter_table_info["primary_key"]

                            # Get the ID for this filter value
                            id_result = await conn.fetchval(
                                f"SELECT {filter_pk} FROM {filter_table_name} WHERE {filter_name_column} = $1",
                                filter_value,
                            )

                            if id_result:
                                # Add filter condition to the query
                                conditions.append(
                                    f"d.{entity_key}_id = ${len(params) + 1}"
                                )
                                params.append(id_result)
                    else:
                        # Direct filter by ID
                        if filter_key.endswith("_id"):
                            conditions.append(f"d.{filter_key} = ${len(params) + 1}")
                            params.append(filter_value)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY t.{name_column}"

            # Execute the query
            rows = await conn.fetch(query, *params)

            # Convert to the expected format
            items = [{"id": row["id"], "name": row["name"]} for row in rows]

            return {"data": items}

    async def search_datasets_generic(
        self,
        main_table: str,
        navigation_analysis: dict[str, Any],
        filters: dict[str, str] = None,
        search: str = "",
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Generic search endpoint that works with any database schema.
        Automatically handles joins based on schema discovery.
        """
        if filters is None:
            filters = {}

        async with self.session() as conn:
            # Build the base query
            query_parts = ["SELECT d.*"]

            # Add joins for navigation tables to get names
            join_parts = []
            for entity in navigation_analysis["navigation_entities"]:
                table_alias = entity["key"][0]  # Use first letter as alias
                referenced_table = entity["referenced_table"]
                column_name = entity["column_name"]
                name_column = navigation_analysis["navigation_tables"][entity["key"]][
                    "name_column"
                ]

                query_parts.append(
                    f", {table_alias}.{name_column} as {entity['key']}_name"
                )
                join_parts.append(
                    f"LEFT JOIN {referenced_table} {table_alias} ON d.{column_name} = {table_alias}.{navigation_analysis['navigation_tables'][entity['key']]['primary_key']}"
                )

            query_parts.append(f" FROM {main_table} d")
            query_parts.extend(join_parts)

            # Build WHERE conditions
            conditions: list[str] = []
            params: list[Any] = []

            # Add filter conditions
            for filter_key, filter_value in filters.items():
                if filter_key.endswith("_name"):
                    # Filter by navigation entity name
                    entity_key = filter_key.replace("_name", "")
                    if entity_key in navigation_analysis["navigation_tables"]:
                        table_alias = entity_key[0]
                        name_column = navigation_analysis["navigation_tables"][
                            entity_key
                        ]["name_column"]
                        conditions.append(
                            f"{table_alias}.{name_column} = ${len(params) + 1}"
                        )
                        params.append(filter_value)

            # Add search condition if provided
            if search:
                # Search in dataset name and description
                search_condition = "("
                search_conditions = []

                # Search in main table text fields
                for col in navigation_analysis["main_table_schema"]["columns"]:
                    if any(
                        text_type in col["data_type"].lower()
                        for text_type in ["text", "varchar", "character"]
                    ):
                        search_conditions.append(
                            f"d.{col['column_name']} ILIKE ${len(params) + 1}"
                        )

                if search_conditions:
                    search_condition += " OR ".join(search_conditions) + ")"
                    conditions.append(search_condition)
                    params.append(f"%{search}%")

            # Combine query parts
            query = "".join(query_parts)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            # Add ordering
            query += f" ORDER BY d.{navigation_analysis['main_table_schema']['primary_key']} DESC"

            # Count query for pagination
            count_query = query.replace(
                "SELECT d.*"
                + "".join(query_parts[1 : query_parts.index(f" FROM {main_table} d")]),
                "SELECT COUNT(*)",
            )

            # Execute count query
            total = await conn.fetchval(count_query, *params) or 0

            # Add pagination
            offset = (page - 1) * limit
            paginated_query = (
                f"{query} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            )

            # Execute main query
            rows = await conn.fetch(paginated_query, *params, limit, offset)

            # Convert to dictionaries
            items = [dict(row) for row in rows]

            return {"total": total, "items": items}
