"""
SQLite database for storing validation history and statistics.

This module provides a database schema and operations for tracking validation
runs, validator results, test cases, and file validations over time. The data
enables historical analysis, flaky test detection, and smart filtering.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional


@dataclass
class ValidationRun:
    """
    Represents a complete validation run.

    Args:
        timestamp: When the validation run started
        git_commit: Git commit hash (if available)
        git_branch: Git branch name (if available)
        incremental: Whether this was an incremental run
        passed: Whether the overall validation passed
        duration_seconds: Total duration of the validation run
        id: Database ID (set after insertion)
    """

    timestamp: datetime
    git_commit: Optional[str]
    git_branch: Optional[str]
    incremental: bool
    passed: bool
    duration_seconds: float
    id: Optional[int] = None


@dataclass
class ValidatorRunRecord:
    """
    Represents the result of running a single validator.

    Args:
        run_id: Foreign key to validation_runs.id
        validator_name: Name of the validator (e.g., "flake8")
        passed: Whether the validator passed
        error_count: Number of errors found
        warning_count: Number of warnings found
        files_checked: Number of files checked
        duration_seconds: Validator execution duration
        id: Database ID (set after insertion)
    """

    run_id: int
    validator_name: str
    passed: bool
    error_count: int
    warning_count: int
    files_checked: int
    duration_seconds: float
    id: Optional[int] = None


@dataclass
class TestCaseRecord:
    """
    Represents a single test case result.

    Note: This is a dataclass, not a pytest test class.

    Args:
        run_id: Foreign key to validation_runs.id
        test_name: Name of the test
        test_suite: Test suite/class name
        passed: Whether the test passed
        skipped: Whether the test was skipped
        duration_seconds: Test execution duration
        failure_message: Failure message if test failed
        id: Database ID (set after insertion)
    """

    run_id: int
    test_name: str
    test_suite: str
    passed: bool
    skipped: bool
    duration_seconds: float
    failure_message: Optional[str]
    id: Optional[int] = None


@dataclass
class FileValidationRecord:
    """
    Represents validation results for a single file.

    Args:
        run_id: Foreign key to validation_runs.id
        validator_name: Name of the validator
        file_path: Path to the file
        error_count: Number of errors in this file
        warning_count: Number of warnings in this file
        id: Database ID (set after insertion)
    """

    run_id: int
    validator_name: str
    file_path: str
    error_count: int
    warning_count: int
    id: Optional[int] = None


class StatisticsDatabase:
    """
    SQLite database for validation statistics and history.

    Provides schema creation, CRUD operations, and historical queries for
    validation runs, validator results, test cases, and file validations.

    Examples:
        >>> db = StatisticsDatabase("anvil_stats.db")
        >>> run = ValidationRun(
        ...     timestamp=datetime.now(),
        ...     git_commit="abc123",
        ...     git_branch="main",
        ...     incremental=False,
        ...     passed=True,
        ...     duration_seconds=45.2,
        ... )
        >>> run_id = db.insert_validation_run(run)
    """

    def __init__(self, db_path: str, auto_recover: bool = False):
        """
        Initialize database connection and create schema if needed.

        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
            auto_recover: If True, recreate corrupted database automatically

        Raises:
            sqlite3.DatabaseError: If database is corrupted and auto_recover=False
        """
        self.db_path = db_path
        self.auto_recover = auto_recover

        try:
            self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._create_schema()
            self._migrate_if_needed()
        except sqlite3.DatabaseError as e:
            if auto_recover and db_path != ":memory:":
                # Close the corrupted connection first
                if hasattr(self, "connection"):
                    try:
                        self.connection.close()
                    except Exception:
                        pass

                # Remove corrupted database and recreate
                import time

                time.sleep(0.1)  # Windows file lock delay
                Path(db_path).unlink(missing_ok=True)

                # Recreate database
                self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
                self.connection.execute("PRAGMA foreign_keys = ON")
                self._create_schema()
            else:
                raise e

    def _create_schema(self):
        """Create database schema if it doesn't exist."""
        cursor = self.connection.cursor()

        # Create validation_runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                git_commit TEXT,
                git_branch TEXT,
                incremental INTEGER NOT NULL,
                passed INTEGER NOT NULL,
                duration_seconds REAL NOT NULL
            )
            """)

        # Create validator_run_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validator_run_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                validator_name TEXT NOT NULL,
                passed INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                warning_count INTEGER NOT NULL,
                files_checked INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
            )
            """)

        # Create test_case_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_case_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                test_name TEXT NOT NULL,
                test_suite TEXT NOT NULL,
                passed INTEGER NOT NULL,
                skipped INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                failure_message TEXT,
                FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
            )
            """)

        # Create file_validation_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_validation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                validator_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                error_count INTEGER NOT NULL,
                warning_count INTEGER NOT NULL,
                FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
            )
            """)

        # Create schema version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
            """)

        # Insert initial schema version if not exists
        cursor.execute("SELECT COUNT(*) FROM schema_version")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO schema_version (version) VALUES (2)")

        self.connection.commit()

    def _migrate_if_needed(self):
        """Migrate database schema to latest version if needed."""
        current_version = self.get_schema_version()

        if current_version < 2:
            self._migrate_v1_to_v2()

    def _migrate_v1_to_v2(self):
        """Migrate from schema version 1 to 2."""
        cursor = self.connection.cursor()

        # Add test_suite column if it doesn't exist
        cursor.execute("PRAGMA table_info(test_case_records)")
        columns = {row[1] for row in cursor.fetchall()}

        if "test_suite" not in columns:
            # Create new table with test_suite column
            cursor.execute("""
                CREATE TABLE test_case_records_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    test_name TEXT NOT NULL,
                    test_suite TEXT NOT NULL DEFAULT '',
                    passed INTEGER NOT NULL,
                    skipped INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    failure_message TEXT,
                    FOREIGN KEY (run_id) REFERENCES validation_runs(id) ON DELETE CASCADE
                )
                """)

            # Copy data from old table
            cursor.execute("""
                INSERT INTO test_case_records_new
                    (id, run_id, test_name, test_suite, passed, skipped,
                     duration_seconds, failure_message)
                SELECT id, run_id, test_name, '', passed, skipped,
                       duration_seconds, failure_message
                FROM test_case_records
                """)

            # Drop old table and rename new one
            cursor.execute("DROP TABLE test_case_records")
            cursor.execute("ALTER TABLE test_case_records_new RENAME TO test_case_records")

        # Update schema version
        cursor.execute("UPDATE schema_version SET version = 2")
        self.connection.commit()

    def get_schema_version(self) -> int:
        """
        Get current database schema version.

        Returns:
            Schema version number
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT version FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result else 0

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def insert_validation_run(self, run: ValidationRun) -> int:
        """
        Insert a validation run record.

        Args:
            run: ValidationRun object to insert

        Returns:
            Database ID of inserted record
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO validation_runs
                (timestamp, git_commit, git_branch, incremental, passed,
                 duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run.timestamp.isoformat(),
                run.git_commit,
                run.git_branch,
                1 if run.incremental else 0,
                1 if run.passed else 0,
                run.duration_seconds,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_validation_run(self, run_id: int) -> Optional[ValidationRun]:
        """
        Get a validation run by ID.

        Args:
            run_id: Database ID of the run

        Returns:
            ValidationRun object or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, git_commit, git_branch, incremental, passed,
                   duration_seconds
            FROM validation_runs
            WHERE id = ?
            """,
            (run_id,),
        )
        row = cursor.fetchone()

        if row:
            return ValidationRun(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                git_commit=row[2],
                git_branch=row[3],
                incremental=bool(row[4]),
                passed=bool(row[5]),
                duration_seconds=row[6],
            )
        return None

    def query_runs_by_date_range(self, start: datetime, end: datetime) -> List[ValidationRun]:
        """
        Query validation runs within a date range.

        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)

        Returns:
            List of ValidationRun objects, newest first
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, git_commit, git_branch, incremental, passed,
                   duration_seconds
            FROM validation_runs
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
            """,
            (start.isoformat(), end.isoformat()),
        )

        runs = []
        for row in cursor.fetchall():
            runs.append(
                ValidationRun(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    git_commit=row[2],
                    git_branch=row[3],
                    incremental=bool(row[4]),
                    passed=bool(row[5]),
                    duration_seconds=row[6],
                )
            )
        return runs

    def query_runs_by_git_commit(self, commit: str) -> List[ValidationRun]:
        """
        Query validation runs by git commit hash.

        Args:
            commit: Git commit hash

        Returns:
            List of ValidationRun objects
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, git_commit, git_branch, incremental, passed,
                   duration_seconds
            FROM validation_runs
            WHERE git_commit = ?
            ORDER BY timestamp DESC
            """,
            (commit,),
        )

        runs = []
        for row in cursor.fetchall():
            runs.append(
                ValidationRun(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    git_commit=row[2],
                    git_branch=row[3],
                    incremental=bool(row[4]),
                    passed=bool(row[5]),
                    duration_seconds=row[6],
                )
            )
        return runs

    def query_runs_by_git_branch(self, branch: str) -> List[ValidationRun]:
        """
        Query validation runs by git branch name.

        Args:
            branch: Git branch name

        Returns:
            List of ValidationRun objects
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, git_commit, git_branch, incremental, passed,
                   duration_seconds
            FROM validation_runs
            WHERE git_branch = ?
            ORDER BY timestamp DESC
            """,
            (branch,),
        )

        runs = []
        for row in cursor.fetchall():
            runs.append(
                ValidationRun(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    git_commit=row[2],
                    git_branch=row[3],
                    incremental=bool(row[4]),
                    passed=bool(row[5]),
                    duration_seconds=row[6],
                )
            )
        return runs

    def insert_validator_run_record(self, record: ValidatorRunRecord) -> int:
        """
        Insert a validator run record.

        Args:
            record: ValidatorRunRecord object to insert

        Returns:
            Database ID of inserted record
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO validator_run_records
                (run_id, validator_name, passed, error_count, warning_count,
                 files_checked, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                record.validator_name,
                1 if record.passed else 0,
                record.error_count,
                record.warning_count,
                record.files_checked,
                record.duration_seconds,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def insert_validator_run_record_with_validation(self, record: ValidatorRunRecord) -> int:
        """
        Insert validator run record with validation.

        Args:
            record: ValidatorRunRecord to insert

        Returns:
            Database ID of inserted record

        Raises:
            ValueError: If validation fails
        """
        if record.error_count < 0:
            raise ValueError("error_count cannot be negative")
        if record.warning_count < 0:
            raise ValueError("warning_count cannot be negative")

        return self.insert_validator_run_record(record)

    def query_validator_results_for_run(self, run_id: int) -> List[ValidatorRunRecord]:
        """
        Query all validator results for a specific run.

        Args:
            run_id: Database ID of the validation run

        Returns:
            List of ValidatorRunRecord objects
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, run_id, validator_name, passed, error_count,
                   warning_count, files_checked, duration_seconds
            FROM validator_run_records
            WHERE run_id = ?
            """,
            (run_id,),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                ValidatorRunRecord(
                    id=row[0],
                    run_id=row[1],
                    validator_name=row[2],
                    passed=bool(row[3]),
                    error_count=row[4],
                    warning_count=row[5],
                    files_checked=row[6],
                    duration_seconds=row[7],
                )
            )
        return records

    def query_validator_history(
        self, validator_name: str, limit: int = 100
    ) -> List[ValidatorRunRecord]:
        """
        Query history for a specific validator across runs.

        Args:
            validator_name: Name of the validator
            limit: Maximum number of records to return

        Returns:
            List of ValidatorRunRecord objects, newest first
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT vrr.id, vrr.run_id, vrr.validator_name, vrr.passed,
                   vrr.error_count, vrr.warning_count, vrr.files_checked,
                   vrr.duration_seconds
            FROM validator_run_records vrr
            JOIN validation_runs vr ON vrr.run_id = vr.id
            WHERE vrr.validator_name = ?
            ORDER BY vr.timestamp DESC
            LIMIT ?
            """,
            (validator_name, limit),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                ValidatorRunRecord(
                    id=row[0],
                    run_id=row[1],
                    validator_name=row[2],
                    passed=bool(row[3]),
                    error_count=row[4],
                    warning_count=row[5],
                    files_checked=row[6],
                    duration_seconds=row[7],
                )
            )
        return records

    def insert_test_case_record(self, record: TestCaseRecord) -> int:
        """
        Insert a test case record.

        Args:
            record: TestCaseRecord object to insert

        Returns:
            Database ID of inserted record
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO test_case_records
                (run_id, test_name, test_suite, passed, skipped,
                 duration_seconds, failure_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                record.test_name,
                record.test_suite,
                1 if record.passed else 0,
                1 if record.skipped else 0,
                record.duration_seconds,
                record.failure_message,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_test_case_record(self, record_id: int) -> Optional[TestCaseRecord]:
        """
        Get a test case record by ID.

        Args:
            record_id: Database ID of the record

        Returns:
            TestCaseRecord object or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, run_id, test_name, test_suite, passed, skipped,
                   duration_seconds, failure_message
            FROM test_case_records
            WHERE id = ?
            """,
            (record_id,),
        )
        row = cursor.fetchone()

        if row:
            return TestCaseRecord(
                id=row[0],
                run_id=row[1],
                test_name=row[2],
                test_suite=row[3],
                passed=bool(row[4]),
                skipped=bool(row[5]),
                duration_seconds=row[6],
                failure_message=row[7],
            )
        return None

    def query_test_cases_for_run(self, run_id: int) -> List[TestCaseRecord]:
        """
        Query all test cases for a specific run.

        Args:
            run_id: Database ID of the validation run

        Returns:
            List of TestCaseRecord objects
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, run_id, test_name, test_suite, passed, skipped,
                   duration_seconds, failure_message
            FROM test_case_records
            WHERE run_id = ?
            """,
            (run_id,),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                TestCaseRecord(
                    id=row[0],
                    run_id=row[1],
                    test_name=row[2],
                    test_suite=row[3],
                    passed=bool(row[4]),
                    skipped=bool(row[5]),
                    duration_seconds=row[6],
                    failure_message=row[7],
                )
            )
        return records

    def query_test_history(self, test_name: str, limit: int = 100) -> List[TestCaseRecord]:
        """
        Query history for a specific test across runs.

        Args:
            test_name: Name of the test
            limit: Maximum number of records to return

        Returns:
            List of TestCaseRecord objects, newest first
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT tcr.id, tcr.run_id, tcr.test_name, tcr.test_suite,
                   tcr.passed, tcr.skipped, tcr.duration_seconds,
                   tcr.failure_message
            FROM test_case_records tcr
            JOIN validation_runs vr ON tcr.run_id = vr.id
            WHERE tcr.test_name = ?
            ORDER BY vr.timestamp DESC
            LIMIT ?
            """,
            (test_name, limit),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                TestCaseRecord(
                    id=row[0],
                    run_id=row[1],
                    test_name=row[2],
                    test_suite=row[3],
                    passed=bool(row[4]),
                    skipped=bool(row[5]),
                    duration_seconds=row[6],
                    failure_message=row[7],
                )
            )
        return records

    def insert_file_validation_record(self, record: FileValidationRecord) -> int:
        """
        Insert a file validation record.

        Args:
            record: FileValidationRecord object to insert

        Returns:
            Database ID of inserted record
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO file_validation_records
                (run_id, validator_name, file_path, error_count, warning_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                record.validator_name,
                record.file_path,
                record.error_count,
                record.warning_count,
            ),
        )
        self.connection.commit()
        return cursor.lastrowid

    def query_file_validations_for_run(self, run_id: int) -> List[FileValidationRecord]:
        """
        Query all file validations for a specific run.

        Args:
            run_id: Database ID of the validation run

        Returns:
            List of FileValidationRecord objects
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, run_id, validator_name, file_path, error_count,
                   warning_count
            FROM file_validation_records
            WHERE run_id = ?
            """,
            (run_id,),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                FileValidationRecord(
                    id=row[0],
                    run_id=row[1],
                    validator_name=row[2],
                    file_path=row[3],
                    error_count=row[4],
                    warning_count=row[5],
                )
            )
        return records

    def get_file_error_frequency(
        self, file_path: str, limit: int = 100
    ) -> List[FileValidationRecord]:
        """
        Get error frequency for a specific file across runs.

        Args:
            file_path: Path to the file
            limit: Maximum number of records to return

        Returns:
            List of FileValidationRecord objects, newest first
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT fvr.id, fvr.run_id, fvr.validator_name, fvr.file_path,
                   fvr.error_count, fvr.warning_count
            FROM file_validation_records fvr
            JOIN validation_runs vr ON fvr.run_id = vr.id
            WHERE fvr.file_path = ?
            ORDER BY vr.timestamp DESC
            LIMIT ?
            """,
            (file_path, limit),
        )

        records = []
        for row in cursor.fetchall():
            records.append(
                FileValidationRecord(
                    id=row[0],
                    run_id=row[1],
                    validator_name=row[2],
                    file_path=row[3],
                    error_count=row[4],
                    warning_count=row[5],
                )
            )
        return records

    def delete_runs_older_than(self, days: int) -> int:
        """
        Delete validation runs older than specified days.

        Args:
            days: Delete runs older than this many days

        Returns:
            Number of runs deleted
        """
        cutoff = datetime.now() - timedelta(days=days)
        cursor = self.connection.cursor()

        # Count runs to be deleted
        cursor.execute(
            "SELECT COUNT(*) FROM validation_runs WHERE timestamp < ?",
            (cutoff.isoformat(),),
        )
        count = cursor.fetchone()[0]

        # Delete runs (cascade will delete related records)
        cursor.execute(
            "DELETE FROM validation_runs WHERE timestamp < ?",
            (cutoff.isoformat(),),
        )
        self.connection.commit()

        return count
