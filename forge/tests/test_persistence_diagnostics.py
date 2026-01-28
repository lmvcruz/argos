"""
Tests for warning and error data persistence (Step 6.4).

This module tests the save_warnings() and save_errors() methods that store
detailed diagnostic information with foreign key relationships to builds.
"""

from datetime import datetime

import pytest

from models.metadata import BuildMetadata, BuildTarget, BuildWarning, Error
from models.results import BuildResult
from storage.data_persistence import DataPersistence


@pytest.fixture
def persistence(tmp_path):
    """Create a DataPersistence instance with temporary database."""
    db_path = tmp_path / "test.db"
    persistence = DataPersistence(db_path)
    return persistence


def create_sample_build(persistence):
    """Helper to create and save a build, return build_id."""
    result = BuildResult(
        success=True,
        exit_code=0,
        duration=5.2,
        stdout="Build output",
        stderr="",
        start_time=datetime(2024, 1, 15, 14, 32, 0),
        end_time=datetime(2024, 1, 15, 14, 37, 12),
    )

    metadata = BuildMetadata(
        project_name="TestProject",
        targets=[BuildTarget(name="app", target_type="executable")],
        warnings=[],
        errors=[],
    )

    build_id = persistence.save_build(result, metadata, None)
    return build_id


class TestSaveSingleWarning:
    """Test saving a single warning to the database."""

    def test_save_single_warning_returns_count(self, persistence):
        """Test that save_warnings returns the count of saved warnings."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="main.cpp",
                line=42,
                column=10,
                message="unused variable 'x'",
                warning_type="unused-variable",
            )
        ]

        count = persistence.save_warnings(build_id, warnings)

        assert count == 1

    def test_save_warning_with_complete_information(self, persistence):
        """Test that all warning fields are persisted correctly."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="src/utils.cpp",
                line=100,
                column=5,
                message="implicit conversion from 'double' to 'int'",
                warning_type="conversion",
            )
        ]

        persistence.save_warnings(build_id, warnings)

        # Verify data in database
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT file, line, column, message, warning_type FROM warnings WHERE build_id = ?",
            (build_id,),
        ).fetchone()

        assert row is not None
        assert row[0] == "src/utils.cpp"
        assert row[1] == 100
        assert row[2] == 5
        assert row[3] == "implicit conversion from 'double' to 'int'"
        assert row[4] == "conversion"

    def test_save_warning_with_build_id_association(self, persistence):
        """Test that warning is correctly associated with build_id."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="test.cpp",
                line=1,
                column=1,
                message="test warning",
                warning_type="test",
            )
        ]

        persistence.save_warnings(build_id, warnings)

        # Verify foreign key relationship
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT build_id FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert row is not None
        assert row[0] == build_id


class TestSaveMultipleWarnings:
    """Test bulk insertion of multiple warnings."""

    def test_save_multiple_warnings_bulk_insert(self, persistence):
        """Test that multiple warnings are inserted efficiently."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file=f"file{i}.cpp",
                line=i * 10,
                column=5,
                message=f"warning message {i}",
                warning_type="test-warning",
            )
            for i in range(10)
        ]

        count = persistence.save_warnings(build_id, warnings)

        assert count == 10

        # Verify all warnings in database
        cursor = persistence._connection.cursor()
        rows = cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert rows[0] == 10

    def test_save_large_warning_list(self, persistence):
        """Test handling of very large warning lists (1000+)."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file=f"module{i % 100}.cpp",
                line=(i % 500) + 1,
                column=(i % 80) + 1,
                message=f"warning {i}",
                warning_type="bulk-test",
            )
            for i in range(1500)
        ]

        count = persistence.save_warnings(build_id, warnings)

        assert count == 1500

        # Verify count in database
        cursor = persistence._connection.cursor()
        rows = cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert rows[0] == 1500

    def test_save_warnings_preserves_order(self, persistence):
        """Test that warnings are saved in the order provided."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="file.cpp", line=i, column=1, message=f"warning {i}", warning_type="test"
            )
            for i in [50, 10, 100, 5, 75]
        ]

        persistence.save_warnings(build_id, warnings)

        # Retrieve warnings in insertion order
        cursor = persistence._connection.cursor()
        rows = cursor.execute(
            "SELECT line FROM warnings WHERE build_id = ? ORDER BY id", (build_id,)
        ).fetchall()

        line_numbers = [row[0] for row in rows]
        assert line_numbers == [50, 10, 100, 5, 75]


class TestSaveWarningsWithPartialInformation:
    """Test saving warnings with some optional fields missing."""

    def test_save_warning_with_missing_warning_type(self, persistence):
        """Test saving warning when warning_type is None."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="main.cpp",
                line=10,
                column=5,
                message="some warning",
                warning_type=None,
            )
        ]

        count = persistence.save_warnings(build_id, warnings)

        assert count == 1

        # Verify NULL in database
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT warning_type FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert row[0] is None

    def test_save_warning_with_long_message(self, persistence):
        """Test saving warning with very long message."""
        build_id = create_sample_build(persistence)

        long_message = "x" * 5000  # Very long message

        warnings = [
            BuildWarning(
                file="test.cpp",
                line=1,
                column=1,
                message=long_message,
                warning_type="test",
            )
        ]

        count = persistence.save_warnings(build_id, warnings)

        assert count == 1

        # Verify message stored correctly
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT message FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert row[0] == long_message


class TestSaveErrors:
    """Test saving error records to the database."""

    def test_save_single_error(self, persistence):
        """Test saving a single error returns correct count."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file="main.cpp",
                line=25,
                column=10,
                message="expected ';' before '}' token",
                error_type="syntax",
                error_code="C2143",
            )
        ]

        count = persistence.save_errors(build_id, errors)

        assert count == 1

    def test_save_error_with_complete_information(self, persistence):
        """Test that all error fields are persisted correctly."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file="src/core.cpp",
                line=150,
                column=20,
                message="undefined reference to 'foo()'",
                error_type="linker",
                error_code="LNK2019",
            )
        ]

        persistence.save_errors(build_id, errors)

        # Verify data in database
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT file, line, column, message, error_type FROM errors WHERE build_id = ?",
            (build_id,),
        ).fetchone()

        assert row is not None
        assert row[0] == "src/core.cpp"
        assert row[1] == 150
        assert row[2] == 20
        assert row[3] == "undefined reference to 'foo()'"
        assert row[4] == "linker"

    def test_save_multiple_errors(self, persistence):
        """Test bulk insertion of multiple errors."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file=f"error{i}.cpp",
                line=i,
                column=1,
                message=f"error {i}",
                error_type="compile",
                error_code=f"E{i:04d}",
            )
            for i in range(20)
        ]

        count = persistence.save_errors(build_id, errors)

        assert count == 20

        # Verify all errors in database
        cursor = persistence._connection.cursor()
        rows = cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert rows[0] == 20

    def test_save_error_with_missing_optional_fields(self, persistence):
        """Test saving error with None values for optional fields."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file="test.cpp",
                line=1,
                column=1,
                message="generic error",
                error_type=None,
                error_code=None,
            )
        ]

        count = persistence.save_errors(build_id, errors)

        assert count == 1

        # Verify NULL values in database
        cursor = persistence._connection.cursor()
        row = cursor.execute(
            "SELECT error_type FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()

        assert row[0] is None


class TestForeignKeyRelationships:
    """Test foreign key relationships between diagnostics and builds."""

    def test_warnings_reference_valid_build(self, persistence):
        """Test that warnings must reference an existing build."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="test.cpp",
                line=1,
                column=1,
                message="test",
                warning_type="test",
            )
        ]

        # Should succeed with valid build_id
        count = persistence.save_warnings(build_id, warnings)
        assert count == 1

    def test_warnings_invalid_build_id_raises_error(self, persistence):
        """Test that saving warnings with invalid build_id raises error."""
        warnings = [
            BuildWarning(
                file="test.cpp",
                line=1,
                column=1,
                message="test",
                warning_type="test",
            )
        ]

        # Should raise error with non-existent build_id
        with pytest.raises(RuntimeError, match="Failed to save warnings"):
            persistence.save_warnings(99999, warnings)

    def test_errors_reference_valid_build(self, persistence):
        """Test that errors must reference an existing build."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file="test.cpp",
                line=1,
                column=1,
                message="test error",
                error_type="test",
                error_code="T001",
            )
        ]

        # Should succeed with valid build_id
        count = persistence.save_errors(build_id, errors)
        assert count == 1

    def test_errors_invalid_build_id_raises_error(self, persistence):
        """Test that saving errors with invalid build_id raises error."""
        errors = [
            Error(
                file="test.cpp",
                line=1,
                column=1,
                message="test error",
                error_type="test",
                error_code="T001",
            )
        ]

        # Should raise error with non-existent build_id
        with pytest.raises(RuntimeError, match="Failed to save errors"):
            persistence.save_errors(99999, errors)


class TestCascadeDelete:
    """Test cascade delete behavior when build is deleted."""

    def test_warnings_cascade_delete(self, persistence):
        """Test that warnings are deleted when build is deleted."""
        build_id = create_sample_build(persistence)

        warnings = [
            BuildWarning(
                file="test.cpp",
                line=i,
                column=1,
                message=f"warning {i}",
                warning_type="test",
            )
            for i in range(5)
        ]

        persistence.save_warnings(build_id, warnings)

        # Verify warnings exist
        cursor = persistence._connection.cursor()
        count_before = cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert count_before == 5

        # Delete the build
        cursor.execute("DELETE FROM builds WHERE id = ?", (build_id,))
        persistence._connection.commit()

        # Verify warnings are also deleted
        count_after = cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert count_after == 0

    def test_errors_cascade_delete(self, persistence):
        """Test that errors are deleted when build is deleted."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file="test.cpp",
                line=i,
                column=1,
                message=f"error {i}",
                error_type="test",
                error_code=f"E{i}",
            )
            for i in range(3)
        ]

        persistence.save_errors(build_id, errors)

        # Verify errors exist
        cursor = persistence._connection.cursor()
        count_before = cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert count_before == 3

        # Delete the build
        cursor.execute("DELETE FROM builds WHERE id = ?", (build_id,))
        persistence._connection.commit()

        # Verify errors are also deleted
        count_after = cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert count_after == 0


class TestTransactionHandling:
    """Test transaction management for bulk operations."""

    def test_warnings_transaction_rollback_on_error(self, persistence):
        """Test that transaction is rolled back if warning insertion fails."""
        _ = create_sample_build(persistence)

        # Create a warning with invalid data that will cause constraint violation
        # This is tricky because BuildWarning validates at creation time
        # Instead, we'll test by trying to save to a non-existent build_id

        warnings = [
            BuildWarning(
                file="test.cpp",
                line=1,
                column=1,
                message="test",
                warning_type="test",
            )
        ]

        # Should raise error and not save anything
        with pytest.raises(RuntimeError):
            persistence.save_warnings(99999, warnings)

        # Verify no warnings were saved
        cursor = persistence._connection.cursor()
        count = cursor.execute("SELECT COUNT(*) FROM warnings").fetchone()[0]
        assert count == 0

    def test_errors_transaction_commit_on_success(self, persistence):
        """Test that transaction is committed when all errors save successfully."""
        build_id = create_sample_build(persistence)

        errors = [
            Error(
                file=f"file{i}.cpp",
                line=i,
                column=1,
                message=f"error {i}",
                error_type="test",
                error_code=f"E{i}",
            )
            for i in range(10)
        ]

        count = persistence.save_errors(build_id, errors)
        assert count == 10

        # Close and reopen database to verify commit
        persistence.close()
        persistence2 = DataPersistence(persistence._db_path)

        cursor = persistence2._connection.cursor()
        saved_count = cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()[0]

        assert saved_count == 10


class TestEmptyDiagnosticLists:
    """Test handling of empty warning/error lists."""

    def test_save_empty_warnings_list(self, persistence):
        """Test that saving empty warnings list returns 0."""
        build_id = create_sample_build(persistence)

        count = persistence.save_warnings(build_id, [])

        assert count == 0

        # Verify no warnings in database
        cursor = persistence._connection.cursor()
        db_count = cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert db_count == 0

    def test_save_empty_errors_list(self, persistence):
        """Test that saving empty errors list returns 0."""
        build_id = create_sample_build(persistence)

        count = persistence.save_errors(build_id, [])

        assert count == 0

        # Verify no errors in database
        cursor = persistence._connection.cursor()
        db_count = cursor.execute(
            "SELECT COUNT(*) FROM errors WHERE build_id = ?", (build_id,)
        ).fetchone()[0]
        assert db_count == 0


class TestMultipleBuildsDiagnostics:
    """Test that multiple builds can have their own warnings/errors."""

    def test_warnings_for_different_builds(self, persistence):
        """Test that warnings are correctly associated with different builds."""
        build_id1 = create_sample_build(persistence)
        build_id2 = create_sample_build(persistence)

        warnings1 = [
            BuildWarning(
                file="build1.cpp",
                line=10,
                column=1,
                message="warning from build 1",
                warning_type="test",
            )
        ]

        warnings2 = [
            BuildWarning(
                file="build2.cpp",
                line=20,
                column=1,
                message="warning from build 2",
                warning_type="test",
            )
        ]

        persistence.save_warnings(build_id1, warnings1)
        persistence.save_warnings(build_id2, warnings2)

        # Verify each build has its own warnings
        cursor = persistence._connection.cursor()

        row1 = cursor.execute(
            "SELECT file FROM warnings WHERE build_id = ?", (build_id1,)
        ).fetchone()
        assert row1[0] == "build1.cpp"

        row2 = cursor.execute(
            "SELECT file FROM warnings WHERE build_id = ?", (build_id2,)
        ).fetchone()
        assert row2[0] == "build2.cpp"

    def test_errors_for_different_builds(self, persistence):
        """Test that errors are correctly associated with different builds."""
        build_id1 = create_sample_build(persistence)
        build_id2 = create_sample_build(persistence)

        errors1 = [
            Error(
                file="build1.cpp",
                line=5,
                column=1,
                message="error from build 1",
                error_type="test",
                error_code="E1",
            )
        ]

        errors2 = [
            Error(
                file="build2.cpp",
                line=15,
                column=1,
                message="error from build 2",
                error_type="test",
                error_code="E2",
            )
        ]

        persistence.save_errors(build_id1, errors1)
        persistence.save_errors(build_id2, errors2)

        # Verify each build has its own errors
        cursor = persistence._connection.cursor()

        row1 = cursor.execute("SELECT file FROM errors WHERE build_id = ?", (build_id1,)).fetchone()
        assert row1[0] == "build1.cpp"

        row2 = cursor.execute("SELECT file FROM errors WHERE build_id = ?", (build_id2,)).fetchone()
        assert row2[0] == "build2.cpp"
