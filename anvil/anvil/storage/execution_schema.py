"""
Database schema for selective execution and history tracking.

This module provides schema definitions for tracking execution history,
execution rules, and entity statistics to enable selective test execution
based on historical data.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ExecutionHistory:
    """
    Historical record of test/validation entity executions.

    Args:
        execution_id: Unique identifier for the execution run
        entity_id: Identifier for the entity (e.g., test nodeid)
        entity_type: Type of entity (test, coverage, lint)
        timestamp: When the execution occurred
        status: Execution status (PASSED, FAILED, SKIPPED, ERROR)
        duration: Execution duration in seconds
        space: Execution space (local, ci)
        metadata: Additional metadata as JSON
        id: Database ID (set after insertion)
    """

    execution_id: str
    entity_id: str
    entity_type: str
    timestamp: datetime
    status: str
    duration: Optional[float]
    space: str = "local"
    metadata: Optional[Dict] = None
    id: Optional[int] = None


@dataclass
class ExecutionRule:
    """
    Rule defining selective execution criteria.

    Args:
        name: Unique rule name
        criteria: Selection criteria (all, group, failed-in-last, failure-rate, changed-files)
        enabled: Whether the rule is active
        threshold: Numeric threshold for failure-rate criteria
        window: Number of executions to consider for statistics
        groups: List of entity patterns for group criteria
        executor_config: Executor-specific configuration
        created_at: Rule creation timestamp
        updated_at: Rule last update timestamp
        id: Database ID (set after insertion)
    """

    name: str
    criteria: str
    enabled: bool = True
    threshold: Optional[float] = None
    window: Optional[int] = None
    groups: Optional[List[str]] = None
    executor_config: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class EntityStatistics:
    """
    Aggregated statistics for a validation entity.

    Args:
        entity_id: Identifier for the entity
        entity_type: Type of entity (test, coverage, lint)
        total_runs: Total number of executions
        passed: Number of passed executions
        failed: Number of failed executions
        skipped: Number of skipped executions
        failure_rate: Percentage of failed executions (0.0-1.0)
        avg_duration: Average execution duration in seconds
        last_run: Timestamp of last execution
        last_failure: Timestamp of last failure (if any)
        last_updated: Timestamp of last statistics update
        id: Database ID (set after insertion)
    """

    entity_id: str
    entity_type: str
    total_runs: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failure_rate: float = 0.0
    avg_duration: Optional[float] = None
    last_run: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class CoverageHistory:
    """
    Historical coverage data for a specific file.

    Args:
        execution_id: Unique identifier for the execution run
        file_path: Path to the covered file (relative to project root)
        timestamp: When the coverage was measured
        total_statements: Total number of executable statements
        covered_statements: Number of covered statements
        coverage_percentage: Coverage percentage (0.0-100.0)
        missing_lines: JSON list of uncovered line numbers
        space: Execution space (local, ci)
        metadata: Additional metadata as JSON
        id: Database ID (set after insertion)
    """

    execution_id: str
    file_path: str
    timestamp: datetime
    total_statements: int
    covered_statements: int
    coverage_percentage: float
    missing_lines: Optional[List[int]] = None
    space: str = "local"
    metadata: Optional[Dict] = None
    id: Optional[int] = None


@dataclass
class CoverageSummary:
    """
    Summary coverage metrics for an execution.

    Args:
        execution_id: Unique identifier for the execution run
        timestamp: When the coverage was measured
        total_coverage: Overall coverage percentage (0.0-100.0)
        files_analyzed: Number of files analyzed
        total_statements: Total number of statements across all files
        covered_statements: Total number of covered statements
        space: Execution space (local, ci)
        metadata: Additional metadata as JSON (e.g., platform, python_version)
        id: Database ID (set after insertion)
    """

    execution_id: str
    timestamp: datetime
    total_coverage: float
    files_analyzed: int
    total_statements: int
    covered_statements: int
    space: str = "local"
    metadata: Optional[Dict] = None
    id: Optional[int] = None


@dataclass
class LintViolation:
    """
    Individual lint violation record.

    Args:
        execution_id: Unique identifier for the execution run
        file_path: Path to the file with the violation
        line_number: Line number of the violation
        column_number: Column number of the violation (optional)
        severity: Violation severity (ERROR, WARNING, INFO)
        code: Violation code (e.g., E501, W503, F401)
        message: Detailed violation message
        validator: Validator that detected the violation (flake8, black, isort, etc.)
        timestamp: When the violation was detected
        space: Execution space (local, ci)
        metadata: Additional metadata as JSON
        id: Database ID (set after insertion)
    """

    execution_id: str
    file_path: str
    line_number: int
    severity: str
    code: str
    message: str
    validator: str
    timestamp: datetime
    column_number: Optional[int] = None
    space: str = "local"
    metadata: Optional[Dict] = None
    id: Optional[int] = None


@dataclass
class LintSummary:
    """
    Summary of lint execution results.

    Args:
        execution_id: Unique identifier for the execution run
        timestamp: When the lint scan was performed
        validator: Validator that was run (flake8, black, isort, etc.)
        files_scanned: Number of files scanned
        total_violations: Total number of violations found
        errors: Number of ERROR severity violations
        warnings: Number of WARNING severity violations
        info: Number of INFO severity violations
        by_code: JSON dict of violation counts by code (e.g., {"E501": 10, "W503": 5})
        space: Execution space (local, ci)
        metadata: Additional metadata as JSON
        id: Database ID (set after insertion)
    """

    execution_id: str
    timestamp: datetime
    validator: str
    files_scanned: int
    total_violations: int
    errors: int = 0
    warnings: int = 0
    info: int = 0
    by_code: Optional[Dict[str, int]] = None
    space: str = "local"
    metadata: Optional[Dict] = None
    id: Optional[int] = None


@dataclass
class CodeQualityMetrics:
    """
    Aggregated code quality metrics per file.

    Args:
        file_path: Path to the file
        validator: Validator type (flake8, black, isort, etc.)
        total_scans: Total number of scans performed on this file
        total_violations: Total cumulative violations found
        avg_violations_per_scan: Average violations per scan
        most_common_code: Most frequently occurring violation code
        last_scan: Timestamp of most recent scan
        last_violation: Timestamp of most recent violation (if any)
        last_updated: Timestamp of last metrics update
        id: Database ID (set after insertion)
    """

    file_path: str
    validator: str
    total_scans: int = 0
    total_violations: int = 0
    avg_violations_per_scan: float = 0.0
    most_common_code: Optional[str] = None
    last_scan: Optional[datetime] = None
    last_violation: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    id: Optional[int] = None


class ExecutionDatabase:
    """
    SQLite database for execution history and selective execution rules.

    Provides schema creation, CRUD operations, and historical queries for
    execution history, rules, and entity statistics to support selective
    execution based on historical data.

    Examples:
        >>> db = ExecutionDatabase(".anvil/history.db")
        >>> history = ExecutionHistory(
        ...     execution_id="local-123",
        ...     entity_id="tests/test_example.py::test_func",
        ...     entity_type="test",
        ...     timestamp=datetime.now(),
        ...     status="PASSED",
        ...     duration=1.23,
        ... )
        >>> db.insert_execution_history(history)
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

        # Create parent directory if it doesn't exist (and not in-memory)
        if db_path != ":memory:":
            db_path_obj = Path(db_path)
            db_path_obj.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._create_schema()
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

        # Create execution_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                duration REAL,
                space TEXT DEFAULT 'local',
                metadata TEXT
            )
            """)

        # Create indexes for execution_history
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_timestamp
            ON execution_history(entity_id, timestamp)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_timestamp
            ON execution_history(status, timestamp)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_execution_id
            ON execution_history(execution_id)
            """)

        # Create execution_rules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                criteria TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                threshold REAL,
                window INTEGER,
                groups TEXT,
                executor_config TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Create entity_statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT UNIQUE NOT NULL,
                entity_type TEXT NOT NULL,
                total_runs INTEGER DEFAULT 0,
                passed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                failure_rate REAL DEFAULT 0.0,
                avg_duration REAL,
                last_run TEXT,
                last_failure TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Create indexes for entity_statistics
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_failure_rate
            ON entity_statistics(failure_rate)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_type
            ON entity_statistics(entity_type)
            """)

        # Create coverage_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coverage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                total_statements INTEGER NOT NULL,
                covered_statements INTEGER NOT NULL,
                coverage_percentage REAL NOT NULL,
                missing_lines TEXT,
                space TEXT DEFAULT 'local',
                metadata TEXT
            )
            """)

        # Create indexes for coverage_history
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coverage_file_timestamp
            ON coverage_history(file_path, timestamp)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coverage_execution_id
            ON coverage_history(execution_id)
            """)

        # Create coverage_summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coverage_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                total_coverage REAL NOT NULL,
                files_analyzed INTEGER NOT NULL,
                total_statements INTEGER NOT NULL,
                covered_statements INTEGER NOT NULL,
                space TEXT DEFAULT 'local',
                metadata TEXT
            )
            """)

        # Create index for coverage_summary
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coverage_summary_timestamp
            ON coverage_summary(timestamp)
            """)

        # Create lint_violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lint_violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                column_number INTEGER,
                severity TEXT NOT NULL,
                code TEXT NOT NULL,
                message TEXT NOT NULL,
                validator TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                space TEXT DEFAULT 'local',
                metadata TEXT
            )
            """)

        # Create indexes for lint_violations
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lint_file_severity
            ON lint_violations(file_path, severity)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lint_code
            ON lint_violations(code)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lint_execution_id
            ON lint_violations(execution_id)
            """)

        # Create lint_summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lint_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                validator TEXT NOT NULL,
                files_scanned INTEGER NOT NULL,
                total_violations INTEGER NOT NULL,
                errors INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                info INTEGER DEFAULT 0,
                by_code TEXT,
                space TEXT DEFAULT 'local',
                metadata TEXT
            )
            """)

        # Create index for lint_summary
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lint_summary_timestamp
            ON lint_summary(timestamp)
            """)

        # Create code_quality_metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                validator TEXT NOT NULL,
                total_scans INTEGER DEFAULT 0,
                total_violations INTEGER DEFAULT 0,
                avg_violations_per_scan REAL DEFAULT 0.0,
                most_common_code TEXT,
                last_scan TEXT,
                last_violation TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, validator)
            )
            """)

        # Create indexes for code_quality_metrics
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality_validator
            ON code_quality_metrics(validator)
            """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality_avg_violations
            ON code_quality_metrics(avg_violations_per_scan)
            """)

        self.connection.commit()

    def close(self):
        """Close the database connection."""
        if hasattr(self, "connection"):
            self.connection.close()

    def insert_execution_history(self, record: ExecutionHistory) -> int:
        """
        Insert an execution history record.

        Args:
            record: ExecutionHistory record to insert

        Returns:
            Database ID of the inserted record
        """
        cursor = self.connection.cursor()

        import json

        metadata_json = json.dumps(record.metadata) if record.metadata else None

        cursor.execute(
            """
            INSERT INTO execution_history
                (execution_id, entity_id, entity_type, timestamp, status, duration, space, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.execution_id,
                record.entity_id,
                record.entity_type,
                record.timestamp.isoformat(),
                record.status,
                record.duration,
                record.space,
                metadata_json,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_execution_history(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ExecutionHistory]:
        """
        Retrieve execution history records.

        Args:
            entity_id: Filter by entity ID (optional)
            entity_type: Filter by entity type (optional)
            limit: Maximum number of records to return (optional)

        Returns:
            List of ExecutionHistory records
        """
        cursor = self.connection.cursor()

        query = "SELECT * FROM execution_history WHERE 1=1"
        params = []

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)

        import json

        records = []
        for row in cursor.fetchall():
            metadata = json.loads(row[8]) if row[8] else None
            records.append(
                ExecutionHistory(
                    id=row[0],
                    execution_id=row[1],
                    entity_id=row[2],
                    entity_type=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    status=row[5],
                    duration=row[6],
                    space=row[7],
                    metadata=metadata,
                )
            )

        return records

    def insert_execution_rule(self, rule: ExecutionRule) -> int:
        """
        Insert an execution rule.

        Args:
            rule: ExecutionRule to insert

        Returns:
            Database ID of the inserted rule
        """
        cursor = self.connection.cursor()

        import json

        groups_json = json.dumps(rule.groups) if rule.groups else None
        config_json = json.dumps(rule.executor_config) if rule.executor_config else None

        cursor.execute(
            """
            INSERT INTO execution_rules
                (name, criteria, enabled, threshold, window, groups, executor_config)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule.name,
                rule.criteria,
                1 if rule.enabled else 0,
                rule.threshold,
                rule.window,
                groups_json,
                config_json,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_execution_rule(self, name: str) -> Optional[ExecutionRule]:
        """
        Retrieve an execution rule by name.

        Args:
            name: Rule name

        Returns:
            ExecutionRule if found, None otherwise
        """
        cursor = self.connection.cursor()

        cursor.execute("SELECT * FROM execution_rules WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return None

        import json

        groups = json.loads(row[6]) if row[6] else None
        config = json.loads(row[7]) if row[7] else None

        return ExecutionRule(
            id=row[0],
            name=row[1],
            criteria=row[2],
            enabled=bool(row[3]),
            threshold=row[4],
            window=row[5],
            groups=groups,
            executor_config=config,
            created_at=datetime.fromisoformat(row[8]) if row[8] else None,
            updated_at=datetime.fromisoformat(row[9]) if row[9] else None,
        )

    def update_entity_statistics(self, stats: EntityStatistics) -> int:
        """
        Update or insert entity statistics.

        Args:
            stats: EntityStatistics to update

        Returns:
            Database ID of the updated/inserted statistics
        """
        cursor = self.connection.cursor()

        # Upsert operation
        cursor.execute(
            """
            INSERT INTO entity_statistics
                (entity_id, entity_type, total_runs, passed, failed, skipped,
                 failure_rate, avg_duration, last_run, last_failure, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_id) DO UPDATE SET
                entity_type = excluded.entity_type,
                total_runs = excluded.total_runs,
                passed = excluded.passed,
                failed = excluded.failed,
                skipped = excluded.skipped,
                failure_rate = excluded.failure_rate,
                avg_duration = excluded.avg_duration,
                last_run = excluded.last_run,
                last_failure = excluded.last_failure,
                last_updated = excluded.last_updated
            """,
            (
                stats.entity_id,
                stats.entity_type,
                stats.total_runs,
                stats.passed,
                stats.failed,
                stats.skipped,
                stats.failure_rate,
                stats.avg_duration,
                stats.last_run.isoformat() if stats.last_run else None,
                stats.last_failure.isoformat() if stats.last_failure else None,
                datetime.now().isoformat(),
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_entity_statistics(
        self, entity_id: Optional[str] = None, entity_type: Optional[str] = None
    ) -> List[EntityStatistics]:
        """
        Retrieve entity statistics.

        Args:
            entity_id: Filter by entity ID (optional)
            entity_type: Filter by entity type (optional)

        Returns:
            List of EntityStatistics records
        """
        cursor = self.connection.cursor()

        query = "SELECT * FROM entity_statistics WHERE 1=1"
        params = []

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                EntityStatistics(
                    id=row[0],
                    entity_id=row[1],
                    entity_type=row[2],
                    total_runs=row[3],
                    passed=row[4],
                    failed=row[5],
                    skipped=row[6],
                    failure_rate=row[7],
                    avg_duration=row[8],
                    last_run=datetime.fromisoformat(row[9]) if row[9] else None,
                    last_failure=datetime.fromisoformat(row[10]) if row[10] else None,
                    last_updated=datetime.fromisoformat(row[11]) if row[11] else None,
                )
            )

        return records

    # Coverage-related methods

    def insert_coverage_history(self, record: CoverageHistory) -> int:
        """
        Insert a coverage history record.

        Args:
            record: CoverageHistory instance to insert

        Returns:
            Row ID of inserted record
        """
        import json

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO coverage_history (
                execution_id, file_path, timestamp, total_statements,
                covered_statements, coverage_percentage, missing_lines,
                space, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.execution_id,
                record.file_path,
                record.timestamp.isoformat(),
                record.total_statements,
                record.covered_statements,
                record.coverage_percentage,
                json.dumps(record.missing_lines) if record.missing_lines else None,
                record.space,
                json.dumps(record.metadata) if record.metadata else None,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def insert_coverage_summary(self, record: CoverageSummary) -> int:
        """
        Insert a coverage summary record.

        Args:
            record: CoverageSummary instance to insert

        Returns:
            Row ID of inserted record
        """
        import json

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO coverage_summary (
                execution_id, timestamp, total_coverage, files_analyzed,
                total_statements, covered_statements, space, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.execution_id,
                record.timestamp.isoformat(),
                record.total_coverage,
                record.files_analyzed,
                record.total_statements,
                record.covered_statements,
                record.space,
                json.dumps(record.metadata) if record.metadata else None,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_coverage_history(
        self,
        execution_id: Optional[str] = None,
        file_path: Optional[str] = None,
        space: Optional[str] = None,
        limit: int = 100,
    ) -> List[CoverageHistory]:
        """
        Query coverage history records.

        Args:
            execution_id: Filter by execution ID
            file_path: Filter by file path
            space: Filter by execution space
            limit: Maximum number of records to return

        Returns:
            List of CoverageHistory instances
        """
        import json

        cursor = self.connection.cursor()
        query = "SELECT * FROM coverage_history WHERE 1=1"
        params = []

        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)

        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        if space:
            query += " AND space = ?"
            params.append(space)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                CoverageHistory(
                    id=row[0],
                    execution_id=row[1],
                    file_path=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    total_statements=row[4],
                    covered_statements=row[5],
                    coverage_percentage=row[6],
                    missing_lines=json.loads(row[7]) if row[7] else None,
                    space=row[8],
                    metadata=json.loads(row[9]) if row[9] else None,
                )
            )

        return records

    def get_coverage_summary(
        self, execution_id: Optional[str] = None, space: Optional[str] = None, limit: int = 50
    ) -> List[CoverageSummary]:
        """
        Query coverage summary records.

        Args:
            execution_id: Filter by execution ID
            space: Filter by execution space
            limit: Maximum number of records to return

        Returns:
            List of CoverageSummary instances
        """
        import json

        cursor = self.connection.cursor()
        query = "SELECT * FROM coverage_summary WHERE 1=1"
        params = []

        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)

        if space:
            query += " AND space = ?"
            params.append(space)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                CoverageSummary(
                    id=row[0],
                    execution_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    total_coverage=row[3],
                    files_analyzed=row[4],
                    total_statements=row[5],
                    covered_statements=row[6],
                    space=row[7],
                    metadata=json.loads(row[8]) if row[8] else None,
                )
            )

        return records

    # Lint-related methods

    def insert_lint_violation(self, record: LintViolation) -> int:
        """
        Insert a lint violation record.

        Args:
            record: LintViolation record to insert

        Returns:
            Database ID of the inserted record
        """
        import json

        cursor = self.connection.cursor()
        metadata_json = json.dumps(record.metadata) if record.metadata else None

        cursor.execute(
            """
            INSERT INTO lint_violations
                (execution_id, file_path, line_number, column_number, severity, code,
                 message, validator, timestamp, space, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.execution_id,
                record.file_path,
                record.line_number,
                record.column_number,
                record.severity,
                record.code,
                record.message,
                record.validator,
                record.timestamp.isoformat(),
                record.space,
                metadata_json,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def insert_lint_summary(self, record: LintSummary) -> int:
        """
        Insert a lint summary record.

        Args:
            record: LintSummary record to insert

        Returns:
            Database ID of the inserted record
        """
        import json

        cursor = self.connection.cursor()
        by_code_json = json.dumps(record.by_code) if record.by_code else None
        metadata_json = json.dumps(record.metadata) if record.metadata else None

        cursor.execute(
            """
            INSERT INTO lint_summary
                (execution_id, timestamp, validator, files_scanned, total_violations,
                 errors, warnings, info, by_code, space, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.execution_id,
                record.timestamp.isoformat(),
                record.validator,
                record.files_scanned,
                record.total_violations,
                record.errors,
                record.warnings,
                record.info,
                by_code_json,
                record.space,
                metadata_json,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_lint_violations(
        self,
        execution_id: Optional[str] = None,
        file_path: Optional[str] = None,
        severity: Optional[str] = None,
        validator: Optional[str] = None,
        space: Optional[str] = None,
        limit: int = 100,
    ) -> List[LintViolation]:
        """
        Query lint violations.

        Args:
            execution_id: Filter by execution ID
            file_path: Filter by file path
            severity: Filter by severity (ERROR, WARNING, INFO)
            validator: Filter by validator (flake8, black, isort, etc.)
            space: Filter by execution space
            limit: Maximum number of records to return

        Returns:
            List of LintViolation instances
        """
        import json

        cursor = self.connection.cursor()
        query = "SELECT * FROM lint_violations WHERE 1=1"
        params = []

        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)

        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        if validator:
            query += " AND validator = ?"
            params.append(validator)

        if space:
            query += " AND space = ?"
            params.append(space)

        query += " ORDER BY timestamp DESC, file_path, line_number LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                LintViolation(
                    id=row[0],
                    execution_id=row[1],
                    file_path=row[2],
                    line_number=row[3],
                    column_number=row[4],
                    severity=row[5],
                    code=row[6],
                    message=row[7],
                    validator=row[8],
                    timestamp=datetime.fromisoformat(row[9]),
                    space=row[10],
                    metadata=json.loads(row[11]) if row[11] else None,
                )
            )

        return records

    def get_lint_summary(
        self,
        execution_id: Optional[str] = None,
        validator: Optional[str] = None,
        space: Optional[str] = None,
        limit: int = 50,
    ) -> List[LintSummary]:
        """
        Query lint summary records.

        Args:
            execution_id: Filter by execution ID
            validator: Filter by validator
            space: Filter by execution space
            limit: Maximum number of records to return

        Returns:
            List of LintSummary instances
        """
        import json

        cursor = self.connection.cursor()
        query = "SELECT * FROM lint_summary WHERE 1=1"
        params = []

        if execution_id:
            query += " AND execution_id = ?"
            params.append(execution_id)

        if validator:
            query += " AND validator = ?"
            params.append(validator)

        if space:
            query += " AND space = ?"
            params.append(space)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                LintSummary(
                    id=row[0],
                    execution_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    validator=row[3],
                    files_scanned=row[4],
                    total_violations=row[5],
                    errors=row[6],
                    warnings=row[7],
                    info=row[8],
                    by_code=json.loads(row[9]) if row[9] else None,
                    space=row[10],
                    metadata=json.loads(row[11]) if row[11] else None,
                )
            )

        return records

    def upsert_code_quality_metrics(self, record: CodeQualityMetrics) -> int:
        """
        Insert or update code quality metrics for a file.

        Args:
            record: CodeQualityMetrics record to upsert

        Returns:
            Database ID of the inserted/updated record
        """
        cursor = self.connection.cursor()

        last_scan_iso = record.last_scan.isoformat() if record.last_scan else None
        last_violation_iso = record.last_violation.isoformat() if record.last_violation else None
        last_updated_iso = record.last_updated.isoformat() if record.last_updated else None

        cursor.execute(
            """
            INSERT INTO code_quality_metrics
                (file_path, validator, total_scans, total_violations, avg_violations_per_scan,
                 most_common_code, last_scan, last_violation, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_path, validator) DO UPDATE SET
                total_scans = ?,
                total_violations = ?,
                avg_violations_per_scan = ?,
                most_common_code = ?,
                last_scan = ?,
                last_violation = ?,
                last_updated = ?
            """,
            (
                record.file_path,
                record.validator,
                record.total_scans,
                record.total_violations,
                record.avg_violations_per_scan,
                record.most_common_code,
                last_scan_iso,
                last_violation_iso,
                last_updated_iso,
                # UPDATE values
                record.total_scans,
                record.total_violations,
                record.avg_violations_per_scan,
                record.most_common_code,
                last_scan_iso,
                last_violation_iso,
                last_updated_iso,
            ),
        )

        self.connection.commit()
        return cursor.lastrowid

    def get_code_quality_metrics(
        self, file_path: Optional[str] = None, validator: Optional[str] = None
    ) -> List[CodeQualityMetrics]:
        """
        Query code quality metrics.

        Args:
            file_path: Filter by file path
            validator: Filter by validator

        Returns:
            List of CodeQualityMetrics instances
        """
        cursor = self.connection.cursor()
        query = "SELECT * FROM code_quality_metrics WHERE 1=1"
        params = []

        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        if validator:
            query += " AND validator = ?"
            params.append(validator)

        query += " ORDER BY avg_violations_per_scan DESC"

        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(
                CodeQualityMetrics(
                    id=row[0],
                    file_path=row[1],
                    validator=row[2],
                    total_scans=row[3],
                    total_violations=row[4],
                    avg_violations_per_scan=row[5],
                    most_common_code=row[6],
                    last_scan=datetime.fromisoformat(row[7]) if row[7] else None,
                    last_violation=datetime.fromisoformat(row[8]) if row[8] else None,
                    last_updated=datetime.fromisoformat(row[9]) if row[9] else None,
                )
            )

        return records


