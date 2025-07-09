import datetime

from pydantic import BaseModel


# Base model with fields common to all other Campaign models
class CampaignBase(BaseModel):
    name: str


# Model for creating a new campaign
class CampaignCreate(CampaignBase):
    pass


# Model representing a campaign as it exists in the database
class Campaign(CampaignBase):
    campaign_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
