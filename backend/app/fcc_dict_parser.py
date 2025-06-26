import json
import re
from logging import getLogger

from pydantic import BaseModel, Field, field_validator

from .db.database import Database


def bytes_to_gib(bytes_value: int) -> float:
    """
    Convert bytes to gibibytes (GiB) with 2 decimal places precision.

    Args:
        bytes_value: Integer representing size in bytes

    Returns:
        Size in gibibytes as a float with 2 decimal places precision
    """
    # 1 GiB = 2^30 bytes = 1,073,741,824 bytes
    gib_value = bytes_value / (2**30)
    # Round to 2 decimal places
    return round(gib_value, 2)


# Type for a file entry: [filename, event_count]
class FileEntry(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    filename: str
    event_count: int

    def __init__(self, data):
        if isinstance(data, list) and len(data) == 2:
            super().__init__(filename=data[0], event_count=data[1])
        else:
            raise ValueError(
                "FileEntry must be initialized with a list of [filename, event_count]"
            )

    def model_dump(self):
        return [self.filename, self.event_count]


class Process(BaseModel):
    """Pydantic model for a physics process."""

    process_name: str = Field(alias="process-name")
    n_events: int = Field(alias="n-events")
    sum_of_weights: float = Field(alias="sum-of-weights")
    n_files_good: int = Field(alias="n-files-good")
    n_files_bad: int = Field(alias="n-files-bad")
    n_files_eos: int = Field(alias="n-files-eos")
    size: int
    path: str
    files: list[FileEntry]
    description: str
    comment: str
    cross_section: float = Field(alias="cross-section")
    k_factor: str = Field(alias="k-factor")
    matching_eff: str = Field(alias="matching-eff")
    status: str

    @field_validator("files", mode="before")
    @classmethod
    def validate_files(cls, v):
        if isinstance(v, list):
            return [FileEntry(item) for item in v]
        raise ValueError("Files must be a list")

    @field_validator("description", mode="before")
    @classmethod
    def normalize_whitespace(cls, v):
        if isinstance(v, str):
            return re.sub(r"\s+", " ", v.strip())
        return v


class ProcessCollection(BaseModel):
    """Pydantic model for a collection of physics processes."""

    processes: list[Process]


class FccDictParser:
    """
    Parses a JSON file containing physics process data and inserts it into the database.
    """

    def __init__(self, db: Database):
        self.db = db
        self.logger = getLogger(__name__)

    async def parse_and_insert(
        self, json_content: bytes, accelerator_type: str = "fcc-ee"
    ):
        """
        Parses the JSON content and inserts the processes into the database.

        Args:
            json_content: The JSON content as bytes
            accelerator_type: The accelerator type name (e.g., "fcc-ee", "fcc-hh")
        """
        try:
            raw_data = json.loads(json_content)
            data = ProcessCollection.model_validate(raw_data)

            async with self.db.session() as conn:
                # 1. Get or create accelerator type
                accelerator_id = await self._get_or_create_accelerator_type(
                    conn, accelerator_type
                )

                # 2. Process each physics process
                for process in data.processes:
                    # Extract and store necessary metadata components
                    framework_id = await self._get_or_create_framework(conn, process)
                    campaign_id = await self._get_or_create_campaign(conn, process)
                    detector_id = await self._get_or_create_detector(
                        conn, process, accelerator_id
                    )

                    # 3. Insert the process with all required foreign keys
                    await conn.execute(
                        """
                        INSERT INTO processes (
                            name,
                            accelerator_type_id,
                            framework_id,
                            campaign_id,
                            detector_id,
                            metadata
                        )
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (name) DO UPDATE
                        SET metadata = $6,
                            accelerator_type_id = $2,
                            framework_id = $3,
                            campaign_id = $4,
                            detector_id = $5;
                        """,
                        process.process_name,
                        accelerator_id,
                        framework_id,
                        campaign_id,
                        detector_id,
                        process.model_dump_json(by_alias=True),
                    )
            self.logger.info("Successfully parsed and inserted data.")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
            raise ValueError("Invalid JSON format") from e
        except Exception as e:
            self.logger.error(f"An error occurred during parsing or insertion: {e}")
            raise

    async def _get_or_create_accelerator_type(self, conn, accelerator_type: str) -> int:
        """Get or create an accelerator type and return its ID."""
        # Default description mapping
        descriptions = {
            "fcc-ee": "Future Circular Collider - electron-positron option",
            "fcc-hh": "Future Circular Collider - hadron-hadron option",
        }
        description = descriptions.get(accelerator_type.lower(), "")

        # Try to get existing accelerator type
        record = await conn.fetchrow(
            "SELECT accelerator_type_id FROM accelerator_types WHERE name = $1",
            accelerator_type.lower(),
        )

        if record:
            return record["accelerator_type_id"]

        # Create new accelerator type
        return await conn.fetchval(
            """
            INSERT INTO accelerator_types (name, description)
            VALUES ($1, $2)
            RETURNING accelerator_type_id
            """,
            accelerator_type.lower(),
            description,
        )

    async def _get_or_create_framework(self, conn, process: Process) -> int:
        """Extract framework info from process and get or create it in DB."""
        # Try to derive framework from metadata (example implementation)
        # In practice, you might need to adjust this to match your data structure
        framework_name = "Unknown"
        framework_desc = ""

        # If process has "framework" in its metadata, extract it
        metadata = json.loads(process.model_dump_json(by_alias=True))
        if "comment" in metadata and "framework" in metadata["comment"].lower():
            # Simple extraction - in practice you'd want more robust parsing
            framework_name = (
                metadata["comment"].split("framework:")[1].strip().split()[0]
            )

        # If we couldn't determine the framework, default to Delphes
        if framework_name == "Unknown":
            framework_name = "Delphes"
            framework_desc = "Fast detector simulation framework with parameterized detector response"

        # Try to get existing framework
        record = await conn.fetchrow(
            "SELECT framework_id FROM frameworks WHERE name = $1", framework_name
        )

        if record:
            return record["framework_id"]

        # Create new framework
        return await conn.fetchval(
            """
            INSERT INTO frameworks (name, description)
            VALUES ($1, $2)
            RETURNING framework_id
            """,
            framework_name,
            framework_desc,
        )

    async def _get_or_create_campaign(self, conn, process: Process) -> int:
        """Extract campaign info from process and get or create it in DB."""
        # In production code, you would extract this from the process metadata
        # For now, we'll use a default campaign based on path or description
        campaign_name = "Unknown"

        # Example: Extract campaign from path if it contains something like "Winter2023"
        metadata = json.loads(process.model_dump_json(by_alias=True))
        path = metadata.get("path", "")

        campaigns = [
            "Winter2023",
            "Spring2023",
            "Summer2023",
            "Fall2023",
            "Winter2024",
            "Spring2024",
            "Summer2024",
            "Fall2024",
        ]

        for campaign in campaigns:
            if campaign.lower() in path.lower():
                campaign_name = campaign
                break

        # If we couldn't determine the campaign, use a timestamp-derived one
        if campaign_name == "Unknown":
            import datetime

            current_time = datetime.datetime.now()
            season = (
                "Winter"
                if current_time.month in [12, 1, 2]
                else "Spring"
                if current_time.month in [3, 4, 5]
                else "Summer"
                if current_time.month in [6, 7, 8]
                else "Fall"
            )
            campaign_name = f"{season}{current_time.year}"

        # Try to get existing campaign
        record = await conn.fetchrow(
            "SELECT campaign_id FROM campaigns WHERE name = $1", campaign_name
        )

        if record:
            return record["campaign_id"]

        # Create new campaign
        return await conn.fetchval(
            """
            INSERT INTO campaigns (name, description)
            VALUES ($1, $2)
            RETURNING campaign_id
            """,
            campaign_name,
            f"Campaign auto-created from uploaded data: {campaign_name}",
        )

    async def _get_or_create_detector(
        self, conn, process: Process, accelerator_type_id: int
    ) -> int:
        """Extract detector info from process and get or create it in DB."""
        # In production code, you would extract this from the process metadata
        # For now, use a default detector or try to extract from the process description
        detector_name = "Unknown Detector"

        # Example: Try to extract detector info from description
        metadata = json.loads(process.model_dump_json(by_alias=True))
        description = metadata.get("description", "")

        # Look for common detector names in description
        common_detectors = [
            "CLD",
            "IDEA",
            "IDEA Standard",
            "IDEA lighterBP",
            "FCC-hh Baseline",
            "FCC-hh Forward",
        ]

        for detector in common_detectors:
            if detector.lower() in description.lower():
                detector_name = detector
                break

        # Try to get existing detector
        record = await conn.fetchrow(
            "SELECT detector_id FROM detectors WHERE name = $1", detector_name
        )

        if record:
            return record["detector_id"]

        # Create new detector
        return await conn.fetchval(
            """
            INSERT INTO detectors (name, accelerator_type_id)
            VALUES ($1, $2)
            RETURNING detector_id
            """,
            detector_name,
            accelerator_type_id,
        )
