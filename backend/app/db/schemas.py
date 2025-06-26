"""
Pydantic models for data validation, mirroring the database schema.

These models ensure that the data we receive from the database or send to it
conforms to the expected types and structure.
"""

import datetime
import json
from typing import Any

from pydantic import BaseModel, Field, model_validator


# =============================================================================
# Search Query Schema
# =============================================================================
class SearchQuery(BaseModel):
    """Defines the available parameters for searching processes."""

    sample_name: str | None = Field(
        default=None, description="Regex/Fuzzy pattern for Sample name"
    )
    detector_name: str | None = Field(
        default=None, description="Regex/Fuzzy pattern for Detector name"
    )
    campaign_name: str | None = Field(
        default=None, description="Regex/Fuzzy pattern for Campaign name"
    )
    framework_name: str | None = Field(
        default=None, description="Regex/Fuzzy pattern for Framework name"
    )
    accelerator_type_name: str | None = Field(
        default=None, description="Regex/Fuzzy pattern for Accelerator Type name"
    )
    metadata_contains: str | None = Field(
        default=None, description="Text to search for within sample metadata"
    )

    use_fuzzy_search: bool = Field(
        default=False,
        description="Enable fuzzy (similarity) search instead of regex/substring matching.",
    )
    exact_match: bool = Field(
        default=False,
        description="Enable exact (but case-insensitive) matching, ignoring regex and fuzzy search.",
    )
    similarity_threshold: float = Field(
        default=0.3, ge=0, le=1, description="Threshold for fuzzy search similarity."
    )


# =============================================================================
# Accelerator Type Schemas
# =============================================================================
class AcceleratorTypeBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class AcceleratorTypeCreate(AcceleratorTypeBase):
    pass


class AcceleratorTypeInDB(AcceleratorTypeBase):
    accelerator_type_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Framework Schemas
# =============================================================================
class FrameworkBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class FrameworkCreate(FrameworkBase):
    pass


class FrameworkInDB(FrameworkBase):
    framework_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Campaign Schemas
# =============================================================================
class CampaignBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class CampaignCreate(CampaignBase):
    pass


class CampaignInDB(CampaignBase):
    campaign_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Detector Schemas
# =============================================================================
class DetectorBase(BaseModel):
    name: str = Field(..., max_length=255)
    accelerator_type_id: int | None = None


class DetectorCreate(DetectorBase):
    pass


class DetectorInDB(DetectorBase):
    detector_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Sample Schemas
# =============================================================================
class ProcessBase(BaseModel):
    name: str = Field(..., max_length=255)
    accelerator_type_id: int
    framework_id: int
    campaign_id: int
    detector_id: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessCreate(ProcessBase):
    pass


class ProcessInDB(ProcessBase):
    process_id: int
    created_at: datetime.datetime
    metadata_search_text: str
    detector_name: str
    campaign_name: str
    framework_name: str
    accelerator_name: str

    @model_validator(mode="before")
    @classmethod
    def parse_metadata(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert metadata from string to dictionary if it's a string.
        This handles the JSON string format that comes from the database.
        """
        if (
            isinstance(data, dict)
            and "metadata" in data
            and isinstance(data["metadata"], str)
        ):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except json.JSONDecodeError:
                pass  # If it's not valid JSON, let Pydantic handle validation error
        return data

    class Config:
        from_attributes = True
