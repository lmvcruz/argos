"""
Scout→Anvil CI integration layer.

Bridges Scout CI log syncing with Anvil database storage, converting
Scout's parsed CI results into Anvil ExecutionHistory records.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory


class ScoutAnvilBridge:
    """
    Integration layer between Scout CI sync and Anvil database.

    Converts Scout's CI log parsing results into Anvil ExecutionHistory
    records for storage and analysis.
    """

    def __init__(self, db: ExecutionDatabase):
        """
        Initialize Scout→Anvil bridge.

        Args:
            db: ExecutionDatabase instance for storage
        """
        self.db = db

    def store_pytest_results(
        self,
        run_id: int,
        job_name: str,
        test_results: List[Dict[str, Any]],
        platform: str,
        python_version: str,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Store pytest results from Scout's PytestParser.

        Args:
            run_id: GitHub Actions workflow run ID
            job_name: Job name from GitHub Actions
            test_results: List of parsed test result dicts from PytestParser
                Expected format: [
                    {
                        "test_path": "tests/test_example.py::test_func",
                        "status": "PASSED",  # or FAILED, SKIPPED
                        "duration": 1.23,
                        "error_message": None  # if failed
                    },
                    ...
                ]
            platform: OS name (ubuntu-latest, windows-latest, macos-latest)
            python_version: Python version (3.8, 3.9, etc.)
            timestamp: Execution timestamp (defaults to now)

        Returns:
            Total number of records stored
        """
        if timestamp is None:
            timestamp = datetime.now()

        stored_count = 0

        for result in test_results:
            test_path = result.get("test_path")
            status = result.get("status", "FAILED")
            duration = result.get("duration")
            error_message = result.get("error_message")

            if not test_path:
                continue

            # Create metadata with CI context
            metadata = {
                "run_id": run_id,
                "job_name": job_name,
                "platform": platform,
                "python_version": python_version,
            }

            if error_message:
                metadata["error_message"] = error_message

            # Create execution history record
            test_path_safe = test_path.replace("::", "_").replace("/", "_")
            execution_id = f"ci-{run_id}-{job_name}-{test_path_safe}"
            execution_id = execution_id[:100]  # Truncate if too long

            record = ExecutionHistory(
                execution_id=execution_id,
                entity_id=test_path,
                entity_type="test",
                timestamp=timestamp,
                status=status,
                duration=duration,
                space="ci",
                metadata=metadata,
            )

            self.db.insert_execution_history(record)
            stored_count += 1

        return stored_count

    def store_lint_results(
        self,
        run_id: int,
        job_name: str,
        lint_results: List[Dict[str, Any]],
        tool_name: str,
        platform: str = "ubuntu-latest",
        python_version: str = "3.11",
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Store lint results from Scout's linting parsers.

        Args:
            run_id: GitHub Actions workflow run ID
            job_name: Job name from GitHub Actions
            lint_results: List of linting violation dicts
                Expected format: [
                    {
                        "file_path": "anvil/models/metadata.py",
                        "line": 42,
                        "column": 5,
                        "code": "E302",
                        "message": "expected 2 blank lines, found 1",
                        "severity": "error"
                    },
                    ...
                ]
            tool_name: Linter name (flake8, black, isort, etc.)
            platform: OS name (default: ubuntu-latest)
            python_version: Python version (default: 3.11)
            timestamp: Execution timestamp (defaults to now)

        Returns:
            Total number of violation records stored
        """
        if timestamp is None:
            timestamp = datetime.now()

        stored_count = 0

        for violation in lint_results:
            file_path = violation.get("file_path")
            line = violation.get("line")
            code = violation.get("code")
            message = violation.get("message")

            if not file_path or not code:
                continue

            # Create metadata
            metadata = {
                "run_id": run_id,
                "job_name": job_name,
                "tool": tool_name,
                "platform": platform,
                "python_version": python_version,
                "line": line,
                "code": code,
                "message": message,
            }

            # Create entity_id from file and code
            entity_id = f"{file_path}:{code}"

            # Create execution history record (status is always the violation code)
            execution_id = f"ci-{run_id}-{tool_name}-{file_path.replace('/', '_')}-{code}"
            execution_id = execution_id[:100]

            record = ExecutionHistory(
                execution_id=execution_id,
                entity_id=entity_id,
                entity_type="lint",
                timestamp=timestamp,
                status="VIOLATION",
                duration=None,
                space="ci",
                metadata=metadata,
            )

            self.db.insert_execution_history(record)
            stored_count += 1

        return stored_count

    def store_coverage_results(
        self,
        run_id: int,
        job_name: str,
        coverage_data: Dict[str, Any],
        platform: str,
        python_version: str,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Store coverage results from Scout's CoverageParser.

        Args:
            run_id: GitHub Actions workflow run ID
            job_name: Job name from GitHub Actions
            coverage_data: Coverage report dict
                Expected format: {
                    "total_coverage": 95.5,
                    "files": [
                        {
                            "file_path": "anvil/models/metadata.py",
                            "coverage": 98.0,
                            "missing_lines": [42, 43, 44]
                        },
                        ...
                    ]
                }
            platform: OS name (ubuntu-latest, windows-latest, macos-latest)
            python_version: Python version (3.8, 3.9, etc.)
            timestamp: Execution timestamp (defaults to now)

        Returns:
            Total number of coverage records stored
        """
        if timestamp is None:
            timestamp = datetime.now()

        stored_count = 0

        total_coverage = coverage_data.get("total_coverage")

        # Store overall coverage record
        if total_coverage is not None:
            metadata = {
                "run_id": run_id,
                "job_name": job_name,
                "platform": platform,
                "python_version": python_version,
                "type": "overall",
            }

            execution_id = f"ci-{run_id}-coverage-overall"

            record = ExecutionHistory(
                execution_id=execution_id,
                entity_id="coverage",
                entity_type="coverage",
                timestamp=timestamp,
                status="PASSED" if total_coverage >= 90 else "FAILED",
                duration=None,
                space="ci",
                metadata=metadata,
            )

            self.db.insert_execution_history(record)
            stored_count += 1

        # Store per-file coverage records
        files = coverage_data.get("files", [])
        for file_coverage in files:
            file_path = file_coverage.get("file_path")
            coverage_pct = file_coverage.get("coverage")

            if not file_path or coverage_pct is None:
                continue

            metadata = {
                "run_id": run_id,
                "job_name": job_name,
                "platform": platform,
                "python_version": python_version,
                "type": "file",
                "missing_lines": file_coverage.get("missing_lines", []),
            }

            execution_id = f"ci-{run_id}-coverage-{file_path.replace('/', '_')}"
            execution_id = execution_id[:100]

            record = ExecutionHistory(
                execution_id=execution_id,
                entity_id=f"coverage:{file_path}",
                entity_type="coverage",
                timestamp=timestamp,
                status="PASSED" if coverage_pct >= 90 else "FAILED",
                duration=None,
                space="ci",
                metadata=metadata,
            )

            self.db.insert_execution_history(record)
            stored_count += 1

        return stored_count

    def store_workflow_run(
        self,
        run_id: int,
        workflow_name: str,
        run_conclusion: str,
        run_timestamp: datetime,
        jobs_data: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Store complete workflow run results.

        Args:
            run_id: GitHub Actions workflow run ID
            workflow_name: Workflow name (e.g., "Anvil Tests")
            run_conclusion: Overall run status (success, failure, etc.)
            run_timestamp: When the run was executed
            jobs_data: List of job execution dicts
                Expected format: [
                    {
                        "job_name": "test",
                        "job_conclusion": "success",
                        "platform": "ubuntu-latest",
                        "python_version": "3.11",
                        "parsed_data": {...}  # output from parsers
                    },
                    ...
                ]

        Returns:
            Dict with counts: {"tests": N, "lint": M, "coverage": K}
        """
        counts = {"tests": 0, "lint": 0, "coverage": 0}

        for job in jobs_data:
            job_name = job.get("job_name")
            platform = job.get("platform", "ubuntu-latest")
            python_version = job.get("python_version", "3.11")
            parsed_data = job.get("parsed_data", {})

            if not parsed_data:
                continue

            # Route to appropriate storage method based on parser output
            if "tests" in parsed_data:
                count = self.store_pytest_results(
                    run_id=run_id,
                    job_name=job_name,
                    test_results=parsed_data["tests"],
                    platform=platform,
                    python_version=python_version,
                    timestamp=run_timestamp,
                )
                counts["tests"] += count

            if "lint_violations" in parsed_data:
                tool_name = parsed_data.get("tool_name", "generic")
                count = self.store_lint_results(
                    run_id=run_id,
                    job_name=job_name,
                    lint_results=parsed_data["lint_violations"],
                    tool_name=tool_name,
                    platform=platform,
                    python_version=python_version,
                    timestamp=run_timestamp,
                )
                counts["lint"] += count

            if "coverage" in parsed_data:
                count = self.store_coverage_results(
                    run_id=run_id,
                    job_name=job_name,
                    coverage_data=parsed_data["coverage"],
                    platform=platform,
                    python_version=python_version,
                    timestamp=run_timestamp,
                )
                counts["coverage"] += count

        return counts

    def get_ci_workflow_summary(self, run_id: int) -> Dict[str, Any]:
        """
        Get summary of all CI data stored for a workflow run.

        Args:
            run_id: GitHub Actions workflow run ID

        Returns:
            Dict with summary statistics
        """
        cursor = self.db.connection.cursor()

        # Get counts by entity type
        cursor.execute(
            """
        SELECT entity_type, COUNT(*),
               SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END),
               SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END)
        FROM execution_history
        WHERE space='ci' AND metadata LIKE ?
        GROUP BY entity_type
        """,
            [f"%{run_id}%"],
        )

        summary = {
            "run_id": run_id,
            "by_type": {},
            "total_records": 0,
        }

        for row in cursor.fetchall():
            entity_type, total, passed, failed = row
            summary["by_type"][entity_type] = {
                "total": total,
                "passed": passed or 0,
                "failed": failed or 0,
            }
            summary["total_records"] += total

        return summary
