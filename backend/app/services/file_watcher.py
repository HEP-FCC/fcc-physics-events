"""
File watcher service for monitoring directories and processing FCC dictionary files.

This service monitors specified directories for JSON file changes and automatically
imports them into the database using the existing FCC dict import functionality.
"""

import asyncio
import os
from pathlib import Path
from typing import Any

from watchfiles import Change, awatch

from app.storage.database import Database
from app.utils import get_config, get_logger

logger = get_logger()


class FileWatcherService:
    """
    File watcher service that monitors directories for JSON file changes
    and automatically imports them into the database.
    """

    def __init__(self, database: Database) -> None:
        """Initialize the file watcher service."""
        self.database = database
        self.config = get_config()
        self.is_running = False
        self._watch_task: asyncio.Task[None] | None = None

        # Load configuration
        watcher_config = self.config.get("file_watcher", {})
        self.enabled = watcher_config.get("enabled", True)
        self.watch_paths = watcher_config.get("watch_paths", ["/data"])
        self.file_extensions = watcher_config.get("file_extensions", [".json"])
        self.recursive = watcher_config.get("recursive", True)
        self.debounce_delay = watcher_config.get("debounce_delay", 2)

        # Handle case where watch_paths comes from config as a string representation of a list
        if isinstance(self.watch_paths, str):
            # If it looks like a JSON array, try to parse it
            if self.watch_paths.startswith("[") and self.watch_paths.endswith("]"):
                import json

                try:
                    self.watch_paths = json.loads(self.watch_paths)
                except json.JSONDecodeError:
                    # Fall back to treating it as a single path
                    self.watch_paths = [self.watch_paths]
            else:
                # Split by comma or treat as single path
                if "," in self.watch_paths:
                    self.watch_paths = [
                        path.strip() for path in self.watch_paths.split(",")
                    ]
                else:
                    self.watch_paths = [self.watch_paths]

        # Ensure watch_paths is a list and strip any whitespace/control characters
        if not isinstance(self.watch_paths, list):
            self.watch_paths = [str(self.watch_paths)]
        self.watch_paths = [path.strip() for path in self.watch_paths]

        # Handle case where file_extensions comes from config as a string representation of a list
        if isinstance(self.file_extensions, str):
            # If it looks like a JSON array, try to parse it
            if self.file_extensions.startswith("[") and self.file_extensions.endswith(
                "]"
            ):
                import json

                try:
                    self.file_extensions = json.loads(self.file_extensions)
                except json.JSONDecodeError:
                    # Fall back to treating it as a single extension
                    self.file_extensions = [self.file_extensions]
            else:
                # Split by comma or treat as single extension
                if "," in self.file_extensions:
                    self.file_extensions = [
                        ext.strip() for ext in self.file_extensions.split(",")
                    ]
                else:
                    self.file_extensions = [self.file_extensions]

        # Ensure file_extensions is a list and strip any whitespace/control characters
        if not isinstance(self.file_extensions, list):
            self.file_extensions = [str(self.file_extensions)]
        self.file_extensions = [ext.strip() for ext in self.file_extensions]

        # Normalize file extensions to lowercase
        self.file_extensions = [ext.lower() for ext in self.file_extensions]

        # Track pending files to implement debouncing
        self._pending_files: dict[str, asyncio.Task[None]] = {}

    async def start(self) -> None:
        """Start the file watcher service."""
        if not self.enabled:
            logger.info("File watcher service is disabled")
            return

        if self.is_running:
            logger.warning("File watcher service is already running")
            return

        # Log configured paths but don't validate immediately
        logger.info(f"File watcher configured to monitor: {self.watch_paths}")
        logger.info(
            f"File extensions: {self.file_extensions}, recursive: {self.recursive}"
        )

        self.is_running = True

        # Start the watcher task (it will validate paths when it starts)
        self._watch_task = asyncio.create_task(self._watch_files())

    async def stop(self) -> None:
        """Stop the file watcher service."""
        if not self.is_running:
            return

        logger.info("Stopping file watcher service")
        self.is_running = False

        # Cancel the watch task
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass

        # Cancel any pending file processing tasks
        for task in self._pending_files.values():
            task.cancel()

        if self._pending_files:
            await asyncio.gather(*self._pending_files.values(), return_exceptions=True)

        self._pending_files.clear()
        logger.info("File watcher service stopped")

    async def _watch_files(self) -> None:
        """Main watch loop for monitoring file changes."""
        retry_count = 0
        max_retries = 5
        retry_delay = 10  # seconds

        while self.is_running and retry_count < max_retries:
            try:
                # Validate watch paths before starting watcher
                valid_paths = []
                for path in self.watch_paths:
                    if os.path.exists(path) and os.path.isdir(path):
                        valid_paths.append(path)
                        logger.info(f"File watcher monitoring: {path}")
                    else:
                        logger.warning(f"Watch path not available: {path}")

                if not valid_paths:
                    retry_count += 1
                    logger.warning(
                        f"No valid watch paths found (attempt {retry_count}/{max_retries}). "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                # Reset retry count on successful path validation
                retry_count = 0

                logger.info(f"Starting file monitoring for paths: {valid_paths}")

                # Start watching the valid paths
                async for changes in awatch(*valid_paths, recursive=self.recursive):
                    if not self.is_running:
                        break

                    for change, file_path in changes:
                        await self._handle_file_change(change, file_path)

            except asyncio.CancelledError:
                logger.info("File watcher task cancelled")
                raise
            except Exception as e:
                retry_count += 1
                logger.error(
                    f"File watcher encountered an error (attempt {retry_count}/{max_retries}): {e}"
                )
                if retry_count >= max_retries:
                    logger.error("File watcher failed after maximum retries")
                    break

                if self.is_running:
                    logger.info(f"Restarting file watcher in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)

        if retry_count >= max_retries:
            logger.error("File watcher service stopped due to repeated failures")
            self.is_running = False

    async def _handle_file_change(self, change: Change, file_path: str) -> None:
        """Handle a single file change event."""
        try:
            # Only process added and modified files
            if change not in (Change.added, Change.modified):
                return

            # Check if it's a file (not directory)
            if not os.path.isfile(file_path):
                return

            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.file_extensions:
                return

            logger.debug(f"File change detected: {change.name} - {file_path}")

            # Cancel any existing pending task for this file
            if file_path in self._pending_files:
                self._pending_files[file_path].cancel()

            # Schedule debounced processing
            self._pending_files[file_path] = asyncio.create_task(
                self._process_file_with_delay(file_path)
            )

        except Exception as e:
            logger.error(f"Error handling file change for {file_path}: {e}")

    async def _process_file_with_delay(self, file_path: str) -> None:
        """Process a file after a debounce delay."""
        try:
            # Wait for debounce delay
            await asyncio.sleep(self.debounce_delay)

            # Process the file
            await self._process_file(file_path)

        except asyncio.CancelledError:
            # Task was cancelled (probably due to another change to the same file)
            logger.debug(f"File processing cancelled for {file_path}")

        finally:
            # Clean up from pending files
            self._pending_files.pop(file_path, None)

    async def _process_file(self, file_path: str) -> None:
        """Process a single file by importing it into the database."""
        try:
            logger.info(f"Processing file: {file_path}")

            # Check if file still exists and is readable
            if not os.path.isfile(file_path):
                logger.warning(f"File no longer exists: {file_path}")
                return

            # Read file content
            try:
                with open(file_path, "rb") as file:
                    content = file.read()
            except Exception as e:
                logger.error(f"Failed to read file {file_path}: {e}")
                return

            # Validate that it's not empty
            if not content.strip():
                logger.warning(f"File is empty: {file_path}")
                return

            # Import the file content
            try:
                await self.database.import_fcc_dict(content)
                logger.info(f"Successfully imported FCC dictionary from: {file_path}")

            except Exception as e:
                logger.error(f"Failed to import FCC dictionary from {file_path}: {e}")

        except Exception as e:
            logger.error(f"Unexpected error processing file {file_path}: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get the current status of the file watcher service."""
        # Check which paths are currently accessible
        valid_paths = []
        invalid_paths = []
        for path in self.watch_paths:
            if os.path.exists(path) and os.path.isdir(path):
                valid_paths.append(path)
            else:
                invalid_paths.append(path)

        return {
            "enabled": self.enabled,
            "running": self.is_running,
            "watch_paths": self.watch_paths,
            "valid_paths": valid_paths,
            "invalid_paths": invalid_paths,
            "file_extensions": self.file_extensions,
            "recursive": self.recursive,
            "debounce_delay": self.debounce_delay,
            "pending_files": len(self._pending_files),
        }
