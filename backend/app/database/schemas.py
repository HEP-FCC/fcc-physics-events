"""
Pydantic models for data validation, mirroring the database schema.

These models ensure that the data we receive from the database or send to it
conforms to the expected types and structure.
"""

import datetime
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Detector Schemas
# =============================================================================
class DetectorBase(BaseModel):
    name: str = Field(..., max_length=255)


class DetectorCreate(DetectorBase):
    pass


class DetectorInDB(DetectorBase):
    detector_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Campaign Schemas
# =============================================================================
class CampaignBase(BaseModel):
    name: str = Field(..., max_length=255)
    detector_id: int


class CampaignCreate(CampaignBase):
    pass


class CampaignInDB(CampaignBase):
    campaign_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =============================================================================
# Sample Schemas
# =============================================================================
class SampleBase(BaseModel):
    name: str = Field(..., max_length=255)
    campaign_id: int
    metadata: dict[str, Any]


class SampleCreate(SampleBase):
    pass


class SampleInDB(SampleBase):
    sample_id: int
    created_at: datetime.datetime
    metadata_search_text: str

    class Config:
        from_attributes = True
