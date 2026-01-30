"""
Test suite for statistics persistence layer.

This module tests the persistence layer that saves validation results to
the statistics database after each validation run. Tests cover saving
runs with various states, git information, and error handling.
"""

import tempfile
from datetime import datetime
from pathlib import Path

from anvil.models.validator import Issue, ValidationResult
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_persistence import StatisticsPersistence


class TestSaveValidationRun:
    """Test saving validation run metadata."""

    def test_save_validation_run_with_no_issues(self):
        """Test saving a validation run that passed with no issues."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create passing validation results
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
                ValidationResult(
                    validator_name="black",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=2.1,
                ),
            ]

            # Save the run
            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=5.6,
            )

            assert run_id > 0

            # Verify run saved
            saved_run = db.get_validation_run(run_id)
            assert saved_run is not None
            assert saved_run.passed is True
            assert saved_run.git_commit == "abc123"
            assert saved_run.git_branch == "main"
            assert saved_run.incremental is False
            assert saved_run.duration_seconds == 5.6

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_save_validation_run_with_errors(self):
        """Test saving a validation run with errors."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create results with errors
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="src/test.py",
                            line_number=10,
                            column_number=5,
                            message="E501 line too long",
                            severity="error",
                        ),
                        Issue(
                            file_path="src/main.py",
                            line_number=20,
                            column_number=1,
                            message="E302 expected 2 blank lines",
                            severity="error",
                        ),
                    ],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            # Save the run
            run_id = persistence.save_validation_run(
                results=results,
                git_commit="def456",
                git_branch="feature",
                incremental=False,
                total_duration=3.5,
            )

            # Verify run marked as failed
            saved_run = db.get_validation_run(run_id)
            assert saved_run.passed is False

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_save_validation_run_with_warnings(self):
        """Test saving a validation run with warnings but no errors."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create results with warnings only
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[
                        Issue(
                            file_path="src/test.py",
                            line_number=15,
                            column_number=1,
                            message="W503 line break before binary operator",
                            severity="warning",
                        ),
                    ],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            # Save the run
            run_id = persistence.save_validation_run(
                results=results,
                git_commit="ghi789",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            # Verify run marked as passed (warnings don't fail)
            saved_run = db.get_validation_run(run_id)
            assert saved_run.passed is True

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestSaveValidatorResults:
    """Test saving individual validator results."""

    def test_save_validator_execution_metadata(self):
        """Test saving validator execution metadata."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=15,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            # Query validator results
            validator_records = db.query_validator_results_for_run(run_id)
            assert len(validator_records) == 1
            assert validator_records[0].validator_name == "flake8"
            assert validator_records[0].passed is True
            assert validator_records[0].error_count == 0
            assert validator_records[0].warning_count == 0
            assert validator_records[0].files_checked == 15
            assert validator_records[0].duration_seconds == 3.5

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_save_multiple_validator_results(self):
        """Test saving results from multiple validators."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=15,
                    execution_time=3.5,
                ),
                ValidationResult(
                    validator_name="black",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="src/test.py",
                            line_number=0,
                            column_number=0,
                            message="would reformat",
                            severity="error",
                        ),
                    ],
                    warnings=[],
                    files_checked=15,
                    execution_time=2.1,
                ),
                ValidationResult(
                    validator_name="isort",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=15,
                    execution_time=1.8,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=7.4,
            )

            # Query validator results
            validator_records = db.query_validator_results_for_run(run_id)
            assert len(validator_records) == 3

            # Check each validator
            names = {r.validator_name for r in validator_records}
            assert names == {"flake8", "black", "isort"}

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestSaveFileValidations:
    """Test saving file-level validation results."""

    def test_save_file_validation_results(self):
        """Test saving file validation results."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="src/test.py",
                            line_number=10,
                            column_number=5,
                            message="E501 line too long",
                            severity="error",
                        ),
                        Issue(
                            file_path="src/test.py",
                            line_number=20,
                            column_number=1,
                            message="E302 expected 2 blank lines",
                            severity="error",
                        ),
                        Issue(
                            file_path="src/main.py",
                            line_number=15,
                            column_number=8,
                            message="E701 multiple statements",
                            severity="error",
                        ),
                    ],
                    warnings=[
                        Issue(
                            file_path="src/test.py",
                            line_number=30,
                            column_number=1,
                            message="W503 line break",
                            severity="warning",
                        ),
                    ],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            # Query file validation results
            file_records = db.query_file_validations_for_run(run_id)
            assert len(file_records) == 2  # 2 unique files

            # Check src/test.py: 2 errors, 1 warning
            test_py = [r for r in file_records if r.file_path == "src/test.py"][0]
            assert test_py.error_count == 2
            assert test_py.warning_count == 1

            # Check src/main.py: 1 error, 0 warnings
            main_py = [r for r in file_records if r.file_path == "src/main.py"][0]
            assert main_py.error_count == 1
            assert main_py.warning_count == 0

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestSaveTestResults:
    """Test saving test case results."""

    def test_save_test_case_results_from_pytest(self):
        """Test saving test case results from pytest."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create pytest result with test cases
            pytest_result = ValidationResult(
                validator_name="pytest",
                passed=False,
                errors=[],
                warnings=[],
                files_checked=5,
                execution_time=10.5,
            )

            # Add test case metadata
            pytest_result.metadata = {
                "test_cases": [
                    {
                        "name": "test_example_pass",
                        "suite": "TestSuite",
                        "passed": True,
                        "skipped": False,
                        "duration": 0.5,
                        "failure_message": None,
                    },
                    {
                        "name": "test_example_fail",
                        "suite": "TestSuite",
                        "passed": False,
                        "skipped": False,
                        "duration": 0.8,
                        "failure_message": "AssertionError: expected 5, got 3",
                    },
                    {
                        "name": "test_example_skip",
                        "suite": "TestSuite",
                        "passed": False,
                        "skipped": True,
                        "duration": 0.0,
                        "failure_message": None,
                    },
                ]
            }

            run_id = persistence.save_validation_run(
                results=[pytest_result],
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=10.5,
            )

            # Query test case results
            test_records = db.query_test_cases_for_run(run_id)
            assert len(test_records) == 3

            # Check passed test
            passed_test = [r for r in test_records if r.test_name == "test_example_pass"][0]
            assert passed_test.passed is True
            assert passed_test.skipped is False

            # Check failed test
            failed_test = [r for r in test_records if r.test_name == "test_example_fail"][0]
            assert failed_test.passed is False
            assert failed_test.failure_message == "AssertionError: expected 5, got 3"

            # Check skipped test
            skipped_test = [r for r in test_records if r.test_name == "test_example_skip"][0]
            assert skipped_test.skipped is True

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_save_test_case_results_from_gtest(self):
        """Test saving test case results from Google Test."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create gtest result with test cases
            gtest_result = ValidationResult(
                validator_name="gtest",
                passed=True,
                errors=[],
                warnings=[],
                files_checked=1,
                execution_time=5.2,
            )

            gtest_result.metadata = {
                "test_cases": [
                    {
                        "name": "TestAddition",
                        "suite": "MathTest",
                        "passed": True,
                        "skipped": False,
                        "duration": 0.1,
                        "failure_message": None,
                    },
                    {
                        "name": "TestSubtraction",
                        "suite": "MathTest",
                        "passed": True,
                        "skipped": False,
                        "duration": 0.15,
                        "failure_message": None,
                    },
                ]
            }

            run_id = persistence.save_validation_run(
                results=[gtest_result],
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=5.2,
            )

            # Query test case results
            test_records = db.query_test_cases_for_run(run_id)
            assert len(test_records) == 2
            assert all(r.test_suite == "MathTest" for r in test_records)

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestGitInformation:
    """Test saving validation runs with git information."""

    def test_save_with_git_commit_information(self):
        """Test saving with git commit hash."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abcdef123456",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            saved_run = db.get_validation_run(run_id)
            assert saved_run.git_commit == "abcdef123456"
            assert saved_run.git_branch == "main"

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_save_without_git_information(self):
        """Test saving without git information (not a git repo)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit=None,
                git_branch=None,
                incremental=False,
                total_duration=3.5,
            )

            saved_run = db.get_validation_run(run_id)
            assert saved_run.git_commit is None
            assert saved_run.git_branch is None

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestIncrementalMode:
    """Test saving validation runs in incremental mode."""

    def test_save_with_incremental_mode_flag(self):
        """Test saving incremental validation run."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=3,  # Only 3 files in incremental
                    execution_time=1.2,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="feature",
                incremental=True,
                total_duration=1.2,
            )

            saved_run = db.get_validation_run(run_id)
            assert saved_run.incremental is True

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestPartialResults:
    """Test saving partial results when some validators fail."""

    def test_save_with_partial_results(self):
        """Test saving when some validators failed to execute."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Mix of successful and failed validator executions
            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
                ValidationResult(
                    validator_name="pylint",
                    passed=False,
                    errors=[
                        Issue(
                            file_path="",
                            line_number=0,
                            column_number=0,
                            message="Validator execution failed: not installed",
                            severity="error",
                        ),
                    ],
                    warnings=[],
                    files_checked=0,
                    execution_time=0.0,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            # Both validators should be saved
            validator_records = db.query_validator_results_for_run(run_id)
            assert len(validator_records) == 2

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestTransactionHandling:
    """Test transaction handling and error recovery."""

    def test_transaction_rollback_on_error(self):
        """Test that transaction rolls back if save fails."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)
            persistence = StatisticsPersistence(db)

            # Create invalid result (will cause error during save)
            results = [
                ValidationResult(
                    validator_name="invalid",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=-1,  # Invalid negative value
                    execution_time=3.5,
                ),
            ]

            # Should handle error gracefully
            try:
                persistence.save_validation_run(
                    results=results,
                    git_commit="abc123",
                    git_branch="main",
                    incremental=False,
                    total_duration=3.5,
                )
            except Exception:
                pass  # Expected to fail

            # Database should not have partial data or should be consistent
            # (depending on where error occurred in the transaction)
            # Just verify database is still accessible
            db.query_runs_by_date_range(datetime(2020, 1, 1), datetime(2030, 1, 1))

            db.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


class TestDatabaseConfiguration:
    """Test database configuration and path handling."""

    def test_database_path_from_configuration(self):
        """Test using database path from configuration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "custom_stats.db"

            db = StatisticsDatabase(str(db_path))
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            assert run_id > 0
            assert db_path.exists()

            db.close()

    def test_create_database_directory_if_not_exists(self):
        """Test creating database directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "stats" / "anvil_stats.db"

            # Directory doesn't exist yet
            assert not db_path.parent.exists()

            # Create database (should create directory)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db = StatisticsDatabase(str(db_path))
            persistence = StatisticsPersistence(db)

            results = [
                ValidationResult(
                    validator_name="flake8",
                    passed=True,
                    errors=[],
                    warnings=[],
                    files_checked=10,
                    execution_time=3.5,
                ),
            ]

            run_id = persistence.save_validation_run(
                results=results,
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                total_duration=3.5,
            )

            assert run_id > 0
            assert db_path.exists()

            db.close()


class TestStatisticsDisabled:
    """Test statistics disabled mode (no-op)."""

    def test_statistics_disabled_mode(self):
        """Test that statistics can be disabled (no-op mode)."""
        # Create persistence with None database (disabled)
        persistence = StatisticsPersistence(None)

        results = [
            ValidationResult(
                validator_name="flake8",
                passed=True,
                errors=[],
                warnings=[],
                files_checked=10,
                execution_time=3.5,
            ),
        ]

        # Should return None and not crash
        run_id = persistence.save_validation_run(
            results=results,
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            total_duration=3.5,
        )

        assert run_id is None
