"""
Core database connection and session management module.

This file contains the Database class, which manages an asyncpg connection
pool and provides a session-based context manager for database interactions.
"""

import os
from typing import Any, TypeVar

import asyncpg  # type: ignore
from asyncpg.pool import Pool  # type: ignore
from pydantic import BaseModel

# A generic type for Pydantic models to allow for typed returns from queries
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


class Session:
    """
    A database session tied to a single connection.

    This class is not meant to be instantiated directly. Instead, it is
    provided by the `Database.session()` context manager. It wraps an
    `asyncpg.Connection` object, providing a clean API for executing queries.
    """

    def __init__(self, connection: asyncpg.Connection) -> None:
        self._connection = connection

    async def fetch(
        self, query: str, *args: Any, model: type[PydanticModel] | None = None
    ) -> list[PydanticModel] | list[asyncpg.Record]:
        """Executes a query and returns a list of results."""
        records = await self._connection.fetch(query, *args)
        if model:
            return [model.model_validate(dict(record)) for record in records]
        return records

    async def fetchrow(
        self, query: str, *args: Any, model: type[PydanticModel] | None = None
    ) -> PydanticModel | asyncpg.Record | None:
        """Executes a query and returns a single result."""
        record = await self._connection.fetchrow(query, *args)
        if record and model:
            return model.model_validate(dict(record))
        return record

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Executes a query and returns a single value from a single result."""
        return await self._connection.fetchval(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        """Executes a command (e.g., INSERT, UPDATE) and returns the status."""
        return await self._connection.execute(query, *args)


class AsyncSessionContextManager:
    """
    Async context manager for acquiring and releasing a connection from the pool.
    """

    def __init__(self, pool: Pool):
        self._pool = pool
        self._connection: asyncpg.Connection | None = None

    async def __aenter__(self) -> Session:
        """Acquires a connection from the pool and returns a Session object."""
        self._connection = await self._pool.acquire()
        return Session(self._connection)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Releases the connection back to the pool."""
        if self._connection:
            await self._pool.release(self._connection)


class Database:
    """
    Manages the connection pool and provides session contexts.
    """

    _pool: Pool | None = None

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    async def setup(self) -> None:
        """
        Creates the connection pool. This should be called on application startup.
        """
        if self._pool:
            return
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.dsn, min_size=5, max_size=20
            )
            print("Database connection pool created successfully.")
        except Exception as e:
            print(f"Error creating database connection pool: {e}")
            raise

    def session(self) -> AsyncSessionContextManager:
        """
        Provides a session context manager for database interactions.

        Usage:
            async with db.session() as s:
                await s.fetch(...)
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
            print("Database connection pool closed.")


DB_DSN = os.environ.get("DATABASE_URL", "")
db = Database(dsn=DB_DSN)
