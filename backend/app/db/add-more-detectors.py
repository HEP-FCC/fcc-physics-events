"""
Standalone script to add additional detectors to the database for fuzzy search testing.

This script adds several detector samples to test the fuzzy search functionality.
"""

import asyncio
import os

import asyncpg

# Construct the DSN from environment variables, with a fallback for local dev
DB_DSN = os.environ.get(
    "DATABASE_URL",
    f"postgres://{os.getenv('POSTGRES_USER', 'fcc_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'fcc_password')}@"
    f"localhost:5432/{os.getenv('POSTGRES_DB', 'fcc_physics_samples')}",
)


async def populate_detectors() -> None:
    """Connects to the database and adds detector samples for fuzzy search testing."""
    conn: asyncpg.Connection | None = None
    try:
        print("Connecting to database...")
        conn = await asyncpg.connect(dsn=DB_DSN)
        print("Connection successful.")

        # Define detector samples to add
        detectors: list[str] = [
            "Alpha_Detector",  # Similar to existing "Alpha_Spectrometer"
            "Alpha_Spectroscope",  # Very similar to "Alpha_Spectrometer"
            "Beta_Imager_2000",  # Extension of existing "Beta_Imager"
            "Beta_Scanner",  # Similar to "Beta_Imager"
            "Gamma_Ray_Detector",  # New detector family
            "Gamma_Spectrometer",  # New detector family
            "Delta_Sensor_Array",  # New detector family
            "Neutrino_Observatory",  # Completely different detector
            "Muon_Chamber",  # Completely different detector
        ]

        # Insert detectors
        print(f"Adding {len(detectors)} detector samples...")
        async with conn.transaction():
            # Using ON CONFLICT (name) DO NOTHING is idempotent
            await conn.executemany(
                "INSERT INTO detectors (name) VALUES ($1) ON CONFLICT (name) DO NOTHING",
                [(name,) for name in detectors],
            )

        # Verify the insertion
        detector_count = await conn.fetchval("SELECT COUNT(*) FROM detectors")
        print(f"Total detectors now in database: {detector_count}")

        print("Detector samples added successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            await conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(populate_detectors())
