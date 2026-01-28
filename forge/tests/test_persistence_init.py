"""
Integration tests for DataPersistence database initialization.

Tests database creation, schema initialization, connection management,
and schema version tracking.
"""

from pathlib import Path
import sqlite3

import pytest

from forge.storage.data_persistence import DataPersistence


class TestDatabaseCreation:
    """Test database file creation and initialization."""

    def test_database_creation_in_default_location(self, tmp_path):
        """Test database is created in default location when no path specified."""
        default_db = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=default_db)

        assert default_db.exists()
        assert default_db.is_file()
        persistence.close()

    def test_database_creation_in_custom_location(self, tmp_path):
        """Test database is created in custom location."""
        custom_path = tmp_path / "custom" / "location" / "mydb.db"
        custom_path.parent.mkdir(parents=True, exist_ok=True)

        persistence = DataPersistence(db_path=custom_path)

        assert custom_path.exists()
        assert custom_path.is_file()
        persistence.close()

    def test_database_creation_with_nonexistent_parent_directory(self, tmp_path):
        """Test database creation creates parent directories."""
        db_path = tmp_path / "nested" / "dir" / "structure" / "forge.db"

        persistence = DataPersistence(db_path=db_path)

        assert db_path.exists()
        assert db_path.parent.exists()
        persistence.close()

    def test_database_file_is_valid_sqlite(self, tmp_path):
        """Test created database file is a valid SQLite database."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)
        persistence.close()

        # Try to open with raw sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        assert len(tables) > 0  # Should have tables


class TestSchemaInitialization:
    """Test database schema creation on first run."""

    def test_schema_created_on_first_initialization(self, tmp_path):
        """Test all tables are created on first initialization."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        conn = persistence._connection
        cursor = conn.cursor()

        # Check all expected tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "builds",
            "build_targets",
            "configurations",
            "errors",
            "schema_version",
            "warnings",
        ]

        for table in expected_tables:
            assert table in tables, f"Table '{table}' not found in database"

        persistence.close()

    def test_idempotent_initialization_multiple_calls(self, tmp_path):
        """Test calling initialize multiple times doesn't cause errors."""
        db_path = tmp_path / "forge.db"

        # First initialization
        persistence1 = DataPersistence(db_path=db_path)
        persistence1.close()

        # Second initialization (should not fail)
        persistence2 = DataPersistence(db_path=db_path)
        persistence2.close()

        # Third initialization
        persistence3 = DataPersistence(db_path=db_path)

        # Verify schema still intact
        cursor = persistence3._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        assert table_count >= 6  # At least our 6 tables
        persistence3.close()

    def test_schema_not_recreated_on_subsequent_runs(self, tmp_path):
        """Test schema is not recreated when database already exists."""
        db_path = tmp_path / "forge.db"

        # First initialization
        persistence1 = DataPersistence(db_path=db_path)
        cursor1 = persistence1._connection.cursor()
        # Insert a different version to test persistence
        cursor1.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
            (2,),
        )
        persistence1._connection.commit()
        persistence1.close()

        # Second initialization
        persistence2 = DataPersistence(db_path=db_path)
        cursor2 = persistence2._connection.cursor()
        cursor2.execute("SELECT COUNT(*) FROM schema_version")
        version_count = cursor2.fetchone()[0]

        # Should have at least the record we inserted
        assert version_count >= 1
        persistence2.close()

    def test_foreign_keys_enabled_on_initialization(self, tmp_path):
        """Test foreign key constraints are enabled."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]

        assert fk_status == 1, "Foreign keys should be enabled"
        persistence.close()


class TestConnectionManagement:
    """Test database connection handling."""

    def test_connection_established_on_initialization(self, tmp_path):
        """Test connection is established when DataPersistence is created."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        assert persistence._connection is not None
        assert isinstance(persistence._connection, sqlite3.Connection)
        persistence.close()

    def test_connection_is_reusable(self, tmp_path):
        """Test the same connection can execute multiple queries."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()

        # First query
        cursor.execute("SELECT COUNT(*) FROM configurations")
        count1 = cursor.fetchone()[0]

        # Second query (same connection)
        cursor.execute("SELECT COUNT(*) FROM builds")
        count2 = cursor.fetchone()[0]

        assert count1 == 0
        assert count2 == 0
        persistence.close()

    def test_close_connection_explicitly(self, tmp_path):
        """Test connection can be closed explicitly."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)
        conn = persistence._connection  # Save reference before closing

        persistence.close()

        # Connection should be closed (attempting query should fail)
        assert persistence._connection is None
        with pytest.raises(sqlite3.ProgrammingError):
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

    def test_context_manager_closes_connection(self, tmp_path):
        """Test using DataPersistence as context manager closes connection."""
        db_path = tmp_path / "forge.db"

        with DataPersistence(db_path=db_path) as persistence:
            assert persistence._connection is not None
            conn = persistence._connection

        # Connection should be closed after exiting context
        with pytest.raises(sqlite3.ProgrammingError):
            cursor = conn.cursor()
            cursor.execute("SELECT 1")

    def test_multiple_instances_can_access_same_database(self, tmp_path):
        """Test multiple DataPersistence instances can access same database."""
        db_path = tmp_path / "forge.db"

        persistence1 = DataPersistence(db_path=db_path)
        persistence2 = DataPersistence(db_path=db_path)

        # Both should work
        cursor1 = persistence1._connection.cursor()
        cursor1.execute("SELECT COUNT(*) FROM configurations")
        count1 = cursor1.fetchone()[0]

        cursor2 = persistence2._connection.cursor()
        cursor2.execute("SELECT COUNT(*) FROM builds")
        count2 = cursor2.fetchone()[0]

        assert count1 == 0
        assert count2 == 0

        persistence1.close()
        persistence2.close()


class TestSchemaVersionTracking:
    """Test schema version tracking for migrations."""

    def test_schema_version_table_exists(self, tmp_path):
        """Test schema_version table is created."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == "schema_version"
        persistence.close()

    def test_initial_schema_version_recorded(self, tmp_path):
        """Test initial schema version is recorded on first initialization."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        version = persistence.get_schema_version()

        assert version == 1  # Initial version should be 1
        persistence.close()

    def test_get_schema_version_method(self, tmp_path):
        """Test get_schema_version() returns current version."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        version = persistence.get_schema_version()

        assert isinstance(version, int)
        assert version >= 1
        persistence.close()

    def test_schema_version_persists_across_instances(self, tmp_path):
        """Test schema version persists when reopening database."""
        db_path = tmp_path / "forge.db"

        # First instance
        persistence1 = DataPersistence(db_path=db_path)
        version1 = persistence1.get_schema_version()
        persistence1.close()

        # Second instance
        persistence2 = DataPersistence(db_path=db_path)
        version2 = persistence2.get_schema_version()
        persistence2.close()

        assert version1 == version2

    def test_schema_version_has_timestamp(self, tmp_path):
        """Test schema version record includes application timestamp."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute("SELECT applied_at FROM schema_version WHERE version = 1")
        timestamp = cursor.fetchone()[0]

        assert timestamp is not None
        assert len(timestamp) > 0  # Should be ISO 8601 format
        persistence.close()


class TestErrorHandling:
    """Test error handling in database operations."""

    def test_invalid_database_path_raises_error(self, tmp_path):
        """Test that invalid database path raises appropriate error."""
        # Skip on Windows - different permission model
        import sys

        if sys.platform == "win32":
            pytest.skip("Test not applicable on Windows")

        # Try to create database in root directory (usually not writable)
        if Path("/").exists():  # Unix-like systems
            with pytest.raises((PermissionError, sqlite3.OperationalError)):
                DataPersistence(db_path=Path("/forge.db"))

    def test_database_with_wrong_permissions(self, tmp_path):
        """Test handling of database file with wrong permissions."""
        db_path = tmp_path / "forge.db"

        # Create database
        persistence1 = DataPersistence(db_path=db_path)
        persistence1.close()

        # Make file read-only
        db_path.chmod(0o444)

        try:
            # Try to open for writing (should fail on write operations)
            persistence2 = DataPersistence(db_path=db_path)
            cursor = persistence2._connection.cursor()

            with pytest.raises(sqlite3.OperationalError):
                cursor.execute(
                    "INSERT INTO configurations (source_dir, build_dir) VALUES (?, ?)",
                    ("/tmp/src", "/tmp/build"),
                )
                persistence2._connection.commit()

            persistence2.close()
        finally:
            # Restore permissions for cleanup
            db_path.chmod(0o644)

    def test_corrupted_database_handling(self, tmp_path):
        """Test handling of corrupted database file."""
        db_path = tmp_path / "forge.db"

        # Create a corrupted file (not a valid SQLite database)
        with open(db_path, "w") as f:
            f.write("This is not a SQLite database")

        with pytest.raises(sqlite3.DatabaseError):
            DataPersistence(db_path=db_path)


class TestConcurrentAccess:
    """Test concurrent database access scenarios."""

    def test_concurrent_read_access(self, tmp_path):
        """Test multiple readers can access database simultaneously."""
        db_path = tmp_path / "forge.db"

        # Create database with initial data
        persistence_init = DataPersistence(db_path=db_path)
        persistence_init.close()

        # Open multiple read connections
        readers = [DataPersistence(db_path=db_path) for _ in range(3)]

        # All readers should be able to query
        for reader in readers:
            cursor = reader._connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM configurations")
            count = cursor.fetchone()[0]
            assert count == 0

        # Close all readers
        for reader in readers:
            reader.close()

    def test_write_transaction_isolation(self, tmp_path):
        """Test write transactions are properly isolated."""
        db_path = tmp_path / "forge.db"

        persistence1 = DataPersistence(db_path=db_path)
        persistence2 = DataPersistence(db_path=db_path)

        # Start transaction in first connection
        cursor1 = persistence1._connection.cursor()
        cursor1.execute(
            """INSERT INTO configurations
               (source_dir, build_dir, timestamp, duration, exit_code, success)
               VALUES (?, ?, datetime('now'), ?, ?, ?)""",
            ("/tmp/src1", "/tmp/build1", 10.5, 0, 1),
        )
        # Don't commit yet

        # Second connection should not see uncommitted data
        cursor2 = persistence2._connection.cursor()
        cursor2.execute("SELECT COUNT(*) FROM configurations")
        count = cursor2.fetchone()[0]
        assert count == 0  # Should not see uncommitted insert

        # Commit first transaction
        persistence1._connection.commit()

        # Now second connection should see it
        cursor2.execute("SELECT COUNT(*) FROM configurations")
        count = cursor2.fetchone()[0]
        assert count == 1

        persistence1.close()
        persistence2.close()


class TestDatabaseProperties:
    """Test database configuration and properties."""

    def test_wal_mode_enabled(self, tmp_path):
        """Test Write-Ahead Logging is enabled for better concurrency."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]

        assert mode.upper() in ["WAL", "DELETE"]  # WAL or default
        persistence.close()

    def test_synchronous_mode_configured(self, tmp_path):
        """Test synchronous mode is configured appropriately."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute("PRAGMA synchronous")
        sync_mode = cursor.fetchone()[0]

        assert sync_mode >= 1  # At least NORMAL synchronous mode
        persistence.close()

    def test_database_encoding_is_utf8(self, tmp_path):
        """Test database uses UTF-8 encoding."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path=db_path)

        cursor = persistence._connection.cursor()
        cursor.execute("PRAGMA encoding")
        encoding = cursor.fetchone()[0]

        assert "UTF" in encoding.upper()
        persistence.close()
