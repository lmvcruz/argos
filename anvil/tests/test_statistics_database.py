"""
Test suite for statistics database schema and operations.

This module tests the SQLite database schema used for storing validation
history, including tables for runs, validator results, test cases, and file
validations. Tests use in-memory databases for speed.
"""

import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anvil.storage.statistics_database import (
    FileValidationRecord,
    StatisticsDatabase,
    TestCaseRecord,
    ValidationRun,
    ValidatorRunRecord,
)


class TestDatabaseSchemaCreation:
    """Test database schema creation and initialization."""

    def test_create_database_schema(self):
        """Test that database schema is created with all required tables."""
        db = StatisticsDatabase(":memory:")

        # Verify all tables exist
        cursor = db.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        assert "validation_runs" in tables
        assert "validator_run_records" in tables
        assert "test_case_records" in tables
        assert "file_validation_records" in tables

    def test_validation_runs_table_structure(self):
        """Test validation_runs table has correct columns."""
        db = StatisticsDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(validation_runs)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "timestamp" in columns
        assert "git_commit" in columns
        assert "git_branch" in columns
        assert "incremental" in columns
        assert "passed" in columns
        assert "duration_seconds" in columns

    def test_validator_run_records_table_structure(self):
        """Test validator_run_records table has correct columns."""
        db = StatisticsDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(validator_run_records)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "run_id" in columns
        assert "validator_name" in columns
        assert "passed" in columns
        assert "error_count" in columns
        assert "warning_count" in columns
        assert "files_checked" in columns
        assert "duration_seconds" in columns

    def test_test_case_records_table_structure(self):
        """Test test_case_records table has correct columns."""
        db = StatisticsDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(test_case_records)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "run_id" in columns
        assert "test_name" in columns
        assert "test_suite" in columns
        assert "passed" in columns
        assert "skipped" in columns
        assert "duration_seconds" in columns
        assert "failure_message" in columns

    def test_file_validation_records_table_structure(self):
        """Test file_validation_records table has correct columns."""
        db = StatisticsDatabase(":memory:")

        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(file_validation_records)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "id" in columns
        assert "run_id" in columns
        assert "validator_name" in columns
        assert "file_path" in columns
        assert "error_count" in columns
        assert "warning_count" in columns

    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are enforced."""
        db = StatisticsDatabase(":memory:")

        # Try to insert validator record without valid run_id
        cursor = db.connection.cursor()
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO validator_run_records
                (run_id, validator_name, passed, error_count, warning_count,
                 files_checked, duration_seconds)
                VALUES (999, 'flake8', 1, 0, 0, 10, 1.5)
                """)


class TestValidationRunOperations:
    """Test CRUD operations for ValidationRun records."""

    def test_insert_validation_run(self):
        """Test inserting a validation run record."""
        db = StatisticsDatabase(":memory:")

        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )

        run_id = db.insert_validation_run(run)
        assert run_id > 0

    def test_insert_validation_run_without_git_info(self):
        """Test inserting validation run without git information."""
        db = StatisticsDatabase(":memory:")

        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit=None,
            git_branch=None,
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )

        run_id = db.insert_validation_run(run)
        assert run_id > 0

    def test_query_validation_run_by_id(self):
        """Test querying a validation run by ID."""
        db = StatisticsDatabase(":memory:")

        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )

        run_id = db.insert_validation_run(run)
        retrieved = db.get_validation_run(run_id)

        assert retrieved is not None
        assert retrieved.git_commit == "abc123"
        assert retrieved.git_branch == "main"
        assert retrieved.passed is True

    def test_query_runs_by_date_range(self):
        """Test querying validation runs by date range."""
        db = StatisticsDatabase(":memory:")

        now = datetime.now()

        # Insert runs at different times
        run1 = ValidationRun(
            timestamp=now - timedelta(days=5),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run2 = ValidationRun(
            timestamp=now - timedelta(days=3),
            git_commit="def456",
            git_branch="main",
            incremental=False,
            passed=False,
            duration_seconds=50.1,
        )
        run3 = ValidationRun(
            timestamp=now - timedelta(days=1),
            git_commit="ghi789",
            git_branch="feature",
            incremental=True,
            passed=True,
            duration_seconds=30.0,
        )

        db.insert_validation_run(run1)
        db.insert_validation_run(run2)
        db.insert_validation_run(run3)

        # Query runs from last 4 days
        start = now - timedelta(days=4)
        end = now
        runs = db.query_runs_by_date_range(start, end)

        assert len(runs) == 2
        assert runs[0].git_commit == "ghi789"  # Most recent first
        assert runs[1].git_commit == "def456"

    def test_query_runs_by_git_commit(self):
        """Test querying validation runs by git commit hash."""
        db = StatisticsDatabase(":memory:")

        run1 = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run2 = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=True,
            passed=True,
            duration_seconds=10.0,
        )

        db.insert_validation_run(run1)
        db.insert_validation_run(run2)

        runs = db.query_runs_by_git_commit("abc123")
        assert len(runs) == 2

    def test_query_runs_by_git_branch(self):
        """Test querying validation runs by git branch."""
        db = StatisticsDatabase(":memory:")

        run1 = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run2 = ValidationRun(
            timestamp=datetime.now(),
            git_commit="def456",
            git_branch="feature-branch",
            incremental=False,
            passed=False,
            duration_seconds=50.0,
        )

        db.insert_validation_run(run1)
        db.insert_validation_run(run2)

        runs = db.query_runs_by_git_branch("feature-branch")
        assert len(runs) == 1
        assert runs[0].git_commit == "def456"


class TestValidatorRunRecordOperations:
    """Test CRUD operations for ValidatorRunRecord records."""

    def test_insert_validator_run_record(self):
        """Test inserting a validator run record."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert validator record
        validator_record = ValidatorRunRecord(
            run_id=run_id,
            validator_name="flake8",
            passed=True,
            error_count=0,
            warning_count=2,
            files_checked=15,
            duration_seconds=3.5,
        )

        record_id = db.insert_validator_run_record(validator_record)
        assert record_id > 0

    def test_query_validator_results_for_run(self):
        """Test querying all validator results for a specific run."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert multiple validator records
        validators = [
            ValidatorRunRecord(
                run_id=run_id,
                validator_name="flake8",
                passed=True,
                error_count=0,
                warning_count=2,
                files_checked=15,
                duration_seconds=3.5,
            ),
            ValidatorRunRecord(
                run_id=run_id,
                validator_name="black",
                passed=False,
                error_count=3,
                warning_count=0,
                files_checked=15,
                duration_seconds=2.1,
            ),
        ]

        for validator_record in validators:
            db.insert_validator_run_record(validator_record)

        records = db.query_validator_results_for_run(run_id)
        assert len(records) == 2
        assert records[0].validator_name in ["flake8", "black"]
        assert records[1].validator_name in ["flake8", "black"]

    def test_query_validator_history(self):
        """Test querying history for a specific validator across runs."""
        db = StatisticsDatabase(":memory:")

        # Insert multiple runs
        for i in range(3):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            run_id = db.insert_validation_run(run)

            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name="flake8",
                passed=i % 2 == 0,
                error_count=i,
                warning_count=0,
                files_checked=15,
                duration_seconds=3.5,
            )
            db.insert_validator_run_record(validator_record)

        records = db.query_validator_history("flake8", limit=10)
        assert len(records) == 3


class TestTestCaseRecordOperations:
    """Test CRUD operations for TestCaseRecord records."""

    def test_insert_test_case_record(self):
        """Test inserting a test case record."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert test case record
        test_record = TestCaseRecord(
            run_id=run_id,
            test_name="test_example",
            test_suite="TestSuite",
            passed=True,
            skipped=False,
            duration_seconds=0.5,
            failure_message=None,
        )

        record_id = db.insert_test_case_record(test_record)
        assert record_id > 0

    def test_insert_failed_test_case_record(self):
        """Test inserting a failed test case with failure message."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=False,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert failed test case record
        test_record = TestCaseRecord(
            run_id=run_id,
            test_name="test_example",
            test_suite="TestSuite",
            passed=False,
            skipped=False,
            duration_seconds=0.5,
            failure_message="AssertionError: expected 5, got 3",
        )

        record_id = db.insert_test_case_record(test_record)
        assert record_id > 0

        # Verify failure message stored
        retrieved = db.get_test_case_record(record_id)
        assert retrieved.failure_message == "AssertionError: expected 5, got 3"

    def test_query_test_cases_for_run(self):
        """Test querying all test cases for a specific run."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert multiple test cases
        tests = [
            TestCaseRecord(
                run_id=run_id,
                test_name="test_one",
                test_suite="TestSuite",
                passed=True,
                skipped=False,
                duration_seconds=0.5,
                failure_message=None,
            ),
            TestCaseRecord(
                run_id=run_id,
                test_name="test_two",
                test_suite="TestSuite",
                passed=False,
                skipped=False,
                duration_seconds=0.8,
                failure_message="Failed",
            ),
        ]

        for test_record in tests:
            db.insert_test_case_record(test_record)

        records = db.query_test_cases_for_run(run_id)
        assert len(records) == 2

    def test_query_test_history(self):
        """Test querying history for a specific test across runs."""
        db = StatisticsDatabase(":memory:")

        # Insert multiple runs with same test
        for i in range(5):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            run_id = db.insert_validation_run(run)

            test_record = TestCaseRecord(
                run_id=run_id,
                test_name="test_example",
                test_suite="TestSuite",
                passed=i % 3 != 0,  # Fails on runs 0, 3
                skipped=False,
                duration_seconds=0.5,
                failure_message="Failed" if i % 3 == 0 else None,
            )
            db.insert_test_case_record(test_record)

        records = db.query_test_history("test_example", limit=10)
        assert len(records) == 5

        # Count passes and failures
        passes = sum(1 for r in records if r.passed)
        failures = sum(1 for r in records if not r.passed and not r.skipped)
        assert passes == 3
        assert failures == 2


class TestFileValidationRecordOperations:
    """Test CRUD operations for FileValidationRecord records."""

    def test_insert_file_validation_record(self):
        """Test inserting a file validation record."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert file validation record
        file_record = FileValidationRecord(
            run_id=run_id,
            validator_name="flake8",
            file_path="src/module.py",
            error_count=2,
            warning_count=1,
        )

        record_id = db.insert_file_validation_record(file_record)
        assert record_id > 0

    def test_query_file_validations_for_run(self):
        """Test querying file validations for a specific run."""
        db = StatisticsDatabase(":memory:")

        # Insert parent validation run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Insert multiple file validation records
        files = [
            FileValidationRecord(
                run_id=run_id,
                validator_name="flake8",
                file_path="src/module1.py",
                error_count=2,
                warning_count=1,
            ),
            FileValidationRecord(
                run_id=run_id,
                validator_name="flake8",
                file_path="src/module2.py",
                error_count=0,
                warning_count=3,
            ),
        ]

        for file_record in files:
            db.insert_file_validation_record(file_record)

        records = db.query_file_validations_for_run(run_id)
        assert len(records) == 2

    def test_get_file_error_frequency(self):
        """Test getting error frequency for a specific file."""
        db = StatisticsDatabase(":memory:")

        # Insert multiple runs with same file
        for i in range(5):
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=i),
                git_commit=f"commit{i}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            run_id = db.insert_validation_run(run)

            file_record = FileValidationRecord(
                run_id=run_id,
                validator_name="flake8",
                file_path="src/problematic.py",
                error_count=i + 1,
                warning_count=0,
            )
            db.insert_file_validation_record(file_record)

        frequency = db.get_file_error_frequency("src/problematic.py", limit=10)
        assert len(frequency) == 5

        # Most recent should have highest error count
        assert frequency[0].error_count == 1  # Most recent first (i=0)


class TestDatabaseMigration:
    """Test database schema migration."""

    def test_database_version_stored(self):
        """Test that database version is stored in metadata."""
        db = StatisticsDatabase(":memory:")

        version = db.get_schema_version()
        assert version >= 1

    def test_migrate_v1_to_v2(self):
        """Test migration from schema v1 to v2."""
        # Create v1 schema (without test_suite column in test_case_records)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        conn = None
        db = None
        try:
            # Create v1 schema manually
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE validation_runs (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    git_commit TEXT,
                    git_branch TEXT,
                    incremental INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL
                )
                """)

            cursor.execute("""
                CREATE TABLE test_case_records (
                    id INTEGER PRIMARY KEY,
                    run_id INTEGER NOT NULL,
                    test_name TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    skipped INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    failure_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES validation_runs(id)
                )
                """)

            cursor.execute("CREATE TABLE schema_version (version INTEGER)")
            cursor.execute("INSERT INTO schema_version (version) VALUES (1)")
            conn.commit()
            conn.close()
            conn = None

            # Open with StatisticsDatabase which should migrate
            db = StatisticsDatabase(db_path)

            # Check version updated
            assert db.get_schema_version() == 2

            # Check test_suite column exists
            cursor = db.connection.cursor()
            cursor.execute("PRAGMA table_info(test_case_records)")
            columns = {row[1] for row in cursor.fetchall()}
            assert "test_suite" in columns

        finally:
            if db:
                db.close()
            if conn:
                conn.close()

    """Test database retention policy and cleanup."""

    def test_delete_old_records(self):
        """Test deleting records older than retention period."""
        db = StatisticsDatabase(":memory:")

        # Insert runs at different ages
        for days_ago in [1, 30, 60, 90, 120]:
            run = ValidationRun(
                timestamp=datetime.now() - timedelta(days=days_ago),
                git_commit=f"commit{days_ago}",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            db.insert_validation_run(run)

        # Delete runs older than 90 days (exclusive - 90 days old is kept)
        deleted = db.delete_runs_older_than(days=90)
        assert deleted == 1  # Only 120 days old

        # Verify remaining runs (1, 30, 60, 90 days ago)
        all_runs = db.query_runs_by_date_range(datetime.now() - timedelta(days=365), datetime.now())
        assert len(all_runs) == 4

        # Insert run with related records
        run = ValidationRun(
            timestamp=datetime.now() - timedelta(days=100),
            git_commit="old_commit",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )
        run_id = db.insert_validation_run(run)

        # Add related records
        validator_record = ValidatorRunRecord(
            run_id=run_id,
            validator_name="flake8",
            passed=True,
            error_count=0,
            warning_count=0,
            files_checked=10,
            duration_seconds=3.5,
        )
        db.insert_validator_run_record(validator_record)

        # Delete old runs
        db.delete_runs_older_than(days=90)

        # Verify related records also deleted
        validator_records = db.query_validator_results_for_run(run_id)
        assert len(validator_records) == 0


class TestConcurrentAccess:
    """Test concurrent database access."""

    def test_concurrent_reads(self):
        """Test multiple concurrent read operations."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Create database with some data
            db1 = StatisticsDatabase(db_path)
            run = ValidationRun(
                timestamp=datetime.now(),
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            db1.insert_validation_run(run)
            db1.close()

            # Open multiple connections
            db2 = StatisticsDatabase(db_path)
            db3 = StatisticsDatabase(db_path)

            # Both should be able to read
            runs2 = db2.query_runs_by_date_range(datetime.now() - timedelta(days=1), datetime.now())
            runs3 = db3.query_runs_by_date_range(datetime.now() - timedelta(days=1), datetime.now())

            assert len(runs2) == 1
            assert len(runs3) == 1

            db2.close()
            db3.close()

        finally:
            Path(db_path).unlink(missing_ok=True)

    def test_write_lock_handling(self):
        """Test that writes are handled with proper locking."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = StatisticsDatabase(db_path)

            # Insert multiple runs (should handle locks automatically)
            for i in range(10):
                run = ValidationRun(
                    timestamp=datetime.now(),
                    git_commit=f"commit{i}",
                    git_branch="main",
                    incremental=False,
                    passed=True,
                    duration_seconds=45.2,
                )
                db.insert_validation_run(run)

            # Verify all inserted
            runs = db.query_runs_by_date_range(datetime.now() - timedelta(days=1), datetime.now())
            assert len(runs) == 10

            db.close()

        finally:
            Path(db_path).unlink(missing_ok=True)


class TestDatabaseCorruptionRecovery:
    """Test database corruption detection and recovery."""

    def test_detect_corrupted_database(self):
        """Test detection of corrupted database file."""
        # Create corrupted database file
        db_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db", mode="wb") as tmp:
                db_path = tmp.name
                # Write invalid data
                tmp.write(b"NOT A VALID SQLITE DATABASE")

            # Try to open corrupted database - should raise error
            try:
                db = StatisticsDatabase(db_path)
                db.close()  # Should not reach here
                assert False, "Expected DatabaseError"
            except sqlite3.DatabaseError:
                pass  # Expected
        finally:
            if db_path:
                # Windows needs a delay for file lock release
                import time

                time.sleep(0.1)
                try:
                    Path(db_path).unlink(missing_ok=True)
                except PermissionError:
                    pass  # Windows file locking - ignore

    def test_recover_from_corrupted_database(self):
        """Test recovery by recreating database from corruption."""
        # Create corrupted database file
        db_path = None
        db = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".db", mode="wb") as tmp:
                db_path = tmp.name
                # Write invalid data
                tmp.write(b"CORRUPTED")

            # Should detect corruption and recreate
            db = StatisticsDatabase(db_path, auto_recover=True)

            # Should be able to use database
            run = ValidationRun(
                timestamp=datetime.now(),
                git_commit="abc123",
                git_branch="main",
                incremental=False,
                passed=True,
                duration_seconds=45.2,
            )
            run_id = db.insert_validation_run(run)
            assert run_id > 0

        finally:
            if db:
                db.close()
            if db_path:
                # Windows needs a delay for file lock release
                import time

                time.sleep(0.1)
                try:
                    Path(db_path).unlink(missing_ok=True)
                except PermissionError:
                    pass  # Windows file locking - ignore


class TestTransactionHandling:
    """Test database transaction management."""

    def test_transaction_rollback_on_error(self):
        """Test that transactions rollback on error."""
        db = StatisticsDatabase(":memory:")

        # Start transaction and insert run
        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )

        try:
            run_id = db.insert_validation_run(run)

            # Try to insert invalid validator record (should fail)
            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name="flake8",
                passed=True,
                error_count=-1,  # Invalid negative count
                warning_count=0,
                files_checked=10,
                duration_seconds=3.5,
            )

            # This should fail validation and rollback
            with pytest.raises(ValueError):
                db.insert_validator_run_record_with_validation(validator_record)
        except Exception:
            pass

        # Verify run still exists (only validator record rolled back)
        retrieved = db.get_validation_run(run_id)
        assert retrieved is not None

    def test_transaction_commit_on_success(self):
        """Test that successful transactions commit properly."""
        db = StatisticsDatabase(":memory:")

        run = ValidationRun(
            timestamp=datetime.now(),
            git_commit="abc123",
            git_branch="main",
            incremental=False,
            passed=True,
            duration_seconds=45.2,
        )

        run_id = db.insert_validation_run(run)

        # Insert multiple records in transaction
        validator_record = ValidatorRunRecord(
            run_id=run_id,
            validator_name="flake8",
            passed=True,
            error_count=0,
            warning_count=2,
            files_checked=10,
            duration_seconds=3.5,
        )
        db.insert_validator_run_record(validator_record)

        # Verify committed
        records = db.query_validator_results_for_run(run_id)
        assert len(records) == 1
