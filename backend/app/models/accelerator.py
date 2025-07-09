import datetime

from pydantic import BaseModel


# Base model with fields common to all other AcceleratorType models
class AcceleratorBase(BaseModel):
    name: str


# Model for creating a new accelerator type
class AcceleratorCreate(AcceleratorBase):
    pass


# Model representing an accelerator as it exists in the database
class Accelerator(AcceleratorBase):
    accelerator_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
