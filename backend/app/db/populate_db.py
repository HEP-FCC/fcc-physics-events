"""
Standalone script to initialize the database schema and insert sample data.

This script should be run once before the first application start. It connects
to the database defined by the DATABASE_URL environment variable and executes the
SQL commands from `fcc-physics-events.sql`.
"""

import asyncio
import os
from pathlib import Path

import asyncpg

# Construct the DSN from environment variables, with a fallback for local dev
DB_DSN = os.environ.get(
    "DATABASE_URL",
    f"postgres://{os.getenv('POSTGRES_USER', 'fcc_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'fcc_password')}@"
    f"localhost:5432/{os.getenv('POSTGRES_DB', 'fcc_physics_samples')}",
)

# Define the path to the SQL file relative to this script
SQL_FILE_PATH = Path(__file__).parent / "fcc-physics-samples.sql"


async def populate() -> None:
    """Connects to the database and executes the schema setup SQL."""
    conn: asyncpg.Connection | None = None
    try:
        print(f"Connecting to database...")
        conn = await asyncpg.connect(dsn=DB_DSN)
        print("Connection successful.")

        print(f"Reading schema from {SQL_FILE_PATH}...")
        with open(SQL_FILE_PATH, encoding="utf-8") as f:
            sql_commands = f.read()

        print("Executing SQL script to create schema and tables...")
        await conn.execute(sql_commands)
        print("Database schema and indexes created successfully.")

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
    """Inserts accelerator types, frameworks, campaigns, detectors, and samples."""
    # Use transactions for data integrity
    async with conn.transaction():
        # Insert Accelerator Types
        await conn.execute(
            """
            INSERT INTO accelerator_types (name, description) VALUES
                ('fcc-ee', 'FCC colliding electrons and positrons'),
                ('fcc-hh', 'FCC colliding protons and heavier nucleus')
            ON CONFLICT (name) DO NOTHING;
            """
        )

        # Insert Frameworks
        await conn.execute(
            """
            INSERT INTO frameworks (name, description) VALUES
                ('Delphes', 'Framework for parametrized simulation'),
                ('FullSim', 'Full simulation framework')
            ON CONFLICT (name) DO NOTHING;
            """
        )

        # Insert Campaigns
        await conn.execute(
            """
            INSERT INTO campaigns (name, description) VALUES
                ('Winter2023', 'Winter 2023 code evolution cycle'),
                ('Summer2024', 'Summer 2024 code evolution cycle')
            ON CONFLICT (name) DO NOTHING;
            """
        )

        # Get IDs for inserted records
        accelerator_ee_id = await conn.fetchval(
            "SELECT accelerator_type_id FROM accelerator_types WHERE name = 'fcc-ee'"
        )

        # Insert Detectors
        await conn.execute(
            """
            INSERT INTO detectors (name, accelerator_type_id) VALUES
                ('IDEA lighterBP 50pc', $1),
                ('IDEA Standard', $1),
                ('CLD Standard', $1)
            ON CONFLICT (name) DO NOTHING;
            """,
            accelerator_ee_id,
        )

        # Get IDs for remaining records
        framework_delphes_id = await conn.fetchval(
            "SELECT framework_id FROM frameworks WHERE name = 'Delphes'"
        )
        campaign_winter_id = await conn.fetchval(
            "SELECT campaign_id FROM campaigns WHERE name = 'Winter2023'"
        )
        detector_idea_lighter_id = await conn.fetchval(
            "SELECT detector_id FROM detectors WHERE name = 'IDEA lighterBP 50pc'"
        )

        # Insert Samples
        if all(
            (
                accelerator_ee_id,
                framework_delphes_id,
                campaign_winter_id,
                detector_idea_lighter_id,
            )
        ):
            await conn.execute(
                """
                INSERT INTO samples (
                    name,
                    accelerator_type_id,
                    framework_id,
                    campaign_id,
                    detector_id,
                    metadata
                ) VALUES
                ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING;
                """,
                "ee_ZH_Zmumu",
                accelerator_ee_id,
                framework_delphes_id,
                campaign_winter_id,
                detector_idea_lighter_id,
                '{"energy_gev": 240, "cross_section_pb": 0.201, "generator": "Whizard", "process": "ee->ZH->mumuX"}',
            )


if __name__ == "__main__":
    asyncio.run(populate())
