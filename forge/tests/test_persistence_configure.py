"""
Tests for configuration data persistence in the Forge database.

This module tests the save_configuration() method that stores ConfigureResult
and ConfigureMetadata to the database with proper transaction handling.
"""

from datetime import datetime
import json
import sqlite3

import pytest

from forge.models.metadata import ConfigureMetadata
from forge.models.results import ConfigureResult
from forge.storage.data_persistence import DataPersistence


def create_sample_metadata(**overrides):
    """
    Create a sample ConfigureMetadata with all required fields.

    This helper provides default values for all required fields,
    allowing tests to override specific fields as needed.
    """
    defaults = {
        "project_name": "TestProject",
        "cmake_version": "3.28.1",
        "generator": "Ninja",
        "system_name": "Linux",
        "system_processor": "x86_64",
    }
    defaults.update(overrides)
    return ConfigureMetadata(**defaults)


def create_sample_result(**overrides):
    """Create a sample ConfigureResult with default values."""
    defaults = {
        "success": True,
        "exit_code": 0,
        "duration": 1.5,
        "stdout": "CMake configured successfully",
        "stderr": "",
        "start_time": datetime(2024, 1, 15, 14, 30, 45),
        "end_time": datetime(2024, 1, 15, 14, 31, 15),
    }
    defaults.update(overrides)
    return ConfigureResult(**defaults)


class TestSaveCompleteConfiguration:
    """Test saving complete ConfigureResult with all fields."""

    def test_save_configuration_returns_id(self, tmp_path):
        """Test that save_configuration returns a configuration ID."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()
        metadata = create_sample_metadata(build_type="Release")

        config_id = persistence.save_configuration(result, metadata)

        assert isinstance(config_id, int)
        assert config_id > 0

    def test_save_configuration_with_all_metadata_fields(self, tmp_path):
        """Test saving configuration with all metadata fields populated."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result(duration=2.3)
        metadata = create_sample_metadata(
            project_name="CompleteProject",
            build_type="Debug",
            compiler_c="/usr/bin/gcc",
            compiler_cxx="/usr/bin/g++",
            found_packages=["Boost", "OpenSSL", "CURL"],
        )

        config_id = persistence.save_configuration(result, metadata)

        # Verify data was saved by querying directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM configurations WHERE id = ?", (config_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[2] == "CompleteProject"  # project_name (column index 2)
        assert row[5] == "3.28.1"  # cmake_version (column index 5)
        assert row[6] == "Ninja"  # generator (column index 6)

    def test_save_configuration_persists_all_result_fields(self, tmp_path):
        """Test that all ConfigureResult fields are persisted correctly."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        start = datetime(2024, 1, 15, 10, 30, 0)
        end = datetime(2024, 1, 15, 10, 30, 2)

        result = create_sample_result(
            success=False,
            exit_code=1,
            duration=2.0,
            stdout="Configuration output",
            stderr="Configuration error",
            start_time=start,
            end_time=end,
        )
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        # Query database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT success, exit_code, stdout, stderr,
                   timestamp, duration
            FROM configurations
            WHERE id = ?
            """,
            (config_id,),
        )
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 0  # success (False = 0)
        assert row[1] == 1  # exit_code
        assert row[2] == "Configuration output"  # stdout
        assert row[3] == "Configuration error"  # stderr
        assert row[5] == pytest.approx(2.0, rel=0.1)  # duration


class TestJSONSerialization:
    """Test JSON serialization of complex fields."""

    def test_found_packages_serialized_as_json(self, tmp_path):
        """Test that found_packages list is stored as JSON."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        packages = ["Boost", "Qt5", "OpenCV", "Eigen3"]
        result = create_sample_result()
        metadata = create_sample_metadata(found_packages=packages)

        config_id = persistence.save_configuration(result, metadata)

        # Verify JSON serialization
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT found_packages FROM configurations WHERE id = ?",
            (config_id,),
        )
        found_packages_json = cursor.fetchone()[0]
        conn.close()

        assert found_packages_json is not None
        deserialized = json.loads(found_packages_json)
        assert deserialized == packages

    def test_empty_found_packages_list(self, tmp_path):
        """Test that empty found_packages list is handled correctly."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()
        metadata = create_sample_metadata(found_packages=[])

        config_id = persistence.save_configuration(result, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT found_packages FROM configurations WHERE id = ?",
            (config_id,),
        )
        found_packages_json = cursor.fetchone()[0]
        conn.close()

        deserialized = json.loads(found_packages_json)
        assert deserialized == []


class TestTimestampFormatting:
    """Test ISO 8601 timestamp formatting."""

    def test_configure_time_is_iso8601_format(self, tmp_path):
        """Test that configure_time is stored in ISO 8601 format."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        start_time = datetime(2024, 1, 15, 14, 30, 45, 123456)
        result = create_sample_result(start_time=start_time)
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp FROM configurations WHERE id = ?",
            (config_id,),
        )
        timestamp_str = cursor.fetchone()[0]
        conn.close()

        # Verify ISO 8601 format (YYYY-MM-DDTHH:MM:SS.ffffff)
        assert "T" in timestamp_str
        assert timestamp_str.startswith("2024-01-15T14:30:45")

    def test_timestamp_roundtrip(self, tmp_path):
        """Test that timestamp can be parsed back to datetime."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        original_time = datetime(2024, 6, 20, 9, 15, 30)
        result = create_sample_result(start_time=original_time)
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp FROM configurations WHERE id = ?",
            (config_id,),
        )
        timestamp_str = cursor.fetchone()[0]
        conn.close()

        # Parse back to datetime
        parsed_time = datetime.fromisoformat(timestamp_str)
        assert parsed_time.year == original_time.year
        assert parsed_time.month == original_time.month
        assert parsed_time.day == original_time.day
        assert parsed_time.hour == original_time.hour
        assert parsed_time.minute == original_time.minute
        assert parsed_time.second == original_time.second


class TestNullHandling:
    """Test NULL handling for optional fields."""

    def test_optional_metadata_fields_can_be_none(self, tmp_path):
        """Test that optional metadata fields can be None/NULL."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()

        # Create metadata with only required fields (optional fields are None)
        metadata = ConfigureMetadata(
            project_name="MinimalProject",
            cmake_version=None,
            generator=None,
            system_name=None,
            system_processor=None,
            build_type=None,
            compiler_c=None,
            compiler_cxx=None,
            found_packages=[],
        )

        config_id = persistence.save_configuration(result, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT cmake_version, generator, build_type,
                   compiler_c, compiler_cxx
            FROM configurations
            WHERE id = ?
            """,
            (config_id,),
        )
        row = cursor.fetchone()
        conn.close()

        # All optional fields should be NULL
        assert row[0] is None  # cmake_version
        assert row[1] is None  # generator
        assert row[2] is None  # build_type
        assert row[3] is None  # compiler_c
        assert row[4] is None  # compiler_cxx

    def test_stderr_can_be_empty_string(self, tmp_path):
        """Test that stderr can be empty string (not NULL)."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result(stderr="")  # Empty string, not None
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stderr FROM configurations WHERE id = ?",
            (config_id,),
        )
        stderr = cursor.fetchone()[0]
        conn.close()

        assert stderr == ""  # Empty string, not None


class TestForeignKeyPreparation:
    """Test that configuration ID can be used as foreign key."""

    def test_configuration_id_can_be_referenced(self, tmp_path):
        """Test that configuration_id can be used as foreign key for builds."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        # Try to insert a build record referencing this configuration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO builds (
                configuration_id, success, exit_code, project_name,
                build_dir, timestamp, duration, warnings_count, errors_count
            )
            VALUES (?, 1, 0, 'TestProject', '', datetime('now'), 5.0, 0, 0)
            """,
            (config_id,),
        )
        conn.commit()
        build_id = cursor.lastrowid
        conn.close()

        assert build_id > 0  # Build was successfully inserted

    def test_multiple_builds_can_reference_same_configuration(self, tmp_path):
        """Test that multiple builds can reference the same configuration."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()
        metadata = create_sample_metadata()

        config_id = persistence.save_configuration(result, metadata)

        # Insert multiple builds referencing this configuration
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for i in range(3):
            cursor.execute(
                """
                INSERT INTO builds (
                    configuration_id, success, exit_code, project_name,
                    build_dir, timestamp, duration, warnings_count, errors_count
                )
                VALUES (?, 1, 0, 'TestProject', '', datetime('now'), ?, 0, 0)
                """,
                (config_id, float(i + 1)),
            )

        conn.commit()

        # Verify all builds reference the same configuration
        cursor.execute("SELECT COUNT(*) FROM builds WHERE configuration_id = ?", (config_id,))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3


class TestDataIntegrityConstraints:
    """Test that data integrity constraints are enforced."""

    def test_success_flag_is_boolean(self, tmp_path):
        """Test that success flag is stored as 0 or 1."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        metadata = create_sample_metadata()

        # Test True
        result_true = create_sample_result(success=True)
        config_id_true = persistence.save_configuration(result_true, metadata)

        # Test False
        result_false = create_sample_result(success=False, exit_code=1)
        config_id_false = persistence.save_configuration(result_false, metadata)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT success FROM configurations WHERE id = ?",
            (config_id_true,),
        )
        success_true = cursor.fetchone()[0]

        cursor.execute(
            "SELECT success FROM configurations WHERE id = ?",
            (config_id_false,),
        )
        success_false = cursor.fetchone()[0]

        conn.close()

        assert success_true == 1  # True stored as 1
        assert success_false == 0  # False stored as 0


class TestDuplicateConfiguration:
    """Test handling of duplicate configuration data."""

    def test_same_configuration_can_be_saved_multiple_times(self, tmp_path):
        """Test that same configuration can be saved multiple times (separate records)."""
        db_path = tmp_path / "test.db"
        persistence = DataPersistence(db_path)

        result = create_sample_result()
        metadata = create_sample_metadata()

        # Save same configuration twice
        config_id1 = persistence.save_configuration(result, metadata)
        config_id2 = persistence.save_configuration(result, metadata)

        # Should get different IDs (separate records)
        assert config_id1 != config_id2
        assert config_id1 > 0
        assert config_id2 > 0

        # Verify both exist in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM configurations WHERE id IN (?, ?)",
            (config_id1, config_id2),
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2
