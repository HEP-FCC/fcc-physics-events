"""
UUID generation utilities for the FCC Physics Events application.

This module provides utilities for generating deterministic UUIDs for datasets
and other entities in the physics events database.
"""

import uuid

from app.utils.config import get_config

# Load configuration once at module level
config = get_config()

# UUID namespace for dataset identification
# This namespace creates deterministic UUIDs for datasets based on the FCC project
# identifier and version. For versioning: FCCv01 -> this namespace, FCCv02 -> different namespace.
ENTITY_UUID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_DNS,
    config.get("database.entity_uuid_namespace", "entity_uuid_namespace.v01"),
)


def generate_dataset_uuid(
    dataset_name: str,
    **foreign_key_ids: int | None,
) -> str:
    """
    Generate deterministic UUID for a dataset based on key identifying fields.

    Uses UUID5 (SHA-1 based) to ensure the same input always generates the same UUID.
    The namespace is derived from the FCC project domain and version (v01).

    Args:
        dataset_name: The dataset name
        **foreign_key_ids: Variable foreign key IDs (e.g., campaign_id=1, accelerator_id=2)

    Returns:
        String representation of the generated UUID

    Example:
        >>> generate_dataset_uuid("my_dataset", campaign_id=1, detector_id=2)
        'a1b2c3d4-e5f6-5789-abcd-ef1234567890'
    """
    # Sort the foreign key IDs by key name for consistent ordering
    sorted_keys = sorted(foreign_key_ids.keys())

    # Convert None values to string "0" and IDs to strings, in sorted order
    foreign_key_parts = []
    for key in sorted_keys:
        value = foreign_key_ids[key]
        value_str = str(value) if value is not None else "0"
        foreign_key_parts.append(value_str)

    foreign_keys_str = ",".join(foreign_key_parts)

    # Create the deterministic name for UUID5 generation
    uuid_name = f"{dataset_name},{foreign_keys_str}"

    # Generate deterministic UUID5 using the FCC namespace
    dataset_uuid = uuid.uuid5(ENTITY_UUID_NAMESPACE, uuid_name)

    return str(dataset_uuid)
