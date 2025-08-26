"""
This file defines the Pydantic models used to parse and validate the
structure of the incoming FCC JSON data dictionaries. It does not contain
any database logic.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.logging import get_logger

logger = get_logger()


class FccDataset(BaseModel):
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


class DatasetCollection(BaseModel):
    """Pydantic model for the root of the JSON dictionary."""

    processes: list[FccDataset]
