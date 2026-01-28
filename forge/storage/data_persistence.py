"""
Data persistence layer for Forge build data.

Handles database initialization, connection management, schema version
tracking, and provides interface for storing and retrieving build data.
"""

import sqlite3
from pathlib import Path
from typing import Optional


class DataPersistence:
    """
    Manages data persistence for Forge build information.

    Provides database initialization, connection management, and schema
    version tracking. Uses SQLite for local storage with support for
    concurrent access and transaction management.

    Args:
        db_path: Path to SQLite database file. Parent directories will be
                 created if they don't exist.

    Examples:
        >>> persistence = DataPersistence(Path("forge.db"))
        >>> version = persistence.get_schema_version()
        >>> persistence.close()

        Using as context manager:
        >>> with DataPersistence(Path("forge.db")) as persistence:
        ...     version = persistence.get_schema_version()
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize DataPersistence with database at specified path.

        Creates parent directories if needed and initializes database
        schema on first run.

        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            db_path = Path.home() / ".forge" / "forge.db"

        self._db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None

        # Create parent directories if they don't exist
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database and establish connection
        self._initialize_database()

    def _initialize_database(self) -> None:
        """
        Initialize database schema and establish connection.

        Creates all required tables if database is new, enables foreign
        keys, configures WAL mode for better concurrency, and records
        initial schema version.
        """
        # Establish connection for this instance
        self._connection = sqlite3.connect(
            self._db_path,
            check_same_thread=False,  # Allow multi-threaded access
            timeout=30.0,  # Wait up to 30 seconds for locks
        )

        # Configure connection
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = NORMAL")

        # Create schema if not exists
        self._create_schema()

        # Record initial schema version if not exists
        self._ensure_schema_version()

    def _create_schema(self) -> None:
        """
        Create database schema if it doesn't exist.

        Reads schema from schema.sql and executes it. This operation
        is idempotent - it can be called multiple times safely.
        """
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        self._connection.executescript(schema_sql)

    def _ensure_schema_version(self) -> None:
        """
        Ensure schema_version table exists and has initial record.

        Creates schema_version table if it doesn't exist and inserts
        initial version record (version 1) if table is empty.
        """
        cursor = self._connection.cursor()

        # Create schema_version table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)

        # Check if version table is empty
        cursor.execute("SELECT COUNT(*) FROM schema_version")
        count = cursor.fetchone()[0]

        if count == 0:
            # Insert initial version
            cursor.execute("""
                INSERT INTO schema_version (version, applied_at)
                VALUES (1, datetime('now'))
            """)
            self._connection.commit()

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Current schema version number. Returns 1 for initial schema.

        Examples:
            >>> persistence = DataPersistence(Path("forge.db"))
            >>> version = persistence.get_schema_version()
            >>> print(version)
            1
        """
        cursor = self._connection.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()

        if result is None or result[0] is None:
            return 1  # Default to version 1 if no records

        return result[0]

    def close(self) -> None:
        """
        Close database connection.

        Should be called when done using the DataPersistence instance
        to ensure proper cleanup of database resources.

        Examples:
            >>> persistence = DataPersistence(Path("forge.db"))
            >>> # ... use persistence ...
            >>> persistence.close()
        """
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        """
        Enter context manager.

        Returns:
            Self for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager and close connection.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Returns:
            False to propagate any exception.
        """
        self.close()
        return False
