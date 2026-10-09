"""Versioned SQLite foundation; monitoring state is never persisted here."""

import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA_VERSION = 1


class StorageError(RuntimeError):
    """Local storage is inaccessible, invalid, or from an unsupported version."""


def initialize_database(path: Path) -> None:
    """Initialize metadata without resetting existing tables or user data."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Explicit transaction control makes schema creation atomic too.
        with closing(sqlite3.connect(path, timeout=1, isolation_level=None)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS schema_metadata (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        version INTEGER NOT NULL CHECK (version > 0)
                    )
                """)
                row = connection.execute(
                    "SELECT version FROM schema_metadata WHERE id = 1"
                ).fetchone()
                if row is None:
                    connection.execute(
                        "INSERT INTO schema_metadata (id, version) VALUES (1, ?)",
                        (SCHEMA_VERSION,),
                    )
                elif row[0] != SCHEMA_VERSION:
                    raise StorageError("Unsupported database schema version.")
                # Legacy monitoring_settings is preserved but never read or written.
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
    except (OSError, sqlite3.Error) as error:
        raise StorageError("Local database initialization failed.") from error
