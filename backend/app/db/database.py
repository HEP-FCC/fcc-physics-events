"""
This file contains the Database class, which manages an asyncpg connection
pool and provides higher-level PostgreSQL database functions with session management.
"""

from logging import Logger
from pathlib import Path
from typing import Any

import asyncpg
import structlog
from asyncpg.pool import Pool
from pyhocon import ConfigTree

logger: Logger = structlog.get_logger()


class AsyncSessionContextManager:
    """
    Async context manager for acquiring and releasing a connection from the pool.
    """

    def __init__(self, pool: Pool):
        self._pool = pool
        self._connection: asyncpg.Connection | None = None

    async def __aenter__(self) -> asyncpg.Connection:
        """Acquires a connection from the pool and returns it."""
        self._connection = await self._pool.acquire()
        return self._connection

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Releases the connection back to the pool."""
        if self._connection:
            await self._pool.release(self._connection)


class Database:
    """
    Manages the connection pool and provides higher-level database functions.
    We are working with a PostgreSQL database.
    """

    _pool: Pool | None = None

    async def setup(self, config: ConfigTree) -> None:
        """
        Creates the connection pool and initializes the database.
        This should be called on application startup.
        """
        if self._pool:
            return
        try:
            connection_string = f"""postgresql://{config["user"]}:${config["password"]}@${config["host"]}:${config["port"]}/${config["db"]}"""

            self._pool = await asyncpg.create_pool(
                dsn=connection_string, min_size=5, max_size=20
            )
            logger.info("Database connection pool created successfully.")

            logger.info("Creating schema..")
            schema_file = Path(__file__).parent / "fcc-physics-events.sql"
            with open(schema_file, encoding="utf-8") as f:
                schema_sql = f.read()

            async with self.session() as conn:
                await conn.execute(schema_sql)

            logger.info("Database setup succesfully.")

        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            raise

    def session(self) -> AsyncSessionContextManager:
        """
        Provides a session context manager for raw database interactions.

        Usage:
            async with db.session() as conn:
                await conn.fetch(...)
        """
        if self._pool is None:
            raise RuntimeError(
                "Connection pool is not initialized. Call setup() first."
            )
        return AsyncSessionContextManager(self._pool)

    async def aclose(self) -> None:
        """
        Closes the connection pool. This should be called on application shutdown.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed.")

    async def generate_schema_mapping(self) -> dict[str, str]:
        """
        Generates schema mapping by introspecting the database.

        Returns:
            A dictionary mapping logical field names to database column references.
        """
        mapping: dict[str, str] = {}

        async with self.session() as conn:
            # Get all tables and their columns
            tables = await conn.fetch("""
                SELECT
                    t.table_name,
                    array_agg(c.column_name) as columns
                FROM
                    information_schema.tables t
                JOIN
                    information_schema.columns c ON t.table_name = c.table_name
                WHERE
                    t.table_schema = 'public' AND
                    t.table_type = 'BASE TABLE' AND
                    t.table_name IN ('processes', 'detectors', 'campaigns', 'frameworks', 'accelerator_types')
                GROUP BY
                    t.table_name
            """)

        for record in tables:
            table = record["table_name"]
            for column in record["columns"]:
                # For most tables, use table_name.column_name mapping
                if column == "name":
                    # Special case for name columns - use logical names
                    if table == "processes":
                        mapping["name"] = f"{table}.{column}"
                    else:
                        # Remove 's' from end of table name for singular form
                        singular = table[:-1] if table.endswith("s") else table
                        mapping[singular] = f"{table}.{column}"
                elif column == "metadata" and table == "processes":
                    mapping["metadata"] = f"{table}.{column}"
                elif column == "metadata_search_text" and table == "processes":
                    mapping["metadata_search_text"] = f"{table}.{column}"

        return mapping
