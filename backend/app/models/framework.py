import datetime

from pydantic import BaseModel


# Base model with fields common to all other Framework models
class FrameworkBase(BaseModel):
    name: str
    description: str | None = None


# Model for creating a new framework
class FrameworkCreate(FrameworkBase):
    pass


# Model representing a framework as it exists in the database
class Framework(FrameworkBase):
    framework_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
