"""
This file defines the Pydantic models used to parse and validate the
structure of the incoming JSON data dictionaries. It does not contain
any database logic.

USAGE FOR CUSTOM DATA FORMATS:
===============================

To add support for your custom data format:

1. Create your entity class by inheriting from BaseEntityData:
   ```python
   class MyCustomEntity(BaseEntityData):
       name: str
       type: str
       custom_field: str | None = None

       def get_all_metadata(self) -> dict[str, Any]:
           return {"type": self.type, "custom_field": self.custom_field}
   ```

2. Create your collection class by inheriting from BaseEntityCollection:
   ```python
   class MyCustomCollection(BaseEntityCollection):
       experiments: list[MyCustomEntity]

       def get_entities(self) -> list[BaseEntityData]:
           return self.experiments
   ```

3. Register your classes and detection rule:
   ```python
   def detect_my_format(raw_data: dict) -> bool:
       return "experiments" in raw_data and isinstance(raw_data["experiments"], list)

   EntityTypeRegistry.register_entity_class("MyCustomEntity", MyCustomEntity)
   EntityTypeRegistry.register_collection_class("MyCustomCollection", MyCustomCollection)
   EntityTypeRegistry.register_detection_rule(detect_my_format, MyCustomCollection)
   ```

The data import system will automatically detect and use your classes.
"""

import re
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.logging import get_logger

logger = get_logger()


class BaseEntityData(BaseModel, ABC):
    """
    Abstract base class for entity data that provides a common interface
    for all entity types that can be processed by the data import system.
    """

    @abstractmethod
    def get_all_metadata(self) -> dict[str, Any]:
        """
        Abstract method that must be implemented by all entity data classes.
        Should return all metadata for the entity as a dictionary.

        Returns:
            Dictionary containing all metadata fields for the entity
        """
        pass


# NOTE(required): Users must define their own data model class
class FccDataset(BaseEntityData):
    """
    Pydantic model for a single dataset from the JSON dictionary.
    Core fields that are likely to be present are defined explicitly,
    while all other fields are stored in the raw_metadata for flexible handling.
    """

    # Core fields that are guaranteed or highly likely to be present
    process_name: str | None = Field(default=None, alias="process-name")
    n_events: int | None = Field(default=None, alias="n-events")
    path: str | None = Field(default=None)
    size: int | None = Field(default=None)
    description: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    status: str | None = Field(default=None)

    # Navigation entity fields
    accelerator: str | None = Field(default=None)
    stage: str | None = Field(default=None)
    campaign: str | None = Field(default=None)
    detector: str | None = Field(default=None)
    file_type: str | None = Field(default=None, alias="file-type")

    # Store all other fields as metadata
    raw_metadata: dict[str, Any] = Field(default_factory=dict, exclude=True)

    @field_validator(
        "process_name",
        "description",
        "comment",
        "status",
        "accelerator",
        "stage",
        "campaign",
        "detector",
        "file_type",
        mode="before",
    )
    @classmethod
    def handle_string_fields(cls, v: Any) -> str | None:
        """
        Handles string fields that might be missing, null, or need whitespace normalization.
        Returns None for null/empty values to avoid storing meaningless data.
        """
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
        if isinstance(v, str):
            normalized = re.sub(r"\s+", " ", v.strip())
            return normalized if normalized else None
        return str(v) if v is not None else None

    @field_validator("n_events", "size", mode="before")
    @classmethod
    def handle_int_fields(cls, v: Any) -> int | None:
        """
        Handles integer fields that might be missing or null.
        Returns None instead of raising an error for invalid values.
        """
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            logger.warning(f"Cannot parse integer value: {v}. Setting to None.")
            return None

    @field_validator("path", mode="before")
    @classmethod
    def handle_path_field(cls, v: Any) -> str | None:
        """
        Handles path field that might be missing or null.
        Returns None for empty/invalid paths.
        """
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return None
        return str(v).strip() if v is not None else None

    @model_validator(mode="before")
    @classmethod
    def extract_metadata(cls, data: Any) -> Any:
        """
        Extract all fields not explicitly defined in the model into raw_metadata.
        This allows flexible handling of varying JSON structures.
        """
        if not isinstance(data, dict):
            return data

        # Fields that are explicitly handled by the model
        core_fields = {
            "process-name",
            "n-events",
            "path",
            "size",
            "description",
            "comment",
            "status",
            "accelerator",
            "stage",
            "campaign",
            "detector",
            "file-type",
        }

        # Create a copy of the data for manipulation
        processed_data = data.copy()
        raw_metadata = {}

        # Extract all non-core fields into raw_metadata
        for key, value in data.items():
            if key not in core_fields:
                # Skip the 'files' field as it's typically large and not needed
                if key != "files":
                    raw_metadata[key] = value

        # Add raw_metadata to the processed data
        processed_data["raw_metadata"] = raw_metadata

        return processed_data

    # NOTE(required): Users must define this function
    def get_all_metadata(self) -> dict[str, Any]:
        """
        Returns all metadata including both core fields and raw_metadata.
        Excludes None values and the process_name (since it's stored as dataset name).
        Also excludes navigation entity fields as they are stored in foreign key relationships.
        """
        metadata: dict[str, Any] = {}

        # Add core fields that have values (excluding navigation fields)
        if self.n_events is not None:
            metadata["n-events"] = self.n_events
        if self.path is not None:
            metadata["path"] = self.path
        if self.size is not None:
            metadata["size"] = self.size
        if self.description is not None:
            metadata["description"] = self.description
        if self.comment is not None:
            metadata["comment"] = self.comment
        if self.status is not None:
            metadata["status"] = self.status

        # Add all raw metadata
        metadata.update(self.raw_metadata)

        return metadata


class BaseEntityCollection(BaseModel, ABC):
    """
    Abstract base class for entity collections that provides a common interface
    for all collection types that can be processed by the data import system.
    """

    @abstractmethod
    def get_entities(self) -> list[BaseEntityData]:
        """
        Abstract method that must be implemented by all entity collection classes.
        Should return a list of entities contained in the collection.

        Returns:
            List of BaseEntityData instances
        """
        pass


class DatasetCollection(BaseEntityCollection):
    """Pydantic model for the root of the JSON dictionary."""

    processes: list[FccDataset]

    def get_entities(self) -> list[BaseEntityData]:
        """
        Return the list of processes/entities in this collection.

        Returns:
            List of FccDataset instances
        """
        return self.processes


class EntityTypeRegistry:
    """
    Registry for user-defined entity and collection classes.
    Users can register their custom classes here to make them discoverable
    by the data import system.
    """

    _entity_classes: dict[str, type[BaseEntityData]] = {}
    _collection_classes: dict[str, type[BaseEntityCollection]] = {}
    _detection_rules: list[tuple[callable, type[BaseEntityCollection]]] = []

    @classmethod
    def register_entity_class(
        cls, name: str, entity_class: type[BaseEntityData]
    ) -> None:
        """Register a custom entity class."""
        cls._entity_classes[name] = entity_class

    @classmethod
    def register_collection_class(
        cls, name: str, collection_class: type[BaseEntityCollection]
    ) -> None:
        """Register a custom collection class."""
        cls._collection_classes[name] = collection_class

    @classmethod
    def register_detection_rule(
        cls, detection_func: callable, collection_class: type[BaseEntityCollection]
    ) -> None:
        """
        Register a detection rule that determines which collection class to use.

        Args:
            detection_func: Function that takes raw_data dict and returns True if this collection class should be used
            collection_class: The collection class to use if detection_func returns True
        """
        cls._detection_rules.append((detection_func, collection_class))

    @classmethod
    def detect_collection_class(
        cls, raw_data: dict
    ) -> type[BaseEntityCollection] | None:
        """
        Detect which collection class to use based on registered detection rules.
        Returns the first matching collection class or None if no match found.
        """
        for detection_func, collection_class in cls._detection_rules:
            try:
                if detection_func(raw_data):
                    return collection_class
            except Exception:
                # If detection function fails, continue to next rule
                continue

        # Return None if no detection rules match - don't fallback to default
        return None

    @classmethod
    def get_entity_class(cls, name: str) -> type[BaseEntityData] | None:
        """Get a registered entity class by name."""
        return cls._entity_classes.get(name)

    @classmethod
    def get_collection_class(cls, name: str) -> type[BaseEntityCollection] | None:
        """Get a registered collection class by name."""
        return cls._collection_classes.get(name)

    @classmethod
    def get_default_collection_class(cls) -> type[BaseEntityCollection] | None:
        """Get the first registered collection class as default."""
        if cls._collection_classes:
            return next(iter(cls._collection_classes.values()))
        return None

    @classmethod
    def list_registered_classes(cls) -> dict[str, dict[str, type]]:
        """List all registered classes for debugging."""
        return {
            "entities": cls._entity_classes.copy(),
            "collections": cls._collection_classes.copy(),
            "detection_rules": [
                (str(func), cls_type) for func, cls_type in cls._detection_rules
            ],
        }


# Detection function for FCC format
def _detect_fcc_format(raw_data: dict) -> bool:
    """Detect if raw_data matches FCC dataset format."""
    return "processes" in raw_data and isinstance(raw_data["processes"], list)


# Auto-register the default FCC classes
EntityTypeRegistry.register_entity_class("FccDataset", FccDataset)
EntityTypeRegistry.register_collection_class("DatasetCollection", DatasetCollection)
EntityTypeRegistry.register_detection_rule(_detect_fcc_format, DatasetCollection)
