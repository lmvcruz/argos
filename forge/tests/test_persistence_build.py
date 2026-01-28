"""
Tests for build data persistence in the Forge database.

This module tests the save_build() method that stores BuildResult
and BuildMetadata to the database with proper foreign key relationships
to configuration records.
"""

from datetime import datetime
import json
import sqlite3

import pytest

from forge.models.metadata import (
    BuildMetadata,
    BuildTarget,
    BuildWarning,
    ConfigureMetadata,
    Error,
)
from forge.models.results import BuildResult, ConfigureResult
from forge.storage.data_persistence import DataPersistence


def create_sample_configuration(persistence):
    """
    Create and save a sample configuration record.

    Returns the configuration_id for use in build tests.
    """
    result = ConfigureResult(
        success=True,
        exit_code=0,
        duration=1.5,
        stdout="CMake configured successfully",
        stderr="",
        start_time=datetime(2024, 1, 15, 14, 30, 45),
        end_time=datetime(2024, 1, 15, 14, 31, 15),
    )

    metadata = ConfigureMetadata(
        project_name="TestProject",
        cmake_version="3.28.1",
        generator="Ninja",
        system_name="Linux",
        system_processor="x86_64",
    )

    return persistence.save_configuration(result, metadata)


def create_sample_build_result(**overrides):
    """Create a sample BuildResult with default values."""
    defaults = {
        "success": True,
        "exit_code": 0,
        "duration": 5.2,
        "stdout": "Build completed successfully",
        "stderr": "",
        "start_time": datetime(2024, 1, 15, 14, 32, 0),
        "end_time": datetime(2024, 1, 15, 14, 37, 12),
    }
    defaults.update(overrides)
    return BuildResult(**defaults)


def create_sample_build_metadata(**overrides):
    """Create a sample BuildMetadata with default values."""
    defaults = {
        "project_name": "TestProject",
        "targets": [
            BuildTarget(name="app", target_type="executable"),
            BuildTarget(name="libcore", target_type="static_library"),
        ],
        "warnings": [
            BuildWarning(
                file="src/main.cpp",
                line=42,
                column=10,
                message="unused variable 'x'",
                warning_type="unused-variable",
            )
        ],
        "errors": [],
    }
    defaults.update(overrides)
    return BuildMetadata(**defaults)


class TestSaveCompleteBuild:
    """Test saving BuildResult with all fields."""

    def test_save_build_returns_id(self, tmp_path):
        """Test that save_build() returns a build ID."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        assert isinstance(build_id, int)
        assert build_id > 0

    def test_save_build_with_all_fields(self, tmp_path):
        """Test that all BuildResult fields are persisted."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        # Verify all fields in database
        cursor = persistence._connection.cursor()
        row = cursor.execute("SELECT * FROM builds WHERE id = ?", (build_id,)).fetchone()

        assert row is not None
        # Verify key fields (index based on schema.sql)
        assert row[1] == config_id  # configuration_id
        assert row[6] == 5.2  # duration
        assert row[7] == 0  # exit_code
        assert row[8] == 1  # success (as INTEGER)
        assert "Build completed successfully" in row[9]  # stdout
        assert row[10] == ""  # stderr

    def test_save_build_persists_metadata_fields(self, tmp_path):
        """Test that BuildMetadata fields are persisted correctly."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        # Verify metadata fields
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT targets_built, warnings_count, errors_count FROM builds WHERE id = ?",
            (build_id,),
        ).fetchone()

        targets_json = json.loads(row[0])
        assert len(targets_json) == 2
        assert targets_json[0]["name"] == "app"
        assert targets_json[0]["target_type"] == "executable"
        assert row[1] == 1  # warning_count
        assert row[2] == 0  # error_count


class TestConfigurationAssociation:
    """Test foreign key relationship with configurations."""

    def test_save_build_with_configuration_id(self, tmp_path):
        """Test that build is associated with configuration."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        # Verify foreign key relationship
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT configuration_id FROM builds WHERE id = ?", (build_id,)
        ).fetchone()

        assert row[0] == config_id

    def test_save_build_without_configuration(self, tmp_path):
        """Test saving build without configuration (build-only mode)."""
        persistence = DataPersistence(tmp_path / "test.db")

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        # Save without configuration_id (None)
        build_id = persistence.save_build(result, metadata, None)

        # Verify build is saved with NULL configuration_id
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT configuration_id FROM builds WHERE id = ?", (build_id,)
        ).fetchone()

        assert row[0] is None

    def test_multiple_builds_per_configuration(self, tmp_path):
        """Test that one configuration can have multiple builds."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result1 = create_sample_build_result()
        metadata1 = create_sample_build_metadata()

        result2 = create_sample_build_result(
            start_time=datetime(2024, 1, 15, 15, 0, 0),
            end_time=datetime(2024, 1, 15, 15, 5, 0),
        )
        metadata2 = create_sample_build_metadata()

        build_id1 = persistence.save_build(result1, metadata1, config_id)
        build_id2 = persistence.save_build(result2, metadata2, config_id)

        assert build_id1 != build_id2

        # Verify both builds reference same configuration
        cursor = persistence._connection.cursor()
        rows = cursor.execute(
            "SELECT id FROM builds WHERE configuration_id = ?", (config_id,)
        ).fetchall()

        assert len(rows) == 2


class TestTargetsSerialization:
    """Test JSON serialization of build targets."""

    def test_targets_list_serialized_as_json(self, tmp_path):
        """Test that targets list is stored as JSON."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata(
            targets=[
                BuildTarget(name="app", target_type="executable"),
                BuildTarget(name="libmath", target_type="static_library"),
                BuildTarget(name="libutil.so", target_type="shared_library"),
            ]
        )

        build_id = persistence.save_build(result, metadata, config_id)

        # Verify JSON structure
        cursor = persistence._connection.cursor()
        targets_json = cursor.execute(
            "SELECT targets_built FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        targets = json.loads(targets_json)
        assert len(targets) == 3
        assert targets[0]["name"] == "app"
        assert targets[1]["name"] == "libmath"
        assert targets[2]["name"] == "libutil.so"
        assert targets[0]["target_type"] == "executable"

    def test_empty_targets_list(self, tmp_path):
        """Test handling of empty targets list."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata(targets=[])

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        targets_json = cursor.execute(
            "SELECT targets_built FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        targets = json.loads(targets_json)
        assert targets == []


class TestTimestampFormatting:
    """Test timestamp storage and formatting."""

    def test_build_time_is_iso8601_format(self, tmp_path):
        """Test that timestamp is stored in ISO 8601 format."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        start_time = datetime(2024, 1, 15, 14, 32, 0)
        result = create_sample_build_result(
            start_time=start_time,
            end_time=datetime(2024, 1, 15, 14, 37, 12),
        )
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        timestamp = cursor.execute(
            "SELECT timestamp FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        # Verify ISO 8601 format
        assert timestamp == "2024-01-15T14:32:00"

    def test_timestamp_roundtrip(self, tmp_path):
        """Test that timestamp can be parsed back to datetime."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        original_time = datetime(2024, 1, 15, 14, 32, 0)
        result = create_sample_build_result(start_time=original_time)
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        timestamp = cursor.execute(
            "SELECT timestamp FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        parsed_time = datetime.fromisoformat(timestamp)
        assert parsed_time == original_time


class TestWarningErrorCounts:
    """Test warning and error count storage."""

    def test_warning_count_stored(self, tmp_path):
        """Test that warning count is calculated and stored."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata(
            warnings=[
                BuildWarning(
                    file="a.cpp", line=1, column=5, message="warning 1", warning_type="unused"
                ),
                BuildWarning(
                    file="b.cpp", line=2, column=5, message="warning 2", warning_type="unused"
                ),
                BuildWarning(
                    file="c.cpp", line=3, column=5, message="warning 3", warning_type="unused"
                ),
            ]
        )

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        count = cursor.execute(
            "SELECT warnings_count FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        assert count == 3

    def test_error_count_stored(self, tmp_path):
        """Test that error count is calculated and stored."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata(
            errors=[
                Error(file="x.cpp", line=10, column=5, message="error 1"),
                Error(file="y.cpp", line=20, column=5, message="error 2"),
            ]
        )

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        count = cursor.execute(
            "SELECT errors_count FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        assert count == 2

    def test_zero_warnings_and_errors(self, tmp_path):
        """Test handling of builds with no warnings or errors."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata(warnings=[], errors=[])

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT warnings_count, errors_count FROM builds WHERE id = ?", (build_id,)
        ).fetchone()

        assert row[0] == 0
        assert row[1] == 0


class TestTransactionHandling:
    """Test transaction management and error handling."""

    def test_transaction_rollback_on_error(self, tmp_path):
        """Test that transaction is rolled back on error."""
        persistence = DataPersistence(tmp_path / "test.db")

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        # Try to save with invalid configuration_id (should fail)
        with pytest.raises(Exception):
            persistence.save_build(result, metadata, 99999)

        # Verify no build was saved
        cursor = persistence._connection.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM builds").fetchone()[0]
        assert count == 0

    def test_successful_transaction_commit(self, tmp_path):
        """Test that successful save commits transaction."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        # Close and reopen database to verify commit
        persistence.close()
        persistence2 = DataPersistence(tmp_path / "test.db")

        cursor = persistence2._connection.cursor()
        row = cursor.execute("SELECT id FROM builds WHERE id = ?", (build_id,)).fetchone()

        assert row is not None
        assert row[0] == build_id


class TestDataIntegrityConstraints:
    """Test data integrity and constraints."""

    def test_success_flag_is_boolean(self, tmp_path):
        """Test that success flag is stored as INTEGER (0/1)."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        # Test with success=True
        result1 = create_sample_build_result(success=True)
        metadata1 = create_sample_build_metadata()
        build_id1 = persistence.save_build(result1, metadata1, config_id)

        # Test with success=False
        result2 = create_sample_build_result(success=False, exit_code=1)
        metadata2 = create_sample_build_metadata()
        build_id2 = persistence.save_build(result2, metadata2, config_id)

        cursor = persistence._connection.cursor()
        row1 = cursor.execute("SELECT success FROM builds WHERE id = ?", (build_id1,)).fetchone()
        row2 = cursor.execute("SELECT success FROM builds WHERE id = ?", (build_id2,)).fetchone()

        assert row1[0] == 1  # True as INTEGER
        assert row2[0] == 0  # False as INTEGER

    def test_duration_precision(self, tmp_path):
        """Test that duration is stored with decimal precision."""
        persistence = DataPersistence(tmp_path / "test.db")
        config_id = create_sample_configuration(persistence)

        result = create_sample_build_result(duration=123.456789)
        metadata = create_sample_build_metadata()

        build_id = persistence.save_build(result, metadata, config_id)

        cursor = persistence._connection.cursor()
        duration = cursor.execute(
            "SELECT duration FROM builds WHERE id = ?", (build_id,)
        ).fetchone()[0]

        assert abs(duration - 123.456789) < 0.000001


class TestForeignKeyRelationships:
    """Test foreign key constraints and cascading."""

    def test_foreign_key_constraint_enforced(self, tmp_path):
        """Test that invalid configuration_id raises error."""
        persistence = DataPersistence(tmp_path / "test.db")

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        # Should raise error for non-existent configuration_id
        with pytest.raises((sqlite3.IntegrityError, RuntimeError)):
            persistence.save_build(result, metadata, 99999)

    def test_null_configuration_id_allowed(self, tmp_path):
        """Test that NULL configuration_id is allowed (build-only mode)."""
        persistence = DataPersistence(tmp_path / "test.db")

        result = create_sample_build_result()
        metadata = create_sample_build_metadata()

        # Should not raise error
        build_id = persistence.save_build(result, metadata, None)
        assert build_id > 0
