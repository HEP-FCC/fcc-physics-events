import datetime

from pydantic import BaseModel


# Base model with fields common to all other SoftwareStack models
# Note: Renamed from "Stack" to "SoftwareStack" to avoid ambiguity
class SoftwareStackBase(BaseModel):
    name: str
    file_path: str
    version: str | None = None
    description: str | None = None


# Model for creating a new software stack
class SoftwareStackCreate(SoftwareStackBase):
    pass

    # Model representing a software stack as it exists in the database
    software_stack_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True
