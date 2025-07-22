"""
This module handles all database interactions for the FCC Physics Events API.
"""

import json
from typing import Any

import asyncpg
from asyncpg import Connection, Pool

from app.fcc_dict_parser import FccDictParser


class Storage:
    """A class to handle database interactions."""

    def __init__(self):
        self._pool: Pool | None = None

    async def setup(self, db_config: dict[str, Any]):
        """Set up the database connection pool."""
        self._pool = await asyncpg.create_pool(
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["name"],
            host=db_config["host"],
            port=db_config["port"],
        )

    async def aclose(self):
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()

    @property
    def pool(self) -> Pool:
        """Get the database connection pool."""
        if not self._pool:
            raise RuntimeError("Database pool is not initialized. Call setup() first.")
        return self._pool

    async def session(self) -> Connection:
        """Get a database connection from the pool."""
        return await self.pool.acquire()

    async def import_fcc_dict(self, contents: bytes):
        """Import an FCC dictionary into the database."""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                parser = FccDictParser(connection)
                await parser.process(json.loads(contents))

    async def perform_search(
        self,
        count_query: str,
        search_query: str,
        search_query_params: list[Any],
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Perform a search query."""
        async with self.pool.acquire() as connection:
            total_count = await connection.fetchval(count_query, *search_query_params)
            results = await connection.fetch(
                search_query, *search_query_params, limit, offset
            )
            return {"total": total_count, "items": [dict(row) for row in results]}

    async def get_entities_by_ids(self, entity_ids: list[int]) -> list[dict[str, Any]]:
        """Get entities by their IDs."""
        async with self.pool.acquire() as connection:
            # This query needs to be adapted to the actual schema
            query = "SELECT * FROM datasets WHERE id = ANY($1)"
            rows = await connection.fetch(query, entity_ids)
            return [dict(row) for row in rows]

    async def get_entity_by_id(self, entity_id: int) -> dict[str, Any] | None:
        """Get a single entity by its ID."""
        async with self.pool.acquire() as connection:
            # This query needs to be adapted to the actual schema
            query = "SELECT * FROM datasets WHERE id = $1"
            row = await connection.fetchrow(query, entity_id)
            return dict(row) if row else None

    async def get_sorting_fields(self) -> dict[str, Any]:
        """Get available fields for sorting."""
        # This should be adapted to return fields from the main table and metadata
        return {"fields": ["last_edited_at", "name"]}

    async def update_entity(
        self, entity_id: int, update_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an entity."""
        async with self.pool.acquire() as connection:
            # This needs to be adapted to a dynamic update query
            # For now, let's assume a simple update
            query = "UPDATE datasets SET metadata = metadata || $1 WHERE id = $2 RETURNING *"
            updated_row = await connection.fetchrow(query, update_dict, entity_id)
            if not updated_row:
                raise ValueError(f"Entity with ID {entity_id} not found")
            return dict(updated_row)
