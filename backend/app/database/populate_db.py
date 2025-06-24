"""
Standalone script to initialize the database schema and insert sample data.

This script should be run once before the first application start. It connects
to the database defined in the docker-compose.yml file and executes the
SQL commands from `fcc-physics-samples.sql`.
"""

import asyncio
import os
from pathlib import Path

import asyncpg  # type: ignore

# Construct the DSN from environment variable1s
DB_DSN = (
    f"postgres://{os.getenv('POSTGRES_USER', 'fcc_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'fcc_password')}@"
    # Use 'db' as the hostname if running this script from another Docker container
    # Use 'localhost' if running from the host machine
    f"localhost:5432/{os.getenv('POSTGRES_DB', 'fcc_physics_samples')}"
)

# Define the path to the SQL file relative to this script
SQL_FILE_PATH = Path(__file__).parent / "fcc-physics-samples.sql"


async def populate() -> None:
    """Connects to the database and executes the schema setup SQL."""
    conn = None
    try:
        print(
            f"Connecting to database at {DB_DSN.replace(os.getenv('POSTGRES_PASSWORD', 'fcc_password'), '***')}..."
        )
        conn = await asyncpg.connect(dsn=DB_DSN)
        print("Connection successful.")

        print(f"Reading schema from {SQL_FILE_PATH}...")
        with open(SQL_FILE_PATH) as f:
            sql_commands = f.read()

        print("Executing SQL script to create schema and tables...")
        await conn.execute(sql_commands)
        print("Database schema created successfully.")

        # Add some initial data for testing if not already present
        print("Populating initial data...")
        await insert_initial_data(conn)
        print("Initial data population complete.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            await conn.close()
            print("Database connection closed.")


async def insert_initial_data(conn: asyncpg.Connection) -> None:
    """Inserts detectors, campaigns, and samples."""
    # Use transactions for data integrity
    async with conn.transaction():
        # Insert Detectors
        await conn.execute(
            "INSERT INTO detectors (name) VALUES ('Alpha_Spectrometer'), ('Beta_Imager') ON CONFLICT (name) DO NOTHING;"
        )

        # Insert Campaigns
        detector_alpha_id = await conn.fetchval(
            "SELECT detector_id FROM detectors WHERE name = 'Alpha_Spectrometer'"
        )
        detector_beta_id = await conn.fetchval(
            "SELECT detector_id FROM detectors WHERE name = 'Beta_Imager'"
        )

        await conn.execute(
            """
            INSERT INTO campaigns (detector_id, name) VALUES
                ($1, 'Q1_2024_Calibration'),
                ($1, 'Q2_2024_Experiment'),
                ($2, 'High_Energy_Tests_2025')
            ON CONFLICT (detector_id, name) DO NOTHING;
            """,
            detector_alpha_id,
            detector_beta_id,
        )

        # Insert Samples
        campaign_q2_id = await conn.fetchval(
            "SELECT campaign_id FROM campaigns WHERE name = 'Q2_2024_Experiment'"
        )
        campaign_he_id = await conn.fetchval(
            "SELECT campaign_id FROM campaigns WHERE name = 'High_Energy_Tests_2025'"
        )

        await conn.execute(
            """
            INSERT INTO samples (campaign_id, name, metadata) VALUES
            ($1, 'Sample_A001', $3),
            ($1, 'Sample_A002', $4),
            ($2, 'Sample_B001', $5)
            ON CONFLICT DO NOTHING;
            """,
            campaign_q2_id,
            campaign_he_id,
            '{"operator": "john_doe", "temperature_celsius": 22.5, "material": "silicon_wafer_batch_123"}',
            '{"operator": "jane_smith", "temperature_celsius": 23.1, "material": "silicon_wafer_batch_456"}',
            '{"operator": "jane_smith", "energy_level_gev": 500, "particle_type": "muon", "filter_id": "F77-a"}',
        )


if __name__ == "__main__":
    asyncio.run(populate())
