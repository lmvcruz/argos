"""
Data persistence layer for Forge build data.

Handles database initialization, connection management, schema version
tracking, and provides interface for storing and retrieving build data.
"""

import json
from pathlib import Path
import sqlite3
from typing import Optional

from forge.models.metadata import ConfigureMetadata
from forge.models.results import ConfigureResult


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

    def save_configuration(self, result: ConfigureResult, metadata: ConfigureMetadata) -> int:
        """
        Save configuration result and metadata to database.

        Stores complete configuration data including result status, timing
        information, and all metadata fields. Serializes complex fields like
        found_packages to JSON. Uses transactions for data integrity.

        Args:
            result: ConfigureResult with success status, exit code, and output
            metadata: ConfigureMetadata with project info and detected settings

        Returns:
            Configuration ID (primary key) for referencing in builds table

        Examples:
            >>> result = ConfigureResult(success=True, exit_code=0, ...)
            >>> metadata = ConfigureMetadata(project_name="MyApp", ...)
            >>> config_id = persistence.save_configuration(result, metadata)
            >>> print(f"Configuration saved with ID: {config_id}")
        """
        cursor = self._connection.cursor()

        # Serialize found_packages list to JSON
        found_packages_json = json.dumps(metadata.found_packages or [])

        # Serialize configuration_options to JSON
        config_options_json = json.dumps(metadata.configuration_options or {})

        # Format timestamp as ISO 8601
        timestamp = result.start_time.isoformat()

        try:
            cursor.execute(
                """
                INSERT INTO configurations (
                    timestamp, project_name, source_dir, build_dir,
                    cmake_version, generator, compiler_c, compiler_cxx,
                    build_type, system_name, system_processor,
                    cmake_args, environment_vars, duration, exit_code,
                    success, stdout, stderr, configuration_options,
                    found_packages
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    metadata.project_name,
                    "",  # source_dir - not in ConfigureMetadata
                    "",  # build_dir - not in ConfigureMetadata
                    metadata.cmake_version,
                    metadata.generator,
                    metadata.compiler_c,
                    metadata.compiler_cxx,
                    metadata.build_type,
                    metadata.system_name,
                    metadata.system_processor,
                    "",  # cmake_args - not in ConfigureMetadata
                    "",  # environment_vars - not in ConfigureMetadata
                    result.duration,
                    result.exit_code,
                    1 if result.success else 0,  # Boolean as INTEGER
                    result.stdout,
                    result.stderr,
                    config_options_json,
                    found_packages_json,
                ),
            )

            self._connection.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            self._connection.rollback()
            raise RuntimeError(f"Failed to save configuration: {e}") from e

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
            exc_type: Exception type (unused).
            exc_val: Exception value (unused).
            exc_tb: Exception traceback (unused).
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Returns:
            False to propagate any exception.
        """
        self.close()
        return False
