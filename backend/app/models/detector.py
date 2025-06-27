import datetime

from pydantic import BaseModel


# Base model with fields common to all other Detector models
class DetectorBase(BaseModel):
    name: str
    # Foreign key is optional because of ON DELETE SET NULL
    accelerator_type_id: int | None = None


# Model for creating a new detector
class DetectorCreate(DetectorBase):
    pass


# Model representing a detector as it exists in the database
class Detector(DetectorBase):
    detector_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
