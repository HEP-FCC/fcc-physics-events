"""
This file defines the Pydantic models used to parse and validate the
structure of the incoming FCC JSON data dictionaries. It does not contain
any database logic.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.logging import get_logger

logger = get_logger()


class FccProcess(BaseModel):
    """
    Pydantic model for a single physics process from the JSON dictionary.
    The 'files' field has been removed as it is not needed for storage.
    """

    process_name: str = Field(alias="process-name")
    n_events: int = Field(alias="n-events")
    sum_of_weights: float = Field(alias="sum-of-weights")
    n_files_good: int = Field(alias="n-files-good")
    n_files_bad: int = Field(alias="n-files-bad")
    n_files_eos: int = Field(alias="n-files-eos")
    size: int
    path: str
    # The 'files' field has been removed from this model.
    # Pydantic will now ignore it during parsing.
    description: str
    comment: str
    cross_section: float = Field(alias="cross-section")
    k_factor: float = Field(alias="k-factor")
    matching_eff: float = Field(alias="matching-eff")
    status: str

    @field_validator("description", mode="before")
    @classmethod
    def normalize_whitespace(cls, v: str) -> str:
        """Strips leading/trailing whitespace and collapses internal whitespace."""
        if isinstance(v, str):
            return re.sub(r"\s+", " ", v.strip())
        return v

    @field_validator("cross_section", "k_factor", "matching_eff", mode="before")
    @classmethod
    def convert_str_to_float(cls, v: Any) -> float:
        """Handles source data that might provide numbers as strings."""
        try:
            return float(v)
        except ValueError:
            logger.error(
                "Can't parse the float value of %s for either of those values: cross_section, k_factor or matching_eff. Using 0.0 instead.",
                v,
            )
            raise


class ProcessCollection(BaseModel):
    """Pydantic model for the root of the JSON dictionary."""

    processes: list[FccProcess]
