"""
Generic models for schema-driven database entities.

These models work with any database schema by using dynamic field generation
based on the discovered schema structure.
"""

import datetime
from typing import Any

from pydantic import BaseModel, Field, create_model, model_validator


class DatabaseEntityBase(BaseModel):
    """Base model for any database entity with common fields."""

    # Every entity should have an ID and name
    id: int
    name: str

    # Optional common fields that many entities might have
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    last_edited_at: datetime.datetime | None = None

    # Metadata field for flexible additional data
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Allow any additional fields that might come from the database
    model_config = {"extra": "allow", "from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_jsonb_as_dict(cls, data: Any) -> Any:
        """
        Ensures that if 'metadata' is returned as a JSON string from the DB,
        it's parsed into a dictionary.
        """
        if isinstance(data, dict) and isinstance(data.get("metadata"), str):
            import json

            try:
                data["metadata"] = json.loads(data["metadata"])
            except json.JSONDecodeError:
                # Let Pydantic handle the error if it's not valid JSON
                pass
        return data


class GenericEntityCreate(BaseModel):
    """Generic model for creating any entity."""

    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Allow any additional fields
    model_config = {"extra": "allow"}


class GenericEntityUpdate(BaseModel):
    """Generic model for updating any entity."""

    name: str | None = None
    metadata: dict[str, Any] | None = None

    # Allow any additional fields
    model_config = {"extra": "allow"}


class GenericEntityWithDetails(DatabaseEntityBase):
    """
    Generic model for entities with joined details from related tables.

    This model will have navigation entity names dynamically added as
    {entity_type}_name fields based on the schema discovery.
    """

    pass


class DropdownItem(BaseModel):
    """Generic dropdown item for any entity."""

    id: int
    name: str


class PaginatedResponse(BaseModel):
    """Generic paginated response for any entity type."""

    total: int
    items: list[dict[str, Any]]  # Flexible items that can contain any entity data


def create_dynamic_entity_model(
    table_name: str,
    primary_key: str,
    columns: list[str],
    foreign_keys: dict[str, str] | None = None,
) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model based on database schema.

    Args:
        table_name: Name of the database table
        primary_key: Name of the primary key column
        columns: List of column names in the table
        foreign_keys: Dict mapping foreign key columns to their referenced tables

    Returns:
        Dynamically created Pydantic model class
    """

    # Start with base fields
    fields: dict[str, Any] = {
        primary_key: (int, ...),  # Primary key is required
        "name": (str, ...),  # Name is required for all entities
    }

    # Add optional fields for common columns
    common_optional_fields: dict[str, Any] = {
        "created_at": (datetime.datetime | None, None),
        "updated_at": (datetime.datetime | None, None),
        "last_edited_at": (datetime.datetime | None, None),
        "metadata": (dict[str, Any], Field(default_factory=dict)),
        "description": (str | None, None),
    }

    # Add fields for all columns that aren't already handled
    for column in columns:
        if column not in fields:
            if column in common_optional_fields:
                fields[column] = common_optional_fields[column]
            elif foreign_keys and column in foreign_keys:
                # Foreign key fields are optional (can be NULL)
                fields[column] = (int | None, None)
            else:
                # Default to optional string for unknown columns
                fields[column] = (str | None, None)

    # Create the model class
    model_class = create_model(
        f"{table_name.title()}Entity", __base__=DatabaseEntityBase, **fields
    )

    return model_class


def create_dynamic_entity_with_details_model(
    table_name: str,
    primary_key: str,
    columns: list[str],
    navigation_tables: dict[str, str],
) -> type[BaseModel]:
    """
    Create a dynamic model that includes navigation entity names.

    Args:
        table_name: Name of the main database table
        primary_key: Name of the primary key column
        columns: List of column names in the main table
        navigation_tables: Dict mapping entity types to their name columns

    Returns:
        Dynamically created model with navigation details
    """

    # Start with the basic entity model
    base_model = create_dynamic_entity_model(table_name, primary_key, columns)

    # Add navigation entity name fields
    navigation_fields: dict[str, Any] = {}
    for entity_type in navigation_tables:
        field_name = f"{entity_type}_name"
        navigation_fields[field_name] = (str | None, None)

    # Create the enhanced model
    model_class = create_model(
        f"{table_name.title()}EntityWithDetails",
        __base__=base_model,
        **navigation_fields,
    )

    return model_class


# Export commonly used models
__all__ = [
    "DatabaseEntityBase",
    "GenericEntityCreate",
    "GenericEntityUpdate",
    "GenericEntityWithDetails",
    "DropdownItem",
    "PaginatedResponse",
    "create_dynamic_entity_model",
    "create_dynamic_entity_with_details_model",
]
