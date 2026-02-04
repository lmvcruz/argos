"""
CI-specific storage layer for execution history.

Extends ExecutionDatabase with CI-focused queries, comparisons, and
platform-aware filtering to support Scout→Anvil integration for CI data.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory


@dataclass
class PlatformStatistics:
    """
    Statistics for a specific platform/Python version combination.

    Args:
        platform: OS name (ubuntu-latest, windows-latest, macos-latest)
        python_version: Python version (3.8, 3.9, etc.)
        total_runs: Total test executions on this platform
        passed: Number of passed tests
        failed: Number of failed tests
        skipped: Number of skipped tests
        avg_duration: Average test duration in seconds
        last_run: Timestamp of last execution
        failure_rate: Percentage of failed tests (0.0-1.0)
    """

    platform: str
    python_version: str
    total_runs: int
    passed: int
    failed: int
    skipped: int
    avg_duration: Optional[float]
    last_run: Optional[datetime]
    failure_rate: float


@dataclass
class ComparisonStatistics:
    """
    Comparison between local and CI executions.

    Args:
        entity_id: Test/entity identifier
        local_status: Status from local execution (PASSED, FAILED, SKIPPED)
        ci_status: Status from CI execution
        local_duration: Duration of local execution
        ci_duration: Duration of CI execution
        platform_specific: Whether failure is platform-specific
        platforms_failed: List of platforms where test failed in CI
    """

    entity_id: str
    local_status: Optional[str]
    ci_status: Optional[str]
    local_duration: Optional[float]
    ci_duration: Optional[float]
    platform_specific: bool
    platforms_failed: List[str]


class CIStorageLayer:
    """
    CI-specific storage operations for Anvil database.

    Provides methods to:
    - Query execution history filtered by space='ci'
    - Analyze platform-specific failures
    - Compare local vs CI execution results
    - Track execution trends across workflows
    """

    def __init__(self, db: ExecutionDatabase):
        """
        Initialize CI storage layer.

        Args:
            db: ExecutionDatabase instance
        """
        self.db = db

    def get_ci_executions(
        self,
        entity_id: Optional[str] = None,
        entity_type: str = "test",
        limit: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[ExecutionHistory]:
        """
        Get CI executions (space='ci') for an entity.

        Args:
            entity_id: Filter by entity ID (optional)
            entity_type: Filter by entity type (default: test)
            limit: Maximum number of records (optional)
            days: Only include last N days of executions (optional)

        Returns:
            List of ExecutionHistory records from CI
        """
        cursor = self.db.connection.cursor()

        query = "SELECT * FROM execution_history WHERE space='ci' AND entity_type=?"
        params = [entity_type]

        if entity_id:
            query += " AND entity_id=?"
            params.append(entity_id)

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            query += " AND timestamp > ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)

        import json

        records = []
        for row in cursor.fetchall():
            metadata = json.loads(row[8]) if row[8] else None
            record = ExecutionHistory(
                execution_id=row[1],
                entity_id=row[2],
                entity_type=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                status=row[5],
                duration=row[6],
                space=row[7],
                metadata=metadata,
                id=row[0],
            )
            records.append(record)

        return records

    def get_local_executions(
        self,
        entity_id: Optional[str] = None,
        entity_type: str = "test",
        limit: Optional[int] = None,
        days: Optional[int] = None,
    ) -> List[ExecutionHistory]:
        """
        Get local executions (space='local') for an entity.

        Args:
            entity_id: Filter by entity ID (optional)
            entity_type: Filter by entity type (default: test)
            limit: Maximum number of records (optional)
            days: Only include last N days of executions (optional)

        Returns:
            List of ExecutionHistory records from local
        """
        cursor = self.db.connection.cursor()

        query = "SELECT * FROM execution_history WHERE space='local' AND entity_type=?"
        params = [entity_type]

        if entity_id:
            query += " AND entity_id=?"
            params.append(entity_id)

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            query += " AND timestamp > ?"
            params.append(cutoff.isoformat())

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)

        import json

        records = []
        for row in cursor.fetchall():
            metadata = json.loads(row[8]) if row[8] else None
            record = ExecutionHistory(
                execution_id=row[1],
                entity_id=row[2],
                entity_type=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                status=row[5],
                duration=row[6],
                space=row[7],
                metadata=metadata,
                id=row[0],
            )
            records.append(record)

        return records

    def get_ci_statistics_by_platform(
        self,
        entity_type: str = "test",
        limit_days: int = 30,
    ) -> List[PlatformStatistics]:
        """
        Get CI statistics aggregated by platform and Python version.

        Args:
            entity_type: Filter by entity type (default: test)
            limit_days: Days of history to consider (default: 30)

        Returns:
            List of PlatformStatistics for each platform/Python combination
        """
        cursor = self.db.connection.cursor()

        cutoff = datetime.now() - timedelta(days=limit_days)

        # Query CI executions grouped by platform and python_version
        query = """
        SELECT
            json_extract(metadata, '$.platform') as platform,
            json_extract(metadata, '$.python_version') as python_version,
            COUNT(*) as total_runs,
            SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END) as passed,
            SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status='SKIPPED' THEN 1 ELSE 0 END) as skipped,
            AVG(duration) as avg_duration,
            MAX(timestamp) as last_run
        FROM execution_history
        WHERE space='ci' AND entity_type=? AND timestamp > ?
        GROUP BY platform, python_version
        ORDER BY platform, python_version
        """

        cursor.execute(query, [entity_type, cutoff.isoformat()])

        stats = []
        for row in cursor.fetchall():
            platform, py_version, total, passed, failed, skipped, avg_dur, last_run = row
            failure_rate = failed / total if total > 0 else 0.0

            stat = PlatformStatistics(
                platform=platform or "unknown",
                python_version=py_version or "unknown",
                total_runs=total,
                passed=passed,
                failed=failed,
                skipped=skipped,
                avg_duration=avg_dur,
                last_run=datetime.fromisoformat(last_run) if last_run else None,
                failure_rate=failure_rate,
            )
            stats.append(stat)

        return stats

    def compare_local_vs_ci(
        self,
        entity_type: str = "test",
        limit_days: int = 30,
    ) -> List[ComparisonStatistics]:
        """
        Compare local vs CI execution results for entities.

        Args:
            entity_type: Filter by entity type (default: test)
            limit_days: Days of history to consider (default: 30)

        Returns:
            List of ComparisonStatistics showing differences
        """
        cutoff = datetime.now() - timedelta(days=limit_days)

        # Get all entities tested in both spaces
        cursor = self.db.connection.cursor()
        cursor.execute(
            """
        SELECT DISTINCT entity_id FROM execution_history
        WHERE entity_type=? AND timestamp > ?
        ORDER BY entity_id
        """,
            [entity_type, cutoff.isoformat()],
        )

        entities = [row[0] for row in cursor.fetchall()]
        comparisons = []

        for entity_id in entities:
            # Get most recent local execution
            local_execs = self.get_local_executions(
                entity_id=entity_id,
                entity_type=entity_type,
                limit=1,
                days=limit_days,
            )
            local_status = local_execs[0].status if local_execs else None
            local_duration = local_execs[0].duration if local_execs else None

            # Get most recent CI execution
            ci_execs = self.get_ci_executions(
                entity_id=entity_id,
                entity_type=entity_type,
                limit=1,
                days=limit_days,
            )
            ci_status = ci_execs[0].status if ci_execs else None
            ci_duration = ci_execs[0].duration if ci_execs else None

            # Check if failure is platform-specific
            platforms_failed = []
            if ci_execs:
                # Get all CI executions for this entity
                all_ci = self.get_ci_executions(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    days=limit_days,
                )
                failed_platforms = set()
                for record in all_ci:
                    if record.status == "FAILED" and record.metadata:
                        platform = record.metadata.get("platform")
                        if platform:
                            failed_platforms.add(platform)
                platforms_failed = list(failed_platforms)

            platform_specific = len(platforms_failed) > 0 and len(platforms_failed) < 3

            comparison = ComparisonStatistics(
                entity_id=entity_id,
                local_status=local_status,
                ci_status=ci_status,
                local_duration=local_duration,
                ci_duration=ci_duration,
                platform_specific=platform_specific,
                platforms_failed=platforms_failed,
            )
            comparisons.append(comparison)

        return comparisons

    def get_platform_specific_failures(
        self,
        entity_type: str = "test",
        limit_days: int = 30,
    ) -> Dict[str, List[str]]:
        """
        Get tests that fail only on specific platforms.

        Args:
            entity_type: Filter by entity type (default: test)
            limit_days: Days of history to consider (default: 30)

        Returns:
            Dict mapping platform names to lists of failing tests
        """
        comparisons = self.compare_local_vs_ci(entity_type, limit_days)

        platform_failures = {}

        for comp in comparisons:
            if comp.platform_specific and comp.platforms_failed:
                for platform in comp.platforms_failed:
                    if platform not in platform_failures:
                        platform_failures[platform] = []
                    platform_failures[platform].append(comp.entity_id)

        return platform_failures

    def get_ci_health_summary(
        self,
        entity_type: str = "test",
        limit_days: int = 30,
    ) -> Dict[str, any]:
        """
        Get overall CI health summary.

        Args:
            entity_type: Filter by entity type (default: test)
            limit_days: Days of history to consider (default: 30)

        Returns:
            Dict with summary statistics
        """
        cursor = self.db.connection.cursor()

        cutoff = datetime.now() - timedelta(days=limit_days)

        # Get overall CI statistics
        query = """
        SELECT
            COUNT(*) as total_runs,
            SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END) as passed,
            SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status='SKIPPED' THEN 1 ELSE 0 END) as skipped,
            AVG(duration) as avg_duration,
            MAX(timestamp) as last_run
        FROM execution_history
        WHERE space='ci' AND entity_type=? AND timestamp > ?
        """

        cursor.execute(query, [entity_type, cutoff.isoformat()])
        row = cursor.fetchone()

        if not row or row[0] == 0:
            return {
                "total_runs": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "avg_duration": None,
                "last_run": None,
                "pass_rate": 0.0,
                "failure_rate": 0.0,
                "days_included": limit_days,
            }

        total, passed, failed, skipped, avg_dur, last_run = row

        return {
            "total_runs": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "avg_duration": avg_dur,
            "last_run": datetime.fromisoformat(last_run) if last_run else None,
            "pass_rate": passed / total if total > 0 else 0.0,
            "failure_rate": failed / total if total > 0 else 0.0,
            "days_included": limit_days,
        }

    def get_flaky_tests_in_ci(
        self,
        failure_threshold: float = 0.10,
        min_runs: int = 5,
        limit_days: int = 30,
    ) -> List[Tuple[str, float, int]]:
        """
        Identify flaky tests (intermittently failing in CI).

        Args:
            failure_threshold: Failure rate threshold to consider flaky (0.0-1.0)
            min_runs: Minimum executions required to evaluate
            limit_days: Days of history to consider

        Returns:
            List of (entity_id, failure_rate, total_runs) for flaky tests
        """
        cursor = self.db.connection.cursor()

        cutoff = datetime.now() - timedelta(days=limit_days)

        query = """
        SELECT
            entity_id,
            COUNT(*) as total_runs,
            SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) as failed_count
        FROM execution_history
        WHERE space='ci' AND entity_type='test' AND timestamp > ?
        GROUP BY entity_id
        HAVING COUNT(*) >= ? AND (CAST(failed_count AS FLOAT) / COUNT(*)) > ?
        ORDER BY (CAST(failed_count AS FLOAT) / COUNT(*)) DESC
        """

        cursor.execute(query, [cutoff.isoformat(), min_runs, failure_threshold])

        flaky = []
        for row in cursor.fetchall():
            entity_id, total_runs, failed_count = row
            failure_rate = failed_count / total_runs if total_runs > 0 else 0.0
            flaky.append((entity_id, failure_rate, total_runs))

        return flaky
