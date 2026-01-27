"""
Integration tests for database schema creation and validation.

Tests database schema creation, structure validation, and constraints.
"""

import sqlite3

import pytest

from forge.storage.persistence import DataPersistence


class TestDatabaseCreation:
    """Test database creation and initialization."""

    def test_database_creation_in_temporary_location(self, tmp_path):
        """Test database can be created in a temporary location."""
        db_path = tmp_path / "test_forge.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()

        assert db_path.exists()
        assert db_path.is_file()

    def test_database_creation_in_default_location(self, tmp_path):
        """Test database creation with custom location."""
        db_path = tmp_path / "forge.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()

        assert db_path.exists()

        # Clean up connection
        persistence.close()

    def test_database_connection_established(self, tmp_path):
        """Test that database connection is established."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()

        # Should be able to execute a query
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

    def test_idempotent_initialization(self, tmp_path):
        """Test database creation is idempotent (can run multiple times)."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        # Initialize multiple times
        persistence.initialize_database()
        persistence.initialize_database()
        persistence.initialize_database()

        # Should still work without errors
        assert db_path.exists()
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) >= 5  # At least 5 main tables


class TestTableStructure:
    """Test that all tables are created with correct structure."""

    @pytest.fixture
    def persistence(self, tmp_path):
        """Create a persistence instance with initialized database."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()
        return persistence

    def test_all_tables_created(self, persistence):
        """Test that all required tables are created."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "build_targets",
            "builds",
            "configurations",
            "errors",
            "warnings",
        ]
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"

    def test_configurations_table_columns(self, persistence):
        """Test configurations table has correct columns."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(configurations)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "timestamp": "TEXT",
            "project_name": "TEXT",
            "source_dir": "TEXT",
            "build_dir": "TEXT",
            "cmake_version": "TEXT",
            "generator": "TEXT",
            "compiler_c": "TEXT",
            "compiler_cxx": "TEXT",
            "build_type": "TEXT",
            "system_name": "TEXT",
            "system_processor": "TEXT",
            "cmake_args": "TEXT",
            "environment_vars": "TEXT",
            "duration": "REAL",
            "exit_code": "INTEGER",
            "success": "INTEGER",
            "stdout": "TEXT",
            "stderr": "TEXT",
            "configuration_options": "TEXT",
            "found_packages": "TEXT",
            "created_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found"
            assert columns[col_name] == col_type, f"Column {col_name} has wrong type"

    def test_builds_table_columns(self, persistence):
        """Test builds table has correct columns."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(builds)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "configuration_id": "INTEGER",
            "timestamp": "TEXT",
            "project_name": "TEXT",
            "build_dir": "TEXT",
            "build_args": "TEXT",
            "duration": "REAL",
            "exit_code": "INTEGER",
            "success": "INTEGER",
            "stdout": "TEXT",
            "stderr": "TEXT",
            "warnings_count": "INTEGER",
            "errors_count": "INTEGER",
            "targets_built": "TEXT",
            "total_files_compiled": "INTEGER",
            "parallel_jobs": "INTEGER",
            "created_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found"

    def test_warnings_table_columns(self, persistence):
        """Test warnings table has correct columns."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(warnings)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "build_id": "INTEGER",
            "file": "TEXT",
            "line": "INTEGER",
            "column": "INTEGER",
            "message": "TEXT",
            "warning_type": "TEXT",
            "created_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found"

    def test_errors_table_columns(self, persistence):
        """Test errors table has correct columns."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(errors)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "build_id": "INTEGER",
            "file": "TEXT",
            "line": "INTEGER",
            "column": "INTEGER",
            "message": "TEXT",
            "error_type": "TEXT",
            "created_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found"

    def test_build_targets_table_columns(self, persistence):
        """Test build_targets table has correct columns."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(build_targets)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "build_id": "INTEGER",
            "target_name": "TEXT",
            "target_type": "TEXT",
            "build_order": "INTEGER",
            "created_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} not found"


class TestIndexes:
    """Test that all indexes are created."""

    @pytest.fixture
    def persistence(self, tmp_path):
        """Create a persistence instance with initialized database."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()
        return persistence

    def test_all_indexes_created(self, persistence):
        """Test that all required indexes are created."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            "idx_configurations_project",
            "idx_configurations_timestamp",
            "idx_configurations_success",
            "idx_builds_project",
            "idx_builds_timestamp",
            "idx_builds_success",
            "idx_builds_config",
            "idx_warnings_build",
            "idx_warnings_file",
            "idx_warnings_type",
            "idx_errors_build",
            "idx_errors_file",
            "idx_errors_type",
            "idx_targets_build",
            "idx_targets_name",
        ]

        for index in expected_indexes:
            assert index in indexes, f"Index {index} not found"


class TestConstraints:
    """Test foreign key constraints and default values."""

    @pytest.fixture
    def persistence(self, tmp_path):
        """Create a persistence instance with initialized database."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()
        return persistence

    def test_foreign_key_constraints_enabled(self, persistence):
        """Test that foreign key constraints are enabled."""
        conn = persistence.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1, "Foreign keys not enabled"

    def test_builds_foreign_key_to_configurations(self, persistence):
        """Test foreign key from builds to configurations."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Insert a configuration
        cursor.execute(
            """
            INSERT INTO configurations
            (timestamp, source_dir, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("2026-01-27T10:00:00", "/src", "/build", 1.0, 0, 1),
        )
        config_id = cursor.lastrowid

        # Insert a build referencing the configuration
        cursor.execute(
            """
            INSERT INTO builds
            (configuration_id, timestamp, project_name, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (config_id, "2026-01-27T10:01:00", "Test", "/build", 2.0, 0, 1),
        )

        # Should succeed
        conn.commit()

    def test_builds_foreign_key_constraint_enforced(self, persistence):
        """Test that invalid foreign key is rejected."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Try to insert a build with non-existent configuration_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO builds
                (configuration_id, timestamp, project_name, build_dir, duration, exit_code, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (99999, "2026-01-27T10:01:00", "Test", "/build", 2.0, 0, 1),
            )
            conn.commit()

    def test_warnings_foreign_key_cascade_delete(self, persistence):
        """Test cascade delete from builds to warnings."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Insert configuration and build
        cursor.execute(
            """
            INSERT INTO configurations
            (timestamp, source_dir, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("2026-01-27T10:00:00", "/src", "/build", 1.0, 0, 1),
        )
        config_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO builds
            (configuration_id, timestamp, project_name, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (config_id, "2026-01-27T10:01:00", "Test", "/build", 2.0, 0, 1),
        )
        build_id = cursor.lastrowid

        # Insert a warning
        cursor.execute(
            """
            INSERT INTO warnings (build_id, message)
            VALUES (?, ?)
        """,
            (build_id, "Test warning"),
        )
        conn.commit()

        # Verify warning exists
        cursor.execute("SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,))
        assert cursor.fetchone()[0] == 1

        # Delete the build
        cursor.execute("DELETE FROM builds WHERE id = ?", (build_id,))
        conn.commit()

        # Warning should be deleted due to CASCADE
        cursor.execute("SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,))
        assert cursor.fetchone()[0] == 0

    def test_errors_foreign_key_cascade_delete(self, persistence):
        """Test cascade delete from builds to errors."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Insert configuration and build
        cursor.execute(
            """
            INSERT INTO configurations
            (timestamp, source_dir, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("2026-01-27T10:00:00", "/src", "/build", 1.0, 0, 1),
        )
        config_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO builds
            (configuration_id, timestamp, project_name, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (config_id, "2026-01-27T10:01:00", "Test", "/build", 2.0, 0, 1),
        )
        build_id = cursor.lastrowid

        # Insert an error
        cursor.execute(
            """
            INSERT INTO errors (build_id, message)
            VALUES (?, ?)
        """,
            (build_id, "Test error"),
        )
        conn.commit()

        # Verify error exists
        cursor.execute("SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,))
        assert cursor.fetchone()[0] == 1

        # Delete the build
        cursor.execute("DELETE FROM builds WHERE id = ?", (build_id,))
        conn.commit()

        # Error should be deleted due to CASCADE
        cursor.execute("SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,))
        assert cursor.fetchone()[0] == 0

    def test_default_values_set_correctly(self, persistence):
        """Test that default values are set correctly."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Insert configuration without created_at
        cursor.execute(
            """
            INSERT INTO configurations
            (timestamp, source_dir, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("2026-01-27T10:00:00", "/src", "/build", 1.0, 0, 1),
        )
        config_id = cursor.lastrowid
        conn.commit()

        # Check that created_at has a default value
        cursor.execute(
            "SELECT created_at FROM configurations WHERE id = ?", (config_id,)
        )
        created_at = cursor.fetchone()[0]
        assert created_at is not None
        assert len(created_at) > 0

    def test_builds_default_warning_error_counts(self, persistence):
        """Test that builds table has default values for warning/error counts."""
        conn = persistence.get_connection()
        cursor = conn.cursor()

        # Insert configuration
        cursor.execute(
            """
            INSERT INTO configurations
            (timestamp, source_dir, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            ("2026-01-27T10:00:00", "/src", "/build", 1.0, 0, 1),
        )
        config_id = cursor.lastrowid

        # Insert build without specifying warning/error counts
        cursor.execute(
            """
            INSERT INTO builds
            (configuration_id, timestamp, project_name, build_dir, duration, exit_code, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (config_id, "2026-01-27T10:01:00", "Test", "/build", 2.0, 0, 1),
        )
        build_id = cursor.lastrowid
        conn.commit()

        # Check default values
        cursor.execute(
            "SELECT warnings_count, errors_count FROM builds WHERE id = ?",
            (build_id,),
        )
        warnings_count, errors_count = cursor.fetchone()
        assert warnings_count == 0
        assert errors_count == 0


class TestConnectionManagement:
    """Test database connection management."""

    def test_connection_reuse(self, tmp_path):
        """Test that connections are reused."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()

        conn1 = persistence.get_connection()
        conn2 = persistence.get_connection()

        # Should return the same connection object
        assert conn1 is conn2

    def test_close_connection(self, tmp_path):
        """Test that connections can be closed."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)
        persistence.initialize_database()

        persistence.close()

        # After close, getting connection should create a new one
        conn = persistence.get_connection()
        assert conn is not None
