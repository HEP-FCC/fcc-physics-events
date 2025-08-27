"""
Data import functionality for the Database class.

This module handles JSON data import operations with entity processing,
navigation entity creation, and metadata management.
"""

import json
import uuid
from datetime import datetime
from typing import Any

import asyncpg

from app.models.generic import GenericEntityCreate
from app.storage.fcc_dict_parser import DatasetCollection
from app.storage.schema_discovery import get_schema_discovery
from app.utils.logging import get_logger
from app.utils.uuid_utils import generate_dataset_uuid

logger = get_logger()


async def import_data(database, json_content: bytes) -> None:
    """Parses JSON content and upserts the data into the database with proper transaction handling."""
    try:
        # NOTE: This function needs to be defined by users
        collection = _parse_json_content(json_content)
    except ValueError as e:
        # If the file format is incompatible, log and skip without raising an error
        if "skipping incompatible format" in str(e):
            logger.info(f"Skipping incompatible JSON format: {e}")
            return
        else:
            # Re-raise other validation errors
            raise

    main_table = database.config["application"]["main_table"]

    # NOTE: This function needs to be defined by users
    # Process each dataset in its own transaction to avoid transaction abort issues
    (
        processed_count,
        failed_count,
    ) = await _process_entity_collection_with_recovery(database, collection, main_table)

    _log_import_results(processed_count, failed_count)
    _validate_import_success(processed_count, failed_count)

    logger.info("Import operation completed successfully")


# Helper functions for data import


def _parse_json_content(json_content: bytes) -> DatasetCollection:
    """Parse and validate JSON content into DatasetCollection."""
    try:
        raw_data = json.loads(json_content)

        # Check if this JSON has the expected "processes" key with a list value
        if not isinstance(raw_data, dict):
            raise ValueError("JSON root must be an object")

        if "processes" not in raw_data:
            raise ValueError(
                "JSON does not contain 'processes' key - skipping incompatible format"
            )

        if not isinstance(raw_data["processes"], list):
            raise ValueError(
                "'processes' value must be a list - skipping incompatible format"
            )

        return DatasetCollection.model_validate(raw_data)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format") from e
    except Exception as e:
        raise ValueError(f"Invalid data format: {e}") from e


async def _process_entity_collection_with_recovery(
    database, collection: DatasetCollection, main_table: str
) -> tuple[int, int]:
    """Process all entity in the collection using batch transactions with fallback."""
    batch_size = database.config["application"]["batch_size"]

    total_processed = 0
    total_failed = 0

    # Split datasets into batches
    datasets = list(collection.processes)

    for batch_start in range(0, len(datasets), batch_size):
        batch_end = min(batch_start + batch_size, len(datasets))
        batch = datasets[batch_start:batch_end]
        batch_indices = list(range(batch_start, batch_end))

        logger.info(
            f"Processing batch {batch_start//batch_size + 1}: datasets {batch_start+1}-{batch_end} of {len(datasets)}"
        )

        # Try batch processing first (all-or-nothing)
        batch_processed, batch_failed = await _process_batch_all_or_nothing(
            database, batch, batch_indices, main_table
        )

        # If batch failed, fall back to individual processing
        if batch_failed > 0 and batch_processed == 0:
            logger.warning(
                f"Batch failed, falling back to individual processing for batch {batch_start//batch_size + 1}"
            )
            batch_processed, batch_failed = await _process_batch_individually(
                database, batch, batch_indices, main_table
            )

        total_processed += batch_processed
        total_failed += batch_failed

        logger.info(
            f"Batch {batch_start//batch_size + 1} completed: {batch_processed} processed, {batch_failed} failed"
        )

    return total_processed, total_failed


async def _process_batch_all_or_nothing(
    database, batch: list, batch_indices: list[int], main_table: str
) -> tuple[int, int]:
    """Process a batch of datasets in a single transaction (all-or-nothing)."""
    try:
        async with database.session() as conn:
            async with conn.transaction():
                # Pre-populate navigation entities for the entire batch
                navigation_cache = await _preprocess_batch_navigation_entities(
                    database, conn, batch
                )

                # Process all datasets in the batch
                for idx, dataset_data in zip(batch_indices, batch, strict=True):
                    await _process_single_entity(
                        database, conn, dataset_data, idx, main_table, navigation_cache
                    )

                # If we get here, all datasets succeeded
                return len(batch), 0

    except Exception as e:
        logger.error(f"Batch transaction failed: {e}")
        # Return 0 processed, all failed - will trigger individual fallback
        return 0, len(batch)


async def _process_batch_individually(
    database, batch: list, batch_indices: list[int], main_table: str
) -> tuple[int, int]:
    """Process batch datasets individually (fallback when batch fails)."""
    processed_count = 0
    failed_count = 0

    for idx, dataset_data in zip(batch_indices, batch, strict=True):
        # Process each dataset in its own session and transaction
        try:
            async with database.session() as conn:
                async with conn.transaction():
                    await _process_single_dataset(
                        database, conn, dataset_data, idx, main_table
                    )
                    processed_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to process dataset at index {idx}: {e}")
            # Continue processing other datasets instead of aborting

    return processed_count, failed_count


async def _preprocess_batch_navigation_entities(
    database, conn: asyncpg.Connection, batch: list
) -> dict[str, dict[str, int]]:
    """Pre-populate all navigation entities for a batch and return ID cache."""
    # Get dynamic navigation structure from config and schema
    entity_structure = await _get_navigation_entity_structure(database, conn)

    if not entity_structure:
        return {}

    # Collect all unique navigation entity names from the batch
    unique_entities = {}

    for dataset_data in batch:
        for entity_key, entity_info in entity_structure.items():
            field_name = entity_info["field_name"]

            # Get entity name from direct JSON field
            entity_name = None
            if hasattr(dataset_data, field_name):
                field_value = getattr(dataset_data, field_name)
                if field_value and str(field_value).strip():
                    entity_name = str(field_value).strip()

            if entity_name:
                if entity_key not in unique_entities:
                    unique_entities[entity_key] = set()
                unique_entities[entity_key].add(entity_name)

    # Create all navigation entities and build cache
    navigation_cache = {}

    for entity_key, names in unique_entities.items():
        entity_info = entity_structure[entity_key]
        table_name = entity_info["table_name"]
        navigation_cache[entity_key] = {}

        for name in names:
            # Create the entity and cache its ID
            entity_id = await _get_or_create_entity(
                conn,
                GenericEntityCreate,
                table_name,
                name=name,
            )
            navigation_cache[entity_key][name] = entity_id

    return navigation_cache


async def _process_single_entity(
    database,
    conn: asyncpg.Connection,
    dataset_data: Any,
    idx: int,
    main_table: str,
    navigation_cache: dict[str, dict[str, int]],
) -> None:
    """Process a single dataset using pre-populated navigation entity cache."""
    dataset_name = _generate_dataset_name(dataset_data, idx)
    logger.info(f"Processing: {dataset_name}")

    # Get foreign key IDs from cache instead of creating individually
    foreign_key_ids = await _get_foreign_key_ids_from_cache(
        dataset_data, navigation_cache
    )

    # Get metadata and create the main entity
    metadata_dict = dataset_data.get_all_metadata()
    await _create_main_entity_with_conflict_resolution(
        database, conn, dataset_name, metadata_dict, foreign_key_ids, main_table
    )


async def _get_foreign_key_ids_from_cache(
    dataset_data: Any,
    navigation_cache: dict[str, dict[str, int]],
) -> dict[str, int | None]:
    # TODO: what is this function? can it be removed or made more generic?
    """Get foreign key IDs from the navigation cache."""
    # For now, let's build the foreign_key_ids based on what we know
    # This is a simplified version that works with the cache structure
    foreign_key_ids = {}

    # Map entity keys to their foreign key column names
    entity_key_mappings = {
        "accelerator": "accelerator_id",
        "stage": "stage_id",
        "campaign": "campaign_id",
        "detector": "detector_id",
        "file_type": "file_type_id",
    }

    for entity_key, foreign_key_col in entity_key_mappings.items():
        if entity_key in navigation_cache:
            # Try to find the entity name for this dataset
            entity_name = _get_entity_name_for_dataset(dataset_data, entity_key)

            if entity_name and entity_name in navigation_cache[entity_key]:
                foreign_key_ids[foreign_key_col] = navigation_cache[entity_key][
                    entity_name
                ]
            else:
                foreign_key_ids[foreign_key_col] = None
        else:
            foreign_key_ids[foreign_key_col] = None

    return foreign_key_ids


def _get_entity_name_for_dataset(dataset_data: Any, field_name: str) -> str | None:
    """Get the entity name for a specific entity key from dataset data."""
    if not field_name:
        return None

    # Get entity name from direct JSON field
    entity_name = None
    if hasattr(dataset_data, field_name):
        field_value = getattr(dataset_data, field_name)
        if field_value and str(field_value).strip():
            entity_name = str(field_value).strip()

    return entity_name


async def _process_single_dataset(
    database, conn: asyncpg.Connection, dataset_data: Any, idx: int, main_table: str
) -> None:
    """Process a single dataset with all its components."""
    dataset_name = _generate_dataset_name(dataset_data, idx)
    logger.info(f"Processing: {dataset_name}")

    # Parse path and create navigation entities
    foreign_key_ids = await _create_navigation_entities(
        database, conn, dataset_data, dataset_name
    )

    # Get metadata and create the main entity
    # TODO: get_all_metadata is a required function
    metadata_dict = dataset_data.get_all_metadata()
    await _create_main_entity_with_conflict_resolution(
        database, conn, dataset_name, metadata_dict, foreign_key_ids, main_table
    )


def _generate_dataset_name(dataset_data: Any, idx: int) -> str:
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


async def _get_navigation_entity_structure(
    database, conn: asyncpg.Connection
) -> dict[str, dict[str, str]]:
    """Get dynamic navigation entity structure from config and schema."""
    try:
        main_table = database.config["application"]["main_table"]
        navigation_order = database.config["navigation"]["order"]

        # Use schema discovery to get the actual table mappings
        schema_discovery = await get_schema_discovery(conn)
        navigation_analysis = await schema_discovery.analyze_navigation_structure(
            main_table
        )

        # Build entity structure mapping: entity_key -> {table_name, field_name}
        entity_structure = {}
        for entity_key in navigation_order:
            # Default to conventional plural table name
            table_name = f"{entity_key}s"

            # Try to find actual table name from schema analysis
            if entity_key in navigation_analysis["navigation_tables"]:
                table_name = navigation_analysis["navigation_tables"][entity_key][
                    "table_name"
                ]

            # Field name matches the entity key (e.g., "accelerator", "file_type")
            field_name = entity_key

            entity_structure[entity_key] = {
                "table_name": table_name,
                "field_name": field_name,
                "foreign_key_column": f"{entity_key}_id",
            }

        return entity_structure

    except Exception as e:
        logger.error(f"Failed to get dynamic navigation structure: {e}")
        try:
            navigation_order = database.config["navigation"]["order"]

            # Build minimal structure from config only
            entity_structure = {}
            for entity_key in navigation_order:
                # Use conventional naming patterns
                table_name = f"{entity_key}s"
                field_name = entity_key

                entity_structure[entity_key] = {
                    "table_name": table_name,
                    "field_name": field_name,
                    "foreign_key_column": f"{entity_key}_id",
                }

            logger.info(
                f"Using config-only navigation structure with {len(entity_structure)} entities"
            )
            return entity_structure

        except Exception as config_error:
            logger.error(
                f"Failed to build navigation structure from config: {config_error}"
            )
            # If even config fails, return empty structure - let the calling code handle gracefully
            return {}


async def _create_navigation_entities(
    database, conn: asyncpg.Connection, dataset_data: Any, dataset_name: str
) -> dict[str, int | None]:
    """Create navigation entities dynamically from direct JSON fields and return their IDs."""
    # Get dynamic navigation structure from config and schema
    entity_structure = await _get_navigation_entity_structure(database, conn)

    # Initialize foreign_key_ids dictionary dynamically
    foreign_key_ids: dict[str, int | None] = {
        entity_info["foreign_key_column"]: None
        for entity_info in entity_structure.values()
    }

    # If no entity structure could be determined, return empty foreign keys
    if not entity_structure:
        logger.warning(
            f"No navigation entity structure available for {dataset_name}. Skipping navigation entity creation."
        )
        return foreign_key_ids

    # Create entities dynamically based on the discovered structure
    try:
        for entity_key, entity_info in entity_structure.items():
            field_name = entity_info["field_name"]
            table_name = entity_info["table_name"]
            foreign_key_column = entity_info["foreign_key_column"]

            # Get entity name from direct JSON field
            entity_name = None
            if hasattr(dataset_data, field_name):
                field_value = getattr(dataset_data, field_name)
                if field_value and str(field_value).strip():
                    entity_name = str(field_value).strip()

            # Create the entity if we have a name
            if entity_name:
                # Special handling for detector which needs accelerator_id
                if entity_key == "detector" and foreign_key_ids.get("accelerator_id"):
                    foreign_key_ids[foreign_key_column] = await _get_or_create_entity(
                        conn,
                        GenericEntityCreate,
                        table_name,
                        name=entity_name,
                        accelerator_id=foreign_key_ids["accelerator_id"],
                    )
                else:
                    foreign_key_ids[foreign_key_column] = await _get_or_create_entity(
                        conn,
                        GenericEntityCreate,
                        table_name,
                        name=entity_name,
                    )

    except Exception as e:
        logger.warning(
            f"Could not create navigation entities for {dataset_name}: {e}. "
            f"Will store dataset with null foreign key references."
        )

    return foreign_key_ids


async def _create_main_entity_with_conflict_resolution(
    database,
    conn: asyncpg.Connection,
    dataset_name: str,
    metadata_dict: dict[str, Any],
    foreign_key_ids: dict[str, int | None],
    main_table: str,
) -> None:
    """Create main entity using UUID-based conflict resolution."""
    try:
        await _create_main_entity(
            database, conn, dataset_name, metadata_dict, foreign_key_ids, main_table
        )
    except Exception as e:
        # Log any errors but don't do name-based retries since UUID handles uniqueness
        logger.error(f"Failed to create/update entity for {dataset_name}: {e}")
        raise


async def _create_main_entity(
    database,
    conn: asyncpg.Connection,
    name: str,
    metadata_dict: dict[str, Any],
    foreign_key_ids: dict[str, int | None],
    main_table: str,
) -> None:
    """Create the main entity in the database."""
    # Generate deterministic UUID based on key fields
    dataset_uuid = generate_dataset_uuid(
        dataset_name=name,
        **foreign_key_ids,
    )

    # Create entity dictionary dynamically
    entity_dict = {
        "name": name,
        "metadata": metadata_dict,
    }

    # Add all foreign key IDs dynamically
    entity_dict.update(foreign_key_ids)
    # Add the UUID to the entity dictionary
    entity_dict["uuid"] = dataset_uuid

    entity_dict = await _merge_metadata_with_locked_fields(
        conn, entity_dict, main_table
    )

    # Build and execute the upsert query
    await _upsert_entity(conn, entity_dict, main_table)


async def _merge_metadata_with_locked_fields(
    conn: asyncpg.Connection, entity_dict: dict[str, Any], main_table: str
) -> dict[str, Any]:
    """Merge new metadata with existing locked fields."""
    if "metadata" not in entity_dict or entity_dict["metadata"] is None:
        return entity_dict

    new_metadata = entity_dict["metadata"]
    existing_metadata_result = await conn.fetchval(
        f"SELECT metadata FROM {main_table} WHERE uuid = $1",
        entity_dict["uuid"],
    )

    if existing_metadata_result:
        existing_metadata = _parse_existing_metadata(existing_metadata_result)
        merged_metadata = _merge_metadata_respecting_locks(
            existing_metadata, new_metadata
        )
        filtered_metadata = _filter_empty_metadata_values(merged_metadata)
        entity_dict["metadata"] = json.dumps(filtered_metadata)
    else:
        # New entity, use new metadata as-is (filtered)
        filtered_metadata = _filter_empty_metadata_values(new_metadata)
        entity_dict["metadata"] = json.dumps(filtered_metadata)

    return entity_dict


def _parse_existing_metadata(metadata_result: Any) -> dict[str, Any]:
    """Parse existing metadata from database result."""
    if isinstance(metadata_result, str):
        return json.loads(metadata_result)
    elif isinstance(metadata_result, dict):
        return metadata_result
    return {}


def _filter_empty_metadata_values(metadata: dict[str, Any]) -> dict[str, Any]:
    """Filter out keys with empty string values, null values, and empty lists from metadata."""
    return {k: v for k, v in metadata.items() if v != "" and v is not None and v != []}


def _merge_metadata_respecting_locks(
    existing_metadata: dict[str, Any], new_metadata: dict[str, Any]
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


async def _upsert_entity(
    conn: asyncpg.Connection,
    entity_dict: dict[str, Any],
    main_table: str,
    user_info: dict[str, Any] | None = None,
) -> None:
    """Execute the upsert query for the main entity, respecting locked fields."""
    columns = list(entity_dict.keys())
    placeholders = [f"${i+1}" for i in range(len(columns))]
    values = list(entity_dict.values())

    # Build the conflict update clause with SQL-based lock checking
    update_clauses = []
    updateable_fields = []  # Track fields that can be updated (for last_edited_at logic)

    for col in columns:
        if col != "uuid":  # Don't update the conflict column
            # Generate SQL-based lock check for this field
            lock_check_sql = (
                f"COALESCE(({main_table}.metadata->'__{col}__lock__')::boolean, false)"
            )

            # Use CASE statement to conditionally update based on lock status
            case_sql = f"""
                {col} = CASE
                    WHEN {lock_check_sql} THEN {main_table}.{col}
                    ELSE EXCLUDED.{col}
                END"""

            update_clauses.append(case_sql)
            updateable_fields.append(col)

    # Always update updated_at for any operation
    update_clauses.append("updated_at = NOW()")

    # Handle last_edited_at and edited_by_name for manual operations
    if user_info:
        # For manual operations, update last_edited_at if any unlocked fields could be updated
        # We check if at least one field is unlocked using SQL logic
        unlocked_conditions = []
        for col in updateable_fields:
            lock_check_sql = (
                f"COALESCE(({main_table}.metadata->'__{col}__lock__')::boolean, false)"
            )
            unlocked_conditions.append(f"NOT {lock_check_sql}")

        if unlocked_conditions:
            # Update last_edited_at if any field is unlocked (meaning manual changes are possible)
            any_unlocked_sql = " OR ".join(unlocked_conditions)
            update_clauses.append(f"""
                last_edited_at = CASE
                    WHEN ({any_unlocked_sql}) THEN NOW()
                    ELSE {main_table}.last_edited_at
                END""")

            # Update edited_by_name if user info is provided and any field is unlocked
            if "name" in user_info:
                user_name_escaped = user_info["name"].replace(
                    "'", "''"
                )  # Escape single quotes
                update_clauses.append(f"""
                    edited_by_name = CASE
                        WHEN ({any_unlocked_sql}) THEN '{user_name_escaped}'
                        ELSE {main_table}.edited_by_name
                    END""")

    # Clean up the update clauses (remove extra whitespace and newlines)
    cleaned_clauses = [
        clause.strip().replace("\n", " ").replace("  ", " ")
        for clause in update_clauses
    ]

    query = f"""
        INSERT INTO {main_table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT (uuid) DO UPDATE
        SET {', '.join(cleaned_clauses)}
    """

    await conn.execute(query, *values)


def _log_import_results(processed_count: int, failed_count: int) -> None:
    """Log the results of the import operation."""
    if failed_count > 0:
        logger.warning(
            f"Import completed with {failed_count} failures out of {processed_count + failed_count} total datasets"
        )
    else:
        logger.info(f"Successfully processed all {processed_count} datasets")


def _validate_import_success(processed_count: int, failed_count: int) -> None:
    """Validate that the import was successful enough to continue."""
    total_datasets = processed_count + failed_count
    if total_datasets > 0 and failed_count > (total_datasets / 2):
        raise RuntimeError(
            f"Import failed: {failed_count}/{total_datasets} datasets could not be processed"
        )


async def _get_or_create_entity(
    conn: asyncpg.Connection, model: type, table_name: str, **kwargs: Any
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
