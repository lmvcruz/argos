"""
Data persistence layer for Forge build data.

Handles database initialization, connection management, schema version
tracking, and provides interface for storing and retrieving build data.
"""

import json
from pathlib import Path
import sqlite3
from typing import Optional

from forge.models.metadata import BuildMetadata, ConfigureMetadata
from forge.models.results import BuildResult, ConfigureResult


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

    def save_build(
        self, result: BuildResult, metadata: BuildMetadata, configuration_id: Optional[int]
    ) -> int:
        """
        Save build result and metadata to database.

        Associates the build with a configuration if configuration_id is provided.
        For build-only mode (without configure), configuration_id can be None.

        Args:
            result: BuildResult containing execution details
            metadata: BuildMetadata containing extracted information
            configuration_id: ID of associated configuration, or None for build-only

        Returns:
            Build ID (primary key) for referencing in warnings/errors tables

        Raises:
            RuntimeError: If database operation fails

        Examples:
            >>> result = BuildResult(success=True, exit_code=0, duration=5.2, ...)
            >>> metadata = BuildMetadata(project_name="MyApp", targets=[...], ...)
            >>> build_id = persistence.save_build(result, metadata, config_id)
        """
        cursor = self._connection.cursor()

        # Serialize targets list to JSON
        targets_json = json.dumps([t.to_dict() for t in metadata.targets])

        # Calculate warning and error counts
        warning_count = len(metadata.warnings)
        error_count = len(metadata.errors)

        # Format timestamp as ISO 8601
        timestamp = result.start_time.isoformat()

        # Get project name from metadata
        project_name = metadata.project_name or "Unknown"

        try:
            cursor.execute(
                """
                INSERT INTO builds (
                    configuration_id, timestamp, project_name, build_dir,
                    build_args, duration, exit_code, success, stdout, stderr,
                    warnings_count, errors_count, targets_built,
                    total_files_compiled, parallel_jobs
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    configuration_id,
                    timestamp,
                    project_name,
                    "",  # build_dir - not in BuildResult/BuildMetadata
                    "",  # build_args - not in BuildResult/BuildMetadata
                    result.duration,
                    result.exit_code,
                    1 if result.success else 0,  # Boolean as INTEGER
                    result.stdout,
                    result.stderr,
                    warning_count,
                    error_count,
                    targets_json,
                    None,  # total_files_compiled - not tracked yet
                    None,  # parallel_jobs - not tracked yet
                ),
            )

            self._connection.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            self._connection.rollback()
            raise RuntimeError(f"Failed to save build: {e}") from e

    def save_warnings(self, build_id: int, warnings: list) -> int:
        """
        Save build warnings to database.

        Associates warnings with a specific build using build_id foreign key.
        Performs bulk insert for efficiency with large warning lists.

        Args:
            build_id: Build ID to associate warnings with (foreign key).
            warnings: List of BuildWarning objects to save.

        Returns:
            Number of warnings saved.

        Raises:
            RuntimeError: If database operation fails (e.g., invalid build_id).

        Examples:
            >>> warnings = [BuildWarning(file="main.cpp", line=10, column=5, ...)]
            >>> count = persistence.save_warnings(build_id, warnings)
            >>> print(f"Saved {count} warnings")
        """
        if not warnings:
            return 0

        cursor = self._connection.cursor()

        try:
            # Prepare data for bulk insert
            warning_rows = [
                (
                    build_id,
                    w.file,
                    w.line,
                    w.column,
                    w.message,
                    w.warning_type,
                )
                for w in warnings
            ]

            # Bulk insert all warnings
            cursor.executemany(
                """
                INSERT INTO warnings (
                    build_id, file, line, column, message, warning_type
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                warning_rows,
            )

            self._connection.commit()
            return len(warnings)

        except sqlite3.Error as e:
            self._connection.rollback()
            raise RuntimeError(f"Failed to save warnings: {e}") from e

    def save_errors(self, build_id: int, errors: list) -> int:
        """
        Save build errors to database.

        Associates errors with a specific build using build_id foreign key.
        Performs bulk insert for efficiency with large error lists.

        Args:
            build_id: Build ID to associate errors with (foreign key).
            errors: List of Error objects to save.

        Returns:
            Number of errors saved.

        Raises:
            RuntimeError: If database operation fails (e.g., invalid build_id).

        Examples:
            >>> errors = [Error(file="core.cpp", line=50, column=10, ...)]
            >>> count = persistence.save_errors(build_id, errors)
            >>> print(f"Saved {count} errors")
        """
        if not errors:
            return 0

        cursor = self._connection.cursor()

        try:
            # Prepare data for bulk insert
            error_rows = [
                (
                    build_id,
                    e.file,
                    e.line,
                    e.column,
                    e.message,
                    e.error_type,
                )
                for e in errors
            ]

            # Bulk insert all errors
            cursor.executemany(
                """
                INSERT INTO errors (
                    build_id, file, line, column, message, error_type
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                error_rows,
            )

            self._connection.commit()
            return len(errors)

        except sqlite3.Error as e:
            self._connection.rollback()
            raise RuntimeError(f"Failed to save errors: {e}") from e

    def get_recent_builds(self, limit: int = 10, project_name: Optional[str] = None) -> list[dict]:
        """
        Retrieve recent builds ordered by timestamp (newest first).

        Args:
            limit: Maximum number of builds to return. Defaults to 10.
            project_name: Optional filter by project name. If None, returns
                         builds from all projects.

        Returns:
            List of dictionaries, each containing:
                - id: Build ID
                - project_name: Project name
                - success: Whether build succeeded
                - duration: Build duration in seconds
                - warning_count: Number of warnings
                - error_count: Number of errors
                - build_time: Build timestamp as ISO format string

        Examples:
            >>> persistence.get_recent_builds(limit=5)
            [{'id': 3, 'project_name': 'MyApp', 'success': True, ...}, ...]

            >>> persistence.get_recent_builds(project_name='MyApp')
            [{'id': 3, 'project_name': 'MyApp', ...}, ...]
        """
        try:
            cursor = self._connection.cursor()

            if project_name is None:
                query = """
                    SELECT id, project_name, success, duration,
                           warnings_count, errors_count, timestamp
                    FROM builds
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (limit,))
            else:
                query = """
                    SELECT id, project_name, success, duration,
                           warnings_count, errors_count, timestamp
                    FROM builds
                    WHERE project_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (project_name, limit))

            rows = cursor.fetchall()

            # Convert rows to list of dicts
            builds = []
            for row in rows:
                builds.append(
                    {
                        "id": row[0],
                        "project_name": row[1],
                        "success": bool(row[2]),
                        "duration": row[3],
                        "warning_count": row[4],
                        "error_count": row[5],
                        "build_time": row[6],
                    }
                )

            return builds

        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to retrieve recent builds: {e}") from e

    def get_build_statistics(self, project_name: Optional[str] = None) -> dict:
        """
        Calculate aggregated build statistics.

        Args:
            project_name: Optional filter by project name. If None, calculates
                         statistics across all projects.

        Returns:
            Dictionary containing:
                - total_builds: Total number of builds
                - successful_builds: Number of successful builds
                - failed_builds: Number of failed builds
                - success_rate: Success rate as percentage (0-100)
                - average_duration: Average build duration in seconds
                - total_warnings: Total number of warnings across all builds
                - total_errors: Total number of errors across all builds

        Examples:
            >>> persistence.get_build_statistics()
            {'total_builds': 10, 'successful_builds': 8, ...}

            >>> persistence.get_build_statistics(project_name='MyApp')
            {'total_builds': 5, 'successful_builds': 4, ...}
        """
        try:
            cursor = self._connection.cursor()

            if project_name is None:
                query = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        AVG(duration) as avg_duration,
                        SUM(warnings_count) as total_warnings,
                        SUM(errors_count) as total_errors
                    FROM builds
                """
                cursor.execute(query)
            else:
                query = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                        AVG(duration) as avg_duration,
                        SUM(warnings_count) as total_warnings,
                        SUM(errors_count) as total_errors
                    FROM builds
                    WHERE project_name = ?
                """
                cursor.execute(query, (project_name,))

            row = cursor.fetchone()

            total_builds = row[0] or 0
            successful_builds = row[1] or 0
            failed_builds = total_builds - successful_builds
            avg_duration = row[2] or 0.0
            total_warnings = row[3] or 0
            total_errors = row[4] or 0

            # Calculate success rate as percentage
            success_rate = (successful_builds / total_builds * 100.0) if total_builds > 0 else 0.0

            return {
                "total_builds": total_builds,
                "successful_builds": successful_builds,
                "failed_builds": failed_builds,
                "success_rate": round(success_rate, 2),
                "average_duration": round(avg_duration, 2),
                "total_warnings": total_warnings,
                "total_errors": total_errors,
            }

        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to calculate build statistics: {e}") from e

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
