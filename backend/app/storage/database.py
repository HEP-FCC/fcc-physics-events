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
import inflect
from asyncpg.pool import Pool
from pydantic import BaseModel

from app.fcc_dict_parser import DatasetCollection
from app.models.generic import GenericEntityCreate
from app.utils import Config, get_config, get_logger

# Constants
SCHEMA_ADVISORY_LOCK_ID = 1234567890

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
    _inflect_engine: inflect.engine | None = None

    def __init__(self):
        """Initialize the database with an inflect engine for dynamic primary key mapping."""
        self._inflect_engine = inflect.engine()

    def _get_dynamic_primary_key(self, table_name: str) -> str:
        """
        Dynamically determine primary key column name from table name.

        Uses inflect library to convert plural table names to singular form
        and appends '_id' to create the primary key column name.

        Args:
            table_name: The name of the database table

        Returns:
            The primary key column name in format "{singular_table}_id"

        Examples:
            "authors" -> "author_id"
            "companies" -> "company_id"
            "categories" -> "category_id"
            "product" -> "product_id" (already singular)
        """
        if not self._inflect_engine:
            self._inflect_engine = inflect.engine()

        # Convert plural to singular if needed
        singular_name = self._inflect_engine.singular_noun(table_name)
        if singular_name:
            # Table name was plural, use singular form
            base_name = singular_name
        else:
            # Table name was already singular
            base_name = table_name

        return f"{base_name}_id"

    async def setup(self, config: Config) -> None:
        """Creates the connection pool and initializes the database."""
        if self._pool:
            return
        try:
            logger.info("Setting up the database...")
            await self._create_connection_pool(config)
            await self._apply_database_schema(config)
            logger.info("Database setup successfully.")
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise

    async def _create_connection_pool(self, config: Config) -> None:
        """Creates the database connection pool."""
        connection_string = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
        self._pool = await asyncpg.create_pool(
            dsn=connection_string, min_size=5, max_size=20
        )
        logger.info("Database connection pool created successfully.")

    async def _apply_database_schema(self, config: Config) -> None:
        """Applies the database schema if not already applied."""
        logger.info("Applying database schema...")
        schema_file = config.get("schema_file", Path(__file__).parent / "database.sql")

        with open(schema_file, encoding="utf-8") as f:
            schema_sql = f.read()

        async with self.session() as conn:
            await self._apply_schema_with_lock(conn, schema_sql)

    async def _apply_schema_with_lock(
        self, conn: asyncpg.Connection, schema_sql: str
    ) -> None:
        """Applies schema using advisory lock to prevent concurrent application."""
        # Use advisory lock to prevent concurrent schema application from multiple workers
        await conn.execute("SELECT pg_advisory_lock($1)", SCHEMA_ADVISORY_LOCK_ID)
        try:
            schema_applied = await self._check_schema_applied(conn)

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
            await conn.execute("SELECT pg_advisory_unlock($1)", SCHEMA_ADVISORY_LOCK_ID)

    async def _check_schema_applied(self, conn: asyncpg.Connection) -> bool:
        """Check if our application schema has been applied by looking for our custom function."""
        return await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public'
                AND p.proname = 'jsonb_values_to_text'
            )
        """)

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

        try:
            config = get_config()
            main_table = config["application"]["main_table"]

            async with self.session() as conn:
                primary_key_column = await self._get_main_table_primary_key(
                    conn, main_table
                )
                base_mapping = self._create_base_mapping(primary_key_column)
                navigation_mapping = await self._create_navigation_mapping(
                    conn, main_table
                )

                # Combine both mappings
                return {**base_mapping, **navigation_mapping}

        except Exception as e:
            logger.error(f"Failed to generate dynamic schema mapping: {e}")
            # Return base mapping on failure
            return self._create_base_mapping("dataset_id")  # Fallback primary key

    def _create_base_mapping(self, primary_key_column: str) -> dict[str, str]:
        """Create base field mappings for common dataset fields."""
        return {
            "name": "d.name",
            "metadata": "d.metadata",
            "metadata_text": "jsonb_values_to_text(d.metadata)",
            primary_key_column: f"d.{primary_key_column}",
            "created_at": "d.created_at",
            "last_edited_at": "d.last_edited_at",
        }

    async def _create_navigation_mapping(
        self, conn: asyncpg.Connection, main_table: str
    ) -> dict[str, str]:
        """Create navigation entity mappings based on schema discovery."""
        try:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                main_table
            )

            return self._build_navigation_aliases(
                navigation_analysis["navigation_tables"]
            )

        except Exception as e:
            logger.warning(f"Failed to create navigation mapping: {e}")
            return {}

    def _build_navigation_aliases(
        self, navigation_tables: dict[str, Any]
    ) -> dict[str, str]:
        """Build alias mappings for navigation entities."""
        mapping = {}
        used_aliases = {"d"}  # 'd' is reserved for the main table

        for entity_key, table_info in navigation_tables.items():
            name_column = table_info["name_column"]
            alias = self._generate_unique_alias(entity_key, used_aliases)
            used_aliases.add(alias)
            mapping[entity_key] = f"{alias}.{name_column}"

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
        return str(result)

    async def _get_or_create_entity(
        self, conn: asyncpg.Connection, model: type[T], table_name: str, **kwargs: Any
    ) -> int:
        """Generic function to get an entity by name or create it within a transaction."""
        name = kwargs.get("name")
        if not name:
            raise ValueError("A 'name' is required to find or create an entity.")

        id_column = f"{table_name.rstrip('s')}_id"
        query = f"SELECT {id_column} FROM {table_name} WHERE name ILIKE $1"

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
        collection = self._parse_json_content(json_content)
        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            async with conn.transaction():
                processed_count, failed_count = await self._process_dataset_collection(
                    conn, collection, main_table
                )
                self._log_import_results(processed_count, failed_count)
                self._validate_import_success(processed_count, failed_count)

        logger.info("Import transaction completed successfully")

    def _parse_json_content(self, json_content: bytes) -> DatasetCollection:
        """Parse and validate JSON content into DatasetCollection."""
        try:
            raw_data = json.loads(json_content)
            return DatasetCollection.model_validate(raw_data)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON format") from e
        except Exception as e:
            raise ValueError(f"Invalid data format: {e}") from e

    async def _process_dataset_collection(
        self, conn: asyncpg.Connection, collection: DatasetCollection, main_table: str
    ) -> tuple[int, int]:
        """Process all datasets in the collection and return counts."""
        processed_count = 0
        failed_count = 0

        for idx, dataset_data in enumerate(collection.processes):
            try:
                await self._process_single_dataset(conn, dataset_data, idx, main_table)
                processed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process dataset at index {idx}: {e}")

        return processed_count, failed_count

    async def _process_single_dataset(
        self, conn: asyncpg.Connection, dataset_data: Any, idx: int, main_table: str
    ) -> None:
        """Process a single dataset with all its components."""
        dataset_name = self._generate_dataset_name(dataset_data, idx)
        logger.info(f"Processing: {dataset_name}")

        # Parse path and create navigation entities
        foreign_key_ids = await self._create_navigation_entities(
            conn, dataset_data, dataset_name
        )

        # Get metadata and create the main entity
        metadata_dict = dataset_data.get_all_metadata()
        await self._create_main_entity_with_conflict_resolution(
            conn, dataset_name, metadata_dict, foreign_key_ids, main_table
        )

    def _generate_dataset_name(self, dataset_data: Any, idx: int) -> str:
        """Generate dataset name with fallback if process_name is missing."""
        dataset_name = dataset_data.process_name
        if not dataset_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            dataset_name = f"unnamed_dataset_{timestamp}_{short_uuid}_{idx}"
            logger.warning(
                f"Dataset at index {idx} has no process_name. Using fallback name: {dataset_name}"
            )
        return dataset_name

    async def _create_navigation_entities(
        self, conn: asyncpg.Connection, dataset_data: Any, dataset_name: str
    ) -> dict[str, int | None]:
        """Create navigation entities from dataset path and return their IDs."""
        foreign_key_ids = {
            "accelerator_id": None,
            "stage_id": None,
            "campaign_id": None,
            "detector_id": None,
        }

        if not dataset_data.path:
            logger.warning(
                f"Dataset {dataset_name} has no path. Will store with null foreign key references."
            )
            return foreign_key_ids

        try:
            path_components = self._parse_path_components(dataset_data.path)
            foreign_key_ids = await self._create_entities_from_path_components(
                conn, path_components
            )
        except (IndexError, AttributeError) as e:
            logger.warning(
                f"Could not parse path components for {dataset_name}: {e}. "
                f"Will store dataset with null foreign key references."
            )

        return foreign_key_ids

    def _parse_path_components(self, path: str) -> dict[str, str | None]:
        """Parse path components and extract entity names."""
        path_parts = Path(path).parts
        return {
            "accelerator_name": path_parts[4] if len(path_parts) > 4 else None,
            "stage_name": (
                path_parts[6].replace("Events", "") if len(path_parts) > 6 else None
            ),
            "campaign_name": path_parts[7] if len(path_parts) > 7 else None,
            "detector_name": path_parts[8] if len(path_parts) > 8 else None,
        }

    async def _create_entities_from_path_components(
        self, conn: asyncpg.Connection, path_components: dict[str, str | None]
    ) -> dict[str, int | None]:
        """Create entities from parsed path components."""
        foreign_key_ids = {
            "accelerator_id": None,
            "stage_id": None,
            "campaign_id": None,
            "detector_id": None,
        }

        # Create accelerator first
        if (
            path_components["accelerator_name"]
            and path_components["accelerator_name"].strip()
        ):
            foreign_key_ids["accelerator_id"] = await self._get_or_create_entity(
                conn,
                GenericEntityCreate,
                "accelerators",
                name=path_components["accelerator_name"].strip(),
            )

        # Create stage
        if path_components["stage_name"] and path_components["stage_name"].strip():
            foreign_key_ids["stage_id"] = await self._get_or_create_entity(
                conn,
                GenericEntityCreate,
                "stages",
                name=path_components["stage_name"].strip(),
            )

        # Create campaign
        if (
            path_components["campaign_name"]
            and path_components["campaign_name"].strip()
        ):
            foreign_key_ids["campaign_id"] = await self._get_or_create_entity(
                conn,
                GenericEntityCreate,
                "campaigns",
                name=path_components["campaign_name"].strip(),
            )

        # Create detector (depends on accelerator)
        if (
            path_components["detector_name"]
            and path_components["detector_name"].strip()
            and foreign_key_ids["accelerator_id"]
        ):
            foreign_key_ids["detector_id"] = await self._get_or_create_entity(
                conn,
                GenericEntityCreate,
                "detectors",
                name=path_components["detector_name"].strip(),
                accelerator_id=foreign_key_ids["accelerator_id"],
            )

        return foreign_key_ids

    async def _create_main_entity_with_conflict_resolution(
        self,
        conn: asyncpg.Connection,
        dataset_name: str,
        metadata_dict: dict[str, Any],
        foreign_key_ids: dict[str, int | None],
        main_table: str,
    ) -> None:
        """Create main entity with conflict resolution for duplicate names."""
        final_name = dataset_name
        conflict_counter = 1

        while True:
            try:
                await self._create_main_entity(
                    conn, final_name, metadata_dict, foreign_key_ids, main_table
                )
                break  # Success, exit the retry loop
            except Exception as e:
                if "duplicate key value violates unique constraint" in str(e).lower():
                    final_name = f"{dataset_name}_conflict_{conflict_counter}"
                    conflict_counter += 1
                    logger.warning(
                        f"Name conflict for {dataset_name}, trying {final_name}"
                    )

                    if conflict_counter > 10:  # Prevent infinite loops
                        logger.error(
                            f"Too many name conflicts for {dataset_name}, skipping"
                        )
                        raise RuntimeError(
                            f"Too many name conflicts for {dataset_name}"
                        )
                else:
                    # Some other error, re-raise it
                    raise

    async def _create_main_entity(
        self,
        conn: asyncpg.Connection,
        name: str,
        metadata_dict: dict[str, Any],
        foreign_key_ids: dict[str, int | None],
        main_table: str,
    ) -> None:
        """Create the main entity in the database."""
        dataset_to_create = GenericEntityCreate(  # type: ignore[call-arg]
            name=name,
            metadata=metadata_dict,
            accelerator_id=foreign_key_ids["accelerator_id"],
            stage_id=foreign_key_ids["stage_id"],
            campaign_id=foreign_key_ids["campaign_id"],
            detector_id=foreign_key_ids["detector_id"],
        )

        entity_dict = dataset_to_create.model_dump(exclude_none=False)
        entity_dict = await self._merge_metadata_with_locked_fields(
            conn, entity_dict, main_table
        )

        # Build and execute the upsert query
        await self._execute_upsert_query(conn, entity_dict, main_table)

    async def _merge_metadata_with_locked_fields(
        self, conn: asyncpg.Connection, entity_dict: dict[str, Any], main_table: str
    ) -> dict[str, Any]:
        """Merge new metadata with existing locked fields."""
        if "metadata" not in entity_dict or entity_dict["metadata"] is None:
            return entity_dict

        new_metadata = entity_dict["metadata"]
        existing_metadata_result = await conn.fetchval(
            f"SELECT metadata FROM {main_table} WHERE name ILIKE $1",
            entity_dict["name"],
        )

        if existing_metadata_result:
            existing_metadata = self._parse_existing_metadata(existing_metadata_result)
            merged_metadata = self._merge_metadata_respecting_locks(
                existing_metadata, new_metadata
            )
            entity_dict["metadata"] = json.dumps(merged_metadata)
        else:
            # New entity, use new metadata as-is
            entity_dict["metadata"] = json.dumps(new_metadata)

        return entity_dict

    def _parse_existing_metadata(self, metadata_result: Any) -> dict[str, Any]:
        """Parse existing metadata from database result."""
        if isinstance(metadata_result, str):
            return json.loads(metadata_result)
        elif isinstance(metadata_result, dict):
            return metadata_result
        return {}

    def _merge_metadata_respecting_locks(
        self, existing_metadata: dict[str, Any], new_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge metadata while respecting locked fields."""
        merged_metadata = existing_metadata.copy()

        for key, value in new_metadata.items():
            # For lock field updates, allow them to pass through
            if key.startswith("__") and key.endswith("__lock__"):
                merged_metadata[key] = value
                continue

            # Check if this field is locked
            lock_field_name = f"__{key}__lock__"
            is_locked = existing_metadata.get(lock_field_name, False)

            if not is_locked:
                # Field is not locked, allow update
                merged_metadata[key] = value
            # If field is locked, keep the existing value

        return merged_metadata

    async def _execute_upsert_query(
        self, conn: asyncpg.Connection, entity_dict: dict[str, Any], main_table: str
    ) -> None:
        """Execute the upsert query for the main entity."""
        columns = list(entity_dict.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(entity_dict.values())

        # Build the conflict update clause for all columns except name
        update_clauses = []
        for col in columns:
            if col != "name":  # Don't update the conflict column
                update_clauses.append(f"{col} = EXCLUDED.{col}")
        update_clauses.append("last_edited_at = NOW()")

        query = f"""
            INSERT INTO {main_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (name) DO UPDATE
            SET {', '.join(update_clauses)}
        """

        await conn.execute(query, *values)

    def _log_import_results(self, processed_count: int, failed_count: int) -> None:
        """Log the results of the import operation."""
        if failed_count > 0:
            logger.warning(
                f"Import completed with {failed_count} failures out of {processed_count + failed_count} total datasets"
            )
        else:
            logger.info(f"Successfully processed all {processed_count} datasets")

    def _validate_import_success(self, processed_count: int, failed_count: int) -> None:
        """Validate that the import was successful enough to continue."""
        total_datasets = processed_count + failed_count
        if total_datasets > 0 and failed_count > (total_datasets / 2):
            raise RuntimeError(
                f"Import failed: {failed_count}/{total_datasets} datasets could not be processed"
            )

    async def _get_entity_id_by_name(
        self, conn: asyncpg.Connection, table_name: str, name: str
    ) -> int | None:
        """Helper function to get an entity ID by name."""
        id_column = f"{table_name.rstrip('s')}_id"
        query = f"SELECT {id_column} FROM {table_name} WHERE name ILIKE $1"

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
        self,
        entity_id: int,
        update_data: dict[str, Any],
        user_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Update an entity with the provided data using full replacement strategy.
        Returns the updated entity with all details.
        """
        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            primary_key_column = await self._get_main_table_primary_key(
                conn, main_table
            )

            async with conn.transaction():
                await self._validate_entity_exists(
                    conn, entity_id, primary_key_column, main_table
                )

                update_fields, values = await self._prepare_update_fields(
                    conn, update_data, main_table, primary_key_column, entity_id
                )

                await self._execute_update_query(
                    conn,
                    update_fields,
                    values,
                    entity_id,
                    primary_key_column,
                    main_table,
                )

                # Return the updated entity
                updated_entity = await self.get_entity_by_id(entity_id)
                if not updated_entity:
                    raise RuntimeError(f"Failed to retrieve updated entity {entity_id}")

                return updated_entity

    async def _validate_entity_exists(
        self,
        conn: asyncpg.Connection,
        entity_id: int,
        primary_key_column: str,
        main_table: str,
    ) -> None:
        """Validate that the entity exists before updating."""
        existing_check = await conn.fetchval(
            f"SELECT {primary_key_column} FROM {main_table} WHERE {primary_key_column} = $1",
            entity_id,
        )
        if not existing_check:
            raise ValueError(f"Entity with ID {entity_id} not found")

    async def _prepare_update_fields(
        self,
        conn: asyncpg.Connection,
        update_data: dict[str, Any],
        main_table: str,
        primary_key_column: str,
        entity_id: int,
    ) -> tuple[list[str], list[str | int]]:
        """Prepare update fields and values for the update query."""
        update_fields = ["last_edited_at = NOW()"]  # Always update last_edited_at
        values: list[str | int] = []
        param_count = 0

        valid_columns = await self._get_valid_table_columns(conn, main_table)

        for field_name, field_value in update_data.items():
            if self._should_skip_field(
                field_name, field_value, valid_columns, primary_key_column
            ):
                continue

            param_count += 1

            if field_name == "metadata" and isinstance(field_value, dict):
                processed_value = await self._process_metadata_field(
                    conn, field_value, entity_id, main_table, primary_key_column
                )
            else:
                processed_value = field_value

            update_fields.append(f"{field_name} = ${param_count}")
            values.append(processed_value)

        return update_fields, values

    async def _get_valid_table_columns(
        self, conn: asyncpg.Connection, main_table: str
    ) -> set[str]:
        """Get valid column names for the table."""
        table_columns_query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        table_columns = await conn.fetch(table_columns_query, main_table)
        return {row["column_name"] for row in table_columns}

    def _should_skip_field(
        self,
        field_name: str,
        field_value: Any,
        valid_columns: set[str],
        primary_key_column: str,
    ) -> bool:
        """Check if a field should be skipped during update."""
        # Skip fields that don't exist in the table
        if field_name not in valid_columns:
            return True

        # Skip primary key and auto-managed fields
        if field_name in [primary_key_column, "created_at", "last_edited_at"]:
            return True

        # Skip None values for non-nullable fields (except explicit null updates)
        if field_value is None and field_name == "name":
            return True

        return False

    async def _process_metadata_field(
        self,
        conn: asyncpg.Connection,
        field_value: dict[str, Any],
        entity_id: int,
        main_table: str,
        primary_key_column: str,
    ) -> str:
        """Process metadata field with locked field handling."""
        current_metadata = await self._get_current_metadata(
            conn, entity_id, main_table, primary_key_column
        )

        merged_metadata = self._merge_metadata_with_locks(current_metadata, field_value)

        self._log_metadata_processing(current_metadata, field_value, merged_metadata)

        return json.dumps(merged_metadata)

    async def _get_current_metadata(
        self,
        conn: asyncpg.Connection,
        entity_id: int,
        main_table: str,
        primary_key_column: str,
    ) -> dict[str, Any]:
        """Get current metadata from the database."""
        current_metadata_query = (
            f"SELECT metadata FROM {main_table} WHERE {primary_key_column} = $1"
        )
        current_metadata_result = await conn.fetchval(current_metadata_query, entity_id)

        if not current_metadata_result:
            return {}

        if isinstance(current_metadata_result, str):
            return json.loads(current_metadata_result)
        elif isinstance(current_metadata_result, dict):
            return current_metadata_result

        return {}

    def _merge_metadata_with_locks(
        self, current_metadata: dict[str, Any], new_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge new metadata with current metadata, respecting locked fields."""
        merged_metadata = current_metadata.copy()

        # First, preserve all existing lock fields
        self._preserve_existing_lock_fields(current_metadata, merged_metadata)

        # Process each field in the update data
        for key, value in new_metadata.items():
            if self._is_lock_field(key):
                self._handle_lock_field_update(key, value, merged_metadata)
            else:
                self._handle_regular_field_update(
                    key, value, current_metadata, merged_metadata
                )

        # Handle explicit unlock operations
        self._handle_explicit_unlocks(new_metadata, merged_metadata)

        return merged_metadata

    def _preserve_existing_lock_fields(
        self, current_metadata: dict[str, Any], merged_metadata: dict[str, Any]
    ) -> None:
        """Preserve all existing lock fields in merged metadata."""
        for existing_key, existing_value in current_metadata.items():
            if self._is_lock_field(existing_key):
                merged_metadata[existing_key] = existing_value
                logger.debug(
                    f"Preserving existing lock field: {existing_key} = {existing_value}"
                )

    def _is_lock_field(self, key: str) -> bool:
        """Check if a key represents a lock field."""
        return key.startswith("__") and key.endswith("__lock__")

    def _handle_lock_field_update(
        self, key: str, value: Any, merged_metadata: dict[str, Any]
    ) -> None:
        """Handle update of a lock field."""
        if value is None:
            # Remove the lock field
            merged_metadata.pop(key, None)
            logger.debug(f"Removing lock field: {key}")
        else:
            merged_metadata[key] = value
            logger.debug(f"Updating lock field: {key} = {value}")

    def _handle_regular_field_update(
        self,
        key: str,
        value: Any,
        current_metadata: dict[str, Any],
        merged_metadata: dict[str, Any],
    ) -> None:
        """Handle update of a regular (non-lock) field."""
        lock_field_name = f"__{key}__lock__"
        is_locked = current_metadata.get(lock_field_name, False)

        if not is_locked:
            # Field is not locked, allow update
            merged_metadata[key] = value
            logger.debug(f"Updating unlocked field: {key}")
        else:
            logger.debug(f"Skipping locked field: {key}")

    def _handle_explicit_unlocks(
        self, new_metadata: dict[str, Any], merged_metadata: dict[str, Any]
    ) -> None:
        """Handle explicit unlock operations."""
        for key, value in new_metadata.items():
            if self._is_lock_field(key) and value is None:
                # This was an explicit unlock operation
                merged_metadata.pop(key, None)
                logger.debug(f"Explicit unlock - removing field: {key}")

    def _log_metadata_processing(
        self,
        current_metadata: dict[str, Any],
        field_value: dict[str, Any],
        merged_metadata: dict[str, Any],
    ) -> None:
        """Log metadata processing information."""
        logger.info(
            f"Database update_entity - Current metadata keys: {list(current_metadata.keys())}"
        )
        logger.info(
            f"Database update_entity - Update data keys: {list(field_value.keys())}"
        )
        logger.info(
            f"Database update_entity - Current lock fields: {[k for k in current_metadata.keys() if '__lock__' in k]}"
        )
        logger.debug(f"Final merged metadata keys: {list(merged_metadata.keys())}")
        logger.info(
            f"Database update_entity - Final lock fields: {[k for k in merged_metadata.keys() if '__lock__' in k]}"
        )

    async def _execute_update_query(
        self,
        conn: asyncpg.Connection,
        update_fields: list[str],
        values: list[str | int],
        entity_id: int,
        primary_key_column: str,
        main_table: str,
    ) -> None:
        """Execute the update query."""
        if (
            not update_fields or len(update_fields) == 1
        ):  # Only last_edited_at was updated
            query = f"""
                UPDATE {main_table}
                SET last_edited_at = NOW()
                WHERE {primary_key_column} = $1
            """
            query_values = [entity_id]
        else:
            # Build the complete update query
            update_clause = ", ".join(update_fields)
            query = f"""
                UPDATE {main_table}
                SET {update_clause}
                WHERE {primary_key_column} = ${len(values) + 1}
            """
            query_values = values + [entity_id]

        try:
            await conn.execute(query, *query_values)
            logger.info(f"Successfully updated entity {entity_id}")
        except asyncpg.UniqueViolationError as e:
            if "name" in str(e):
                raise ValueError("An entity with the name already exists")
            raise ValueError(f"Update failed due to constraint violation: {e}")
        except asyncpg.ForeignKeyViolationError as e:
            raise ValueError(f"Update failed due to invalid reference: {e}")

    async def delete_entities_by_ids(self, entity_ids: list[int]) -> dict[str, Any]:
        """
        Delete entities by their IDs from the database.
        Returns a summary of the deletion operation.
        """
        if not entity_ids:
            return {
                "success": True,
                "deleted_count": 0,
                "not_found_count": 0,
                "message": "No entity IDs provided for deletion",
            }

        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            # Get the primary key column dynamically
            primary_key_column = await self._get_main_table_primary_key(
                conn, main_table
            )

            async with conn.transaction():
                # First, check which entities exist
                placeholders = ",".join(f"${i+1}" for i in range(len(entity_ids)))
                check_query = f"""
                    SELECT {primary_key_column}
                    FROM {main_table}
                    WHERE {primary_key_column} IN ({placeholders})
                """

                existing_entities = await conn.fetch(check_query, *entity_ids)
                existing_ids = {row[primary_key_column] for row in existing_entities}

                not_found_ids = set(entity_ids) - existing_ids
                not_found_count = len(not_found_ids)

                if not existing_ids:
                    return {
                        "success": True,
                        "deleted_count": 0,
                        "not_found_count": not_found_count,
                        "message": "No entities found with the provided IDs",
                        "not_found_ids": list(not_found_ids),
                    }

                # Delete the entities
                existing_ids_list = list(existing_ids)
                delete_placeholders = ",".join(
                    f"${i+1}" for i in range(len(existing_ids_list))
                )
                delete_query = f"""
                    DELETE FROM {main_table}
                    WHERE {primary_key_column} IN ({delete_placeholders})
                """

                try:
                    result = await conn.execute(delete_query, *existing_ids_list)
                    # Extract the count from the result (e.g., "DELETE 3")
                    deleted_count = (
                        int(result.split()[-1])
                        if result.split()[-1].isdigit()
                        else len(existing_ids_list)
                    )

                    logger.info(
                        f"Successfully deleted {deleted_count} entities: {existing_ids_list}"
                    )

                    return {
                        "success": True,
                        "deleted_count": deleted_count,
                        "not_found_count": not_found_count,
                        "message": f"Successfully deleted {deleted_count} entities",
                        "deleted_ids": existing_ids_list,
                        "not_found_ids": list(not_found_ids) if not_found_ids else None,
                    }

                except asyncpg.ForeignKeyViolationError as e:
                    logger.error(
                        f"Cannot delete entities due to foreign key constraints: {e}"
                    )
                    raise ValueError(
                        "Cannot delete entities as they are referenced by other records. "
                        "Please remove related records first."
                    )
                except Exception as e:
                    logger.error(f"Error deleting entities: {e}")
                    raise RuntimeError(f"Failed to delete entities: {str(e)}")

    async def get_sorting_fields(self) -> dict[str, Any]:
        """
        Dynamically fetch available sorting fields from the database schema.
        Returns categorized lists of sortable fields based on the current database structure.
        """
        config = get_config()
        main_table = config["application"]["main_table"]

        async with self.session() as conn:
            schema_data = await self._fetch_schema_data(conn, main_table)
            field_collections = self._build_field_collections(schema_data)
            all_fields = self._combine_and_sort_fields(field_collections)

        return {
            "fields": all_fields,
            "count": len(all_fields),
            "info": "All available fields for sorting. Metadata fields can be used with or without 'metadata.' prefix (e.g., 'status' or 'metadata.status').",
        }

    async def _fetch_schema_data(
        self, conn: asyncpg.Connection, main_table: str
    ) -> dict[str, Any]:
        """Fetch all schema-related data needed for sorting fields."""
        try:
            dataset_columns = await self._fetch_dataset_columns(conn, main_table)
            foreign_keys = await self._fetch_foreign_keys(conn, main_table)
            metadata_keys = await self._fetch_metadata_keys(conn, main_table)
            nested_metadata_keys = await self._fetch_nested_metadata_keys(
                conn, main_table
            )

            return {
                "dataset_columns": dataset_columns,
                "foreign_keys": foreign_keys,
                "metadata_keys": metadata_keys,
                "nested_metadata_keys": nested_metadata_keys,
            }
        except Exception as e:
            logger.error(f"Failed to execute schema discovery queries: {e}")
            raise

    async def _fetch_dataset_columns(
        self, conn: asyncpg.Connection, main_table: str
    ) -> list[dict]:
        """Fetch dataset column information."""
        return await conn.fetch(f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{main_table}'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

    async def _fetch_foreign_keys(
        self, conn: asyncpg.Connection, main_table: str
    ) -> list[dict]:
        """Fetch foreign key information."""
        return await conn.fetch(f"""
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
        """)

    async def _fetch_metadata_keys(
        self, conn: asyncpg.Connection, main_table: str
    ) -> list[dict]:
        """Fetch metadata field keys."""
        return await conn.fetch(f"""
            SELECT DISTINCT jsonb_object_keys(metadata) as metadata_key
            FROM {main_table}
            WHERE metadata IS NOT NULL
            AND metadata != 'null'::jsonb
            ORDER BY metadata_key
        """)

    async def _fetch_nested_metadata_keys(
        self, conn: asyncpg.Connection, main_table: str
    ) -> list[dict]:
        """Fetch nested metadata field keys."""
        return await conn.fetch(f"""
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
        """)

    def _build_field_collections(
        self, schema_data: dict[str, Any]
    ) -> dict[str, list[str]]:
        """Build different field collections from schema data."""
        dataset_fields = self._build_dataset_fields(
            schema_data["dataset_columns"], schema_data["foreign_keys"]
        )
        joined_fields = self._build_joined_fields(schema_data["foreign_keys"])
        metadata_fields = self._build_metadata_fields(schema_data["metadata_keys"])
        nested_fields = self._build_nested_fields(schema_data["nested_metadata_keys"])

        return {
            "dataset_fields": dataset_fields,
            "joined_fields": joined_fields,
            "metadata_fields": metadata_fields,
            "nested_fields": nested_fields,
        }

    def _build_dataset_fields(
        self, dataset_columns: list[dict], foreign_keys: list[dict]
    ) -> list[str]:
        """Build dataset fields excluding foreign keys and metadata."""
        foreign_key_columns = {fk["column_name"] for fk in foreign_keys}
        dataset_fields = []

        for col in dataset_columns:
            col_name = col["column_name"]
            if col_name not in foreign_key_columns and col_name != "metadata":
                dataset_fields.append(col_name)

        return dataset_fields

    def _build_joined_fields(self, foreign_keys: list[dict]) -> list[str]:
        """Build joined fields from foreign key relationships."""
        joined_fields = []
        for fk in foreign_keys:
            fk_column = fk["column_name"]
            # Convert foreign key column name to corresponding joined field name
            # e.g., accelerator_id -> accelerator_name
            if fk_column.endswith("_id"):
                base_name = fk_column[:-3]  # Remove '_id' suffix
                joined_field_name = f"{base_name}_name"
                joined_fields.append(joined_field_name)

        return joined_fields

    def _build_metadata_fields(self, metadata_keys: list[dict]) -> list[str]:
        """Build metadata fields list."""
        return [row["metadata_key"] for row in metadata_keys]

    def _build_nested_fields(self, nested_metadata_keys: list[dict]) -> list[str]:
        """Build nested metadata fields list."""
        return [row["nested_key"] for row in nested_metadata_keys]

    def _combine_and_sort_fields(
        self, field_collections: dict[str, list[str]]
    ) -> list[str]:
        """Combine all field collections and sort alphabetically."""
        all_fields = []
        all_fields.extend(field_collections["dataset_fields"])
        all_fields.extend(field_collections["joined_fields"])
        all_fields.extend(field_collections["metadata_fields"])
        all_fields.extend(field_collections["nested_fields"])

        # Sort alphabetically for better UX
        all_fields.sort()
        return all_fields

    async def perform_search(
        self,
        count_query: str,
        search_query: str,
        params: list[Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        async with self.session() as conn:
            # Execute count and records queries sequentially to avoid connection conflicts
            # The performance difference is minimal for these quick queries
            try:
                # Get total count first
                total_records_result = await conn.fetchval(count_query, *params)
                total_records = total_records_result or 0

                # Then get the records
                records = await conn.fetch(
                    f"{search_query} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}",
                    *params,
                    limit,
                    offset,
                )

            except Exception as e:
                logger.error(f"Failed to execute search queries: {e}")
                raise

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
                    navigation_id_map: dict[str, dict[str, int]] = {}

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

        # Use dynamic primary key mapping instead of hardcoded dictionary
        primary_key = self._get_dynamic_primary_key(table_name)

        # Check if entity exists
        check_query = f"SELECT {primary_key} FROM {table_name} WHERE name ILIKE $1"
        existing_record: dict[str, int] = await conn.fetchrow(check_query, name)

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

        result: dict[str, int] = await conn.fetchrow(insert_query, *values)
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

        primary_key = self._get_primary_key_for_table(main_table)
        columns, values, placeholders = self._prepare_entity_data(
            entity_data, primary_key, navigation_id_map
        )

        if columns:
            upsert_query = self._build_upsert_query(main_table, columns, placeholders)
            await conn.execute(upsert_query, *values)

    def _get_primary_key_for_table(self, table_name: str) -> str:
        """Get the primary key column name for a table using dynamic mapping."""
        return self._get_dynamic_primary_key(table_name)

    def _prepare_entity_data(
        self,
        entity_data: dict[str, Any],
        primary_key: str,
        navigation_id_map: dict[str, dict[str, int]],
    ) -> tuple[list[str], list[str | int], list[str]]:
        """Prepare entity data for insertion, handling navigation references and metadata."""
        columns = []
        values: list[str | int] = []
        placeholders = []

        for i, (key, value) in enumerate(entity_data.items(), 1):
            if key == primary_key:  # Skip auto-generated primary key
                continue

            processed_column, processed_value = self._process_entity_field(
                key, value, navigation_id_map
            )

            if processed_column and processed_value is not None:
                columns.append(processed_column)
                values.append(processed_value)
                placeholders.append(f"${i}")

        return columns, values, placeholders

    def _process_entity_field(
        self, key: str, value: Any, navigation_id_map: dict[str, dict[str, int]]
    ) -> tuple[str | None, str | int | None]:
        """Process a single entity field, handling navigation references and metadata."""
        # Check if this is a navigation reference (ends with _name)
        if key.endswith("_name") and value:
            return self._process_navigation_reference(key, value, navigation_id_map)

        # Handle metadata fields
        if key == "metadata" and isinstance(value, dict):
            return key, json.dumps(value)

        # Handle regular fields (excluding metadata dict that wasn't properly handled)
        if key != "metadata" or not isinstance(value, dict):
            return key, value

        return None, None

    def _process_navigation_reference(
        self, key: str, value: str, navigation_id_map: dict[str, dict[str, int]]
    ) -> tuple[str | None, int | None]:
        """Process a navigation reference field, converting name to ID."""
        table_prefix = key[:-5]  # Remove "_name" suffix

        # Find matching table in navigation_id_map
        matching_table = None
        for nav_table in navigation_id_map:
            if nav_table.startswith(table_prefix) or table_prefix in nav_table:
                matching_table = nav_table
                break

        if matching_table and value in navigation_id_map[matching_table]:
            id_column = f"{table_prefix}_id"
            return id_column, navigation_id_map[matching_table][value]

        return None, None

    def _build_upsert_query(
        self, main_table: str, columns: list[str], placeholders: list[str]
    ) -> str:
        """Build an upsert query for the main entity."""
        update_columns = [col for col in columns if col != "name"]
        update_clauses = [f"{col} = EXCLUDED.{col}" for col in update_columns]
        update_clauses.append("last_edited_at = NOW()")

        return f"""
            INSERT INTO {main_table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            ON CONFLICT (name) DO UPDATE SET
            {', '.join(update_clauses)}
        """

    async def get_dropdown_items(
        self,
        table_key: str,
        main_table: str,
        navigation_analysis: dict[str, Any],
        filter_dict: dict[str, str] | None = None,
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
            base_query = self._build_dropdown_base_query(
                table_info, table_key, main_table
            )

            conditions, params = await self._process_dropdown_filters(
                conn, filter_dict, navigation_analysis
            )

            final_query = self._finalize_dropdown_query(
                base_query, conditions, table_info["name_column"]
            )
            rows = await conn.fetch(final_query, *params)

            items = [{"id": row["id"], "name": row["name"]} for row in rows]
            return {"data": items}

    def _build_dropdown_base_query(
        self, table_info: dict[str, Any], table_key: str, main_table: str
    ) -> str:
        """Build the base query for dropdown items."""
        table_name = table_info["table_name"]
        primary_key = table_info["primary_key"]
        name_column = table_info["name_column"]

        return f"""
            SELECT DISTINCT t.{primary_key} as id, t.{name_column} as name
            FROM {table_name} t
            INNER JOIN {main_table} d ON d.{table_key}_id = t.{primary_key}
        """

    async def _process_dropdown_filters(
        self,
        conn: asyncpg.Connection,
        filter_dict: dict[str, str],
        navigation_analysis: dict[str, Any],
    ) -> tuple[list[str], list[Any]]:
        """Process filter conditions for dropdown queries."""
        conditions: list[str] = []
        params: list[Any] = []

        for filter_key, filter_value in filter_dict.items():
            if filter_key.endswith("_name"):
                condition, param = await self._process_name_filter(
                    conn, filter_key, filter_value, navigation_analysis
                )
                if condition and param is not None:
                    conditions.append(
                        condition.replace("$PARAM", f"${len(params) + 1}")
                    )
                    params.append(param)
            elif filter_key.endswith("_id"):
                conditions.append(f"d.{filter_key} = ${len(params) + 1}")
                params.append(filter_value)

        return conditions, params

    async def _process_name_filter(
        self,
        conn: asyncpg.Connection,
        filter_key: str,
        filter_value: str,
        navigation_analysis: dict[str, Any],
    ) -> tuple[str | None, int | None]:
        """Process a name-based filter, converting it to an ID filter."""
        entity_key = filter_key.replace("_name", "")

        if entity_key not in navigation_analysis["navigation_tables"]:
            return None, None

        filter_table_info = navigation_analysis["navigation_tables"][entity_key]
        filter_table_name = filter_table_info["table_name"]
        filter_name_column = filter_table_info["name_column"]
        filter_pk = filter_table_info["primary_key"]

        # Get the ID for this filter value (case-insensitive)
        id_result = await conn.fetchval(
            f"SELECT {filter_pk} FROM {filter_table_name} WHERE {filter_name_column} ILIKE $1",
            filter_value,
        )

        if id_result:
            return f"d.{entity_key}_id = $PARAM", id_result

        return None, None

    def _finalize_dropdown_query(
        self, base_query: str, conditions: list[str], name_column: str
    ) -> str:
        """Add WHERE clause and ORDER BY to the dropdown query."""
        query = base_query

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY t.{name_column}"
        return query

    async def search_datasets_generic(
        self,
        main_table: str,
        navigation_analysis: dict[str, Any],
        filters: dict[str, str] | None = None,
        search: str = "",
        page: int = 1,
        limit: int = 25,
    ) -> dict[str, Any]:
        """
        Generic search endpoint that works with any database schema.
        Automatically handles joins based on schema discovery.
        """
        if filters is None:
            filters = {}

        async with self.session() as conn:
            query_parts, join_parts = self._build_search_query_parts(
                main_table, navigation_analysis
            )
            conditions, params = self._build_search_conditions(
                navigation_analysis, filters, search
            )

            base_query = self._assemble_base_query(
                query_parts,
                join_parts,
                conditions,
                navigation_analysis["main_table_schema"]["primary_key"],
            )
            count_query = self._build_count_query(base_query, query_parts, main_table)

            # Execute queries and return results
            total = await conn.fetchval(count_query, *params) or 0

            offset = (page - 1) * limit
            paginated_query = (
                f"{base_query} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
            )
            rows = await conn.fetch(paginated_query, *params, limit, offset)

            items = [dict(row) for row in rows]
            return {"total": total, "items": items}

    def _build_search_query_parts(
        self, main_table: str, navigation_analysis: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Build the SELECT and JOIN parts of the search query."""
        query_parts = ["SELECT d.*"]
        join_parts = []

        for entity in navigation_analysis["navigation_entities"]:
            table_alias = entity["key"][0]  # Use first letter as alias
            referenced_table = entity["referenced_table"]
            column_name = entity["column_name"]
            name_column = navigation_analysis["navigation_tables"][entity["key"]][
                "name_column"
            ]
            primary_key = navigation_analysis["navigation_tables"][entity["key"]][
                "primary_key"
            ]

            query_parts.append(f", {table_alias}.{name_column} as {entity['key']}_name")
            join_parts.append(
                f"LEFT JOIN {referenced_table} {table_alias} ON d.{column_name} = {table_alias}.{primary_key}"
            )

        query_parts.append(f" FROM {main_table} d")

        return query_parts, join_parts

    def _build_search_conditions(
        self, navigation_analysis: dict[str, Any], filters: dict[str, str], search: str
    ) -> tuple[list[str], list[Any]]:
        """Build WHERE conditions and parameters for the search query."""
        conditions: list[str] = []
        params: list[Any] = []

        # Add filter conditions
        self._add_filter_conditions(navigation_analysis, filters, conditions, params)

        # Add search conditions
        if search:
            self._add_search_conditions(navigation_analysis, search, conditions, params)

        return conditions, params

    def _add_filter_conditions(
        self,
        navigation_analysis: dict[str, Any],
        filters: dict[str, str],
        conditions: list[str],
        params: list[Any],
    ) -> None:
        """Add filter conditions to the query."""
        for filter_key, filter_value in filters.items():
            if filter_key.endswith("_name"):
                entity_key = filter_key.replace("_name", "")
                if entity_key in navigation_analysis["navigation_tables"]:
                    table_alias = entity_key[0]
                    name_column = navigation_analysis["navigation_tables"][entity_key][
                        "name_column"
                    ]
                    conditions.append(
                        f"{table_alias}.{name_column} = ${len(params) + 1}"
                    )
                    params.append(filter_value)

    def _add_search_conditions(
        self,
        navigation_analysis: dict[str, Any],
        search: str,
        conditions: list[str],
        params: list[Any],
    ) -> None:
        """Add text search conditions to the query."""
        search_conditions = []

        for col in navigation_analysis["main_table_schema"]["columns"]:
            if any(
                text_type in col["data_type"].lower()
                for text_type in ["text", "varchar", "character"]
            ):
                search_conditions.append(
                    f"d.{col['column_name']} ILIKE ${len(params) + 1}"
                )

        if search_conditions:
            search_condition = "(" + " OR ".join(search_conditions) + ")"
            conditions.append(search_condition)
            params.append(f"%{search}%")

    def _assemble_base_query(
        self,
        query_parts: list[str],
        join_parts: list[str],
        conditions: list[str],
        primary_key: str,
    ) -> str:
        """Assemble the complete base query with WHERE and ORDER BY clauses."""
        query = "".join(query_parts)
        query += "".join(join_parts)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY d.{primary_key} DESC"
        return query

    def _build_count_query(
        self, base_query: str, query_parts: list[str], main_table: str
    ) -> str:
        """Build the count query from the base query."""
        # Find the part to replace for count query
        select_part = "SELECT d.*" + "".join(
            query_parts[1 : query_parts.index(f" FROM {main_table} d")]
        )
        return base_query.replace(select_part, "SELECT COUNT(*)")
