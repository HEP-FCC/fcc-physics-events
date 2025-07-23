"""
Schema-driven API routes for the FCC Physics Events API.
Handles dynamic schema discovery, dropdown data, search, import, and validation.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.storage.database import Database
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["schema-api"])

# This will be injected from main.py
database: Database


def init_dependencies(db: Database) -> None:
    """Initialize dependencies for this router."""
    global database
    database = db


async def get_and_validate_user_from_session(request: Request) -> dict[str, Any]:
    """Get current user from session cookie with CERN validation."""
    from app.auth import cern_auth

    try:
        # Check if session has auth info
        token = request.session.get("token")
        user = request.session.get("user")

        if not token or not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please login.",
            )

        # Validate the token with CERN
        decoded_token = cern_auth.jwt_decode_token(token)
        user_data = await cern_auth.validate_user_from_token(decoded_token)

        return user_data
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during session validation: {e}")
        raise HTTPException(
            status_code=401,
            detail="Session validation failed. Please login again.",
        )


class SearchRequest(BaseModel):
    """Request model for generic search"""

    filters: dict[str, str] = {}
    search: str = ""
    page: int = 1
    limit: int = 20


@router.get("/schema")
async def get_database_schema() -> Any:
    """
    Get the complete database schema configuration for frontend.
    This endpoint analyzes the database structure and returns configuration
    that allows the frontend to work with any database schema.
    """
    try:
        from app.utils import get_config

        config = get_config()
        main_table = config["application"]["main_table"]

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            # Analyze the navigation structure based on the main table
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                main_table
            )

            # Fetch navigation configuration from config file
            navigation_config = _get_navigation_config_from_config(
                config, navigation_analysis
            )

            # Build the response
            schema_config = {
                "tables": [navigation_analysis["main_table"]]
                + list(navigation_analysis["navigation_tables"].keys()),
                "main_table": navigation_analysis["main_table"],
                "foreign_keys": [
                    f"{key}_id"
                    for key in navigation_analysis["navigation_tables"].keys()
                ],
                "navigation_config": {
                    "order": navigation_config["order"],
                    "menu": navigation_config[
                        "config"
                    ],  # Only return what exists in DB
                },
                "mainTableSchema": {
                    "tableName": navigation_analysis["main_table"],
                    "primaryKey": navigation_analysis["main_table_schema"][
                        "primary_key"
                    ],
                    "nameColumn": "name",  # Datasets typically use 'name'
                    "columns": [
                        col["column_name"]
                        for col in navigation_analysis["main_table_schema"]["columns"]
                    ],
                },
                "navigationTables": navigation_analysis["navigation_tables"],
                "navigationOrder": navigation_config["order"],
                "navigation": navigation_config["config"],
                "appTitle": config.get("application", {}).get("title", "Data Explorer"),
                "searchPlaceholder": config.get("application", {}).get(
                    "search_placeholder", f"Search {main_table}..."
                ),
            }

            return schema_config

    except Exception as e:
        logger.error(f"Failed to get database schema: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve database schema"
        )


def _get_navigation_config_from_config(
    config: Any, navigation_analysis: dict[str, Any]
) -> dict[str, Any]:
    """
    Get navigation configuration from config file.
    Uses the navigation.order setting from config.conf.
    """
    # Get the navigation order from config, fallback to alphabetical if not defined
    config_order = config.get("navigation", {}).get("order", [])

    # Map of available navigation entities by key
    navigation_tables = {
        entity["key"]: entity["table_name"]
        for entity in navigation_analysis["navigation_entities"]
    }

    # Use config order if provided, otherwise use all available entities in alphabetical order
    if config_order:
        # Filter to only include entities that actually exist in the schema
        ordered_keys = [key for key in config_order if key in navigation_tables]
        # Add any entities not in config (in case schema has more than config)
        remaining_keys = [
            key for key in navigation_tables.keys() if key not in ordered_keys
        ]
        remaining_keys.sort()  # Alphabetical order for any missing ones
        ordered_keys.extend(remaining_keys)
    else:
        # Fallback to alphabetical order
        ordered_keys = sorted(navigation_tables.keys())

    # Build minimal navigation config - frontend will derive colors, icons, labels
    navigation_configs = {}
    for i, key in enumerate(ordered_keys):
        if key in navigation_tables:
            entity_info = next(
                e for e in navigation_analysis["navigation_entities"] if e["key"] == key
            )
            navigation_configs[key] = {
                "columnName": entity_info["column_name"],
                "orderIndex": i,  # Frontend will use this to derive color from app config
            }

    return {"order": ordered_keys, "config": navigation_configs}


@router.get("/dropdown/{table_key}")
async def get_dropdown_items(
    table_key: str,
    filters: str = Query("", description="JSON string of filters to apply"),
) -> Any:
    """
    Get dropdown items for any navigation table based on schema discovery.
    This replaces table-specific endpoints like /stages/, /detectors/, etc.
    Returns only items that have related datasets.
    """
    try:
        # Parse filters
        filter_dict = {}
        if filters:
            filter_dict = json.loads(filters)

        # Get schema information to find the appropriate table
        from app.utils import get_config

        config = get_config()
        main_table = config["application"]["main_table"]

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                main_table
            )

            # Use the database method instead of direct SQL
            result = await database.get_dropdown_items(
                table_key, main_table, navigation_analysis, filter_dict
            )
            return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in filters parameter")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get dropdown items for {table_key}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load {table_key} options"
        )


@router.post("/search")
async def search_datasets_generic(request: SearchRequest) -> Any:
    """
    Generic search endpoint that works with any database schema.
    Automatically handles joins based on schema discovery.
    """
    try:
        from app.utils import get_config

        config = get_config()
        main_table = config["application"]["main_table"]

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)
            navigation_analysis = await schema_discovery.analyze_navigation_structure(
                main_table
            )

            # Use the database method instead of direct SQL
            result = await database.search_datasets_generic(
                main_table,
                navigation_analysis,
                request.filters,
                request.search,
                request.page,
                request.limit,
            )
            return result

    except Exception as e:
        logger.error(f"Failed to perform generic search: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/import/{table_key}")
async def import_data_generic(
    table_key: str,
    _data: dict[str, Any],
    user: dict[str, Any] = Depends(get_and_validate_user_from_session),
) -> Any:
    """
    Generic data import endpoint that works with any table based on schema discovery.
    """
    try:
        logger.info(
            f"User {user.get('preferred_username', 'unknown')} importing data to {table_key}"
        )

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            if table_key == "main":
                # Handle main table import (datasets)
                # For now, delegate to existing import logic
                raise HTTPException(
                    status_code=501,
                    detail="Main table import not yet implemented via generic endpoint",
                )
            else:
                # Handle navigation table import
                from app.utils import get_config

                config = get_config()
                main_table = config["application"]["main_table"]

                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure(main_table)
                )

                if table_key not in navigation_analysis["navigation_tables"]:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_key}' not found"
                    )

                table_info = navigation_analysis["navigation_tables"][table_key]
                table_name = table_info["table_name"]

                # Basic validation and insertion logic would go here
                # For now, return a placeholder response
                return {
                    "status": "success",
                    "message": f"Import to {table_name} would be processed here",
                }

    except Exception as e:
        logger.error(f"Failed to import data to {table_key}: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed for {table_key}")


@router.post("/validate/{table_key}")
async def validate_data_generic(table_key: str, data: dict[str, Any]) -> Any:
    """
    Generic data validation endpoint that works with any table based on schema discovery.
    """
    try:
        from app.utils import get_config

        config = get_config()
        main_table = config["application"]["main_table"]

        async with database.session() as conn:
            from app.schema_discovery import get_schema_discovery

            schema_discovery = await get_schema_discovery(conn)

            if table_key == "main":
                table_metadata = await schema_discovery.get_table_metadata(main_table)
            else:
                navigation_analysis = (
                    await schema_discovery.analyze_navigation_structure(main_table)
                )
                if table_key not in navigation_analysis["navigation_tables"]:
                    raise HTTPException(
                        status_code=404, detail=f"Table '{table_key}' not found"
                    )

                table_info = navigation_analysis["navigation_tables"][table_key]
                table_metadata = await schema_discovery.get_table_metadata(
                    table_info["table_name"]
                )

            if not table_metadata:
                raise HTTPException(
                    status_code=404, detail=f"Table metadata not found for {table_key}"
                )

            # Perform basic validation
            validation_errors = []

            # Check required fields
            for column in table_metadata["columns"]:
                if not column["is_nullable"] and column["column_name"] not in data.get(
                    "data", {}
                ):
                    validation_errors.append(
                        f"Required field '{column['column_name']}' is missing"
                    )

            # Check data types (basic validation)
            for field, _value in data.get("data", {}).items():
                column_info = next(
                    (
                        col
                        for col in table_metadata["columns"]
                        if col["column_name"] == field
                    ),
                    None,
                )
                if column_info:
                    # Add basic type validation here
                    pass

            return {"valid": len(validation_errors) == 0, "errors": validation_errors}

    except Exception as e:
        logger.error(f"Failed to validate data for {table_key}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Validation failed for {table_key}"
        )
