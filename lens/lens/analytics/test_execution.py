"""
Test execution analytics.

Provides analysis of test execution history from Anvil database,
including failure rates, flaky test detection, and execution trends.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TestExecutionAnalyzer:
    """Analyzer for test execution history."""

    def __init__(self, db_path: str = ".anvil/history.db"):
        """
        Initialize the test execution analyzer.

        Args:
            db_path: Path to Anvil execution history database
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connect to the database."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}. "
                "Run tests with Anvil to create execution history."
            )
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_execution_summary(self, days: int = 30) -> Dict:
        """
        Get summary of test executions.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with execution summary metrics
        """
        self.connect()
        try:
            cutoff = datetime.now() - timedelta(days=days)

            cursor = self.conn.cursor()

            # Total executions
            cursor.execute(
                """
                SELECT COUNT(*) as total
                FROM execution_history
                WHERE entity_type = 'test' AND timestamp > ?
                """,
                (cutoff,),
            )
            total = cursor.fetchone()["total"]

            # Pass/fail breakdown
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM execution_history
                WHERE entity_type = 'test' AND timestamp > ?
                GROUP BY status
                """,
                (cutoff,),
            )
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Unique tests
            cursor.execute(
                """
                SELECT COUNT(DISTINCT entity_id) as unique_tests
                FROM execution_history
                WHERE entity_type = 'test' AND timestamp > ?
                """,
                (cutoff,),
            )
            unique_tests = cursor.fetchone()["unique_tests"]

            # Average duration
            cursor.execute(
                """
                SELECT AVG(duration) as avg_duration
                FROM execution_history
                WHERE entity_type = 'test' AND timestamp > ? AND duration IS NOT NULL
                """,
                (cutoff,),
            )
            avg_duration = cursor.fetchone()["avg_duration"] or 0

            return {
                "total_executions": total,
                "unique_tests": unique_tests,
                "passed": status_counts.get("PASSED", 0),
                "failed": status_counts.get("FAILED", 0),
                "skipped": status_counts.get("SKIPPED", 0),
                "error": status_counts.get("ERROR", 0),
                "success_rate": (
                    status_counts.get("PASSED", 0) / total * 100 if total > 0 else 0
                ),
                "avg_duration": avg_duration,
                "window_days": days,
            }
        finally:
            self.close()

    def get_flaky_tests(
        self, threshold: float = 0.10, window: int = 20
    ) -> List[Dict]:
        """
        Get list of flaky tests.

        Args:
            threshold: Failure rate threshold (0.0-1.0)
            window: Number of recent executions to analyze

        Returns:
            List of flaky tests with statistics
        """
        self.connect()
        try:
            cursor = self.conn.cursor()

            # Get tests with failure rate above threshold
            cursor.execute(
                """
                SELECT
                    entity_id,
                    total_runs,
                    passed,
                    failed,
                    failure_rate,
                    avg_duration
                FROM entity_statistics
                WHERE entity_type = 'test'
                  AND failure_rate >= ?
                  AND failure_rate < 1.0
                  AND total_runs >= 3
                ORDER BY failure_rate DESC
                """,
                (threshold,),
            )

            flaky_tests = []
            for row in cursor.fetchall():
                flaky_tests.append(
                    {
                        "entity_id": row["entity_id"],
                        "total_runs": row["total_runs"],
                        "passed": row["passed"],
                        "failed": row["failed"],
                        "failure_rate": row["failure_rate"],
                        "avg_duration": row["avg_duration"],
                    }
                )

            return flaky_tests
        finally:
            self.close()

    def get_test_trends(self, days: int = 30) -> List[Dict]:
        """
        Get test execution trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            List of daily statistics
        """
        self.connect()
        try:
            cutoff = datetime.now() - timedelta(days=days)

            cursor = self.conn.cursor()

            # Daily statistics
            cursor.execute(
                """
                SELECT
                    DATE(timestamp) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'SKIPPED' THEN 1 ELSE 0 END) as skipped,
                    AVG(duration) as avg_duration
                FROM execution_history
                WHERE entity_type = 'test' AND timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY date
                """,
                (cutoff,),
            )

            trends = []
            for row in cursor.fetchall():
                total = row["total"]
                trends.append(
                    {
                        "date": row["date"],
                        "total": total,
                        "passed": row["passed"],
                        "failed": row["failed"],
                        "skipped": row["skipped"],
                        "success_rate": row["passed"] / total * 100 if total > 0 else 0,
                        "avg_duration": row["avg_duration"] or 0,
                    }
                )

            return trends
        finally:
            self.close()

    def get_slowest_tests(self, limit: int = 10) -> List[Dict]:
        """
        Get slowest tests by average duration.

        Args:
            limit: Number of tests to return

        Returns:
            List of slowest tests
        """
        self.connect()
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT
                    entity_id,
                    total_runs,
                    avg_duration
                FROM entity_statistics
                WHERE entity_type = 'test' AND avg_duration IS NOT NULL
                ORDER BY avg_duration DESC
                LIMIT ?
                """,
                (limit,),
            )

            slowest = []
            for row in cursor.fetchall():
                slowest.append(
                    {
                        "entity_id": row["entity_id"],
                        "total_runs": row["total_runs"],
                        "avg_duration": row["avg_duration"],
                    }
                )

            return slowest
        finally:
            self.close()

    def get_execution_rules(self) -> List[Dict]:
        """
        Get list of execution rules.

        Returns:
            List of execution rules
        """
        self.connect()
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT
                    name,
                    criteria,
                    enabled,
                    threshold,
                    window,
                    groups
                FROM execution_rules
                ORDER BY name
                """
            )

            rules = []
            for row in cursor.fetchall():
                rules.append(
                    {
                        "name": row["name"],
                        "criteria": row["criteria"],
                        "enabled": bool(row["enabled"]),
                        "threshold": row["threshold"],
                        "window": row["window"],
                        "groups": row["groups"],
                    }
                )

            return rules
        finally:
            self.close()
