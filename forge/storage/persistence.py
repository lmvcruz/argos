"""
DataPersistence class for SQLite database operations.

Handles database initialization, connection management, and schema creation.
"""

from pathlib import Path
import sqlite3
from typing import Optional


class DataPersistence:
    """
    Manages SQLite database operations for Forge.

    Provides methods for database initialization, connection management,
    and schema creation with proper foreign key constraint enforcement.
    """

    def __init__(self, database_path: Optional[Path] = None):
        """
        Initialize DataPersistence with database path.

        Args:
            database_path: Path to SQLite database file.
                          If None, uses default location.
        """
        if database_path is None:
            database_path = Path.home() / ".forge" / "forge.db"

        self.database_path = Path(database_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._schema_initialized = False

    def initialize_database(self) -> None:
        """
        Initialize database and create schema.

        Creates all tables, indexes, and constraints if they don't exist.
        This operation is idempotent - it can be called multiple times safely.
        """
        # Ensure database directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Get connection (will create database file if it doesn't exist)
        conn = self.get_connection()

        # Read and execute schema SQL
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Execute schema creation
        conn.executescript(schema_sql)
        conn.commit()

        self._schema_initialized = True

    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with foreign keys enabled.

        Returns:
            SQLite connection object

        Note:
            Connection is cached and reused. Foreign key constraints
            are enabled for data integrity.
        """
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self.database_path),
                check_same_thread=False,
            )
            # Enable foreign key constraints
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.commit()

        return self._connection

    def close(self) -> None:
        """
        Close database connection.

        Commits any pending transactions and closes the connection.
        """
        if self._connection is not None:
            self._connection.commit()
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: vulture
        """Context manager exit - ensures connection is closed."""
        self.close()
        return False
