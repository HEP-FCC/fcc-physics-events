import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


# Base model with fields for creation and updates
class DatasetBase(BaseModel):
    name: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    # Foreign keys are optional because of ON DELETE SET NULL in the database
    accelerator_id: int | None = None
    stage_id: int | None = None
    campaign_id: int | None = None
    detector_id: int | None = None


# Model for creating a new dataset (used for API input)
class DatasetCreate(DatasetBase):
    pass


# Model for updating an existing dataset (used for API input)
class DatasetUpdate(BaseModel):
    name: str | None = None
    metadata: dict[str, Any] | None = None
    accelerator_id: int | None = None
    stage_id: int | None = None
    campaign_id: int | None = None
    detector_id: int | None = None


# The core model representing a dataset record from the database
class Dataset(DatasetBase):
    dataset_id: int
    created_at: datetime.datetime
    last_edited_at: datetime.datetime

    class Config:
        from_attributes = True


# A comprehensive model for API responses, including joined data from other tables
class DatasetWithDetails(Dataset):
    detector_name: str | None = None
    campaign_name: str | None = None
    stage_name: str | None = None
    accelerator_type_name: str | None = None

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

    class Config:
        from_attributes = True
