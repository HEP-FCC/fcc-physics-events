import datetime

from pydantic import BaseModel


# Base model with fields common to all other Stage models
class StageBase(BaseModel):
    name: str
    description: str | None = None


# Model for creating a new stage
class StageCreate(StageBase):
    pass


# Model representing a stage as it exists in the database
class Stage(StageBase):
    stage_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
