"""
CI Health Analytics Module.

Analyzes CI workflow data to compute health metrics, identify trends,
and detect platform-specific issues.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import Scout's database components
import sys
from pathlib import Path

# Add scout to path if needed
scout_path = Path(__file__).parent.parent.parent.parent / "scout"
if scout_path.exists():
    sys.path.insert(0, str(scout_path))

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowJob, WorkflowRun, WorkflowTestResult


class CIHealthAnalyzer:
    """
    Analyzes CI workflow health metrics.

    Provides insights into CI pipeline stability, failure rates,
    platform-specific issues, and trends over time.
    """

    def __init__(self, scout_db_path: str):
        """
        Initialize the CI health analyzer.

        Args:
            scout_db_path: Path to Scout's database
        """
        self.db_manager = DatabaseManager(scout_db_path)
        self.db_manager.initialize()

    def get_ci_health_summary(
        self, days: int = 30, workflow_name: Optional[str] = None
    ) -> Dict:
        """
        Get overall CI health summary for the specified time window.

        Args:
            days: Number of days to analyze
            workflow_name: Filter by workflow name (None = all workflows)

        Returns:
            Dictionary with health metrics:
            {
                "total_runs": int,
                "successful_runs": int,
                "failed_runs": int,
                "success_rate": float,
                "avg_duration_seconds": float,
                "time_window": str
            }
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(WorkflowRun).filter(
                WorkflowRun.started_at >= cutoff_date
            )

            if workflow_name:
                query = query.filter_by(workflow_name=workflow_name)

            runs = query.all()

            if not runs:
                return {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "success_rate": 0.0,
                    "avg_duration_seconds": 0.0,
                    "time_window": f"Last {days} days",
                }

            successful = sum(1 for r in runs if r.conclusion == "success")
            failed = sum(1 for r in runs if r.conclusion == "failure")
            durations = [r.duration_seconds for r in runs if r.duration_seconds]

            return {
                "total_runs": len(runs),
                "successful_runs": successful,
                "failed_runs": failed,
                "success_rate": (successful / len(runs)) * 100 if runs else 0.0,
                "avg_duration_seconds": (
                    sum(durations) / len(durations) if durations else 0.0
                ),
                "time_window": f"Last {days} days",
            }

        finally:
            session.close()

    def get_platform_breakdown(
        self, days: int = 30, workflow_name: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Get CI results breakdown by platform.

        Args:
            days: Number of days to analyze
            workflow_name: Filter by workflow name

        Returns:
            Dictionary mapping platform to metrics:
            {
                "ubuntu-latest": {
                    "total_jobs": int,
                    "successful_jobs": int,
                    "failed_jobs": int,
                    "success_rate": float,
                    "avg_duration": float
                },
                ...
            }
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(WorkflowJob).join(WorkflowRun).filter(
                WorkflowRun.started_at >= cutoff_date
            )

            if workflow_name:
                query = query.filter(WorkflowRun.workflow_name == workflow_name)

            jobs = query.all()

            # Group by platform
            platform_stats = defaultdict(
                lambda: {
                    "total_jobs": 0,
                    "successful_jobs": 0,
                    "failed_jobs": 0,
                    "durations": [],
                }
            )

            for job in jobs:
                platform = job.runner_os or "unknown"
                platform_stats[platform]["total_jobs"] += 1

                if job.conclusion == "success":
                    platform_stats[platform]["successful_jobs"] += 1
                elif job.conclusion == "failure":
                    platform_stats[platform]["failed_jobs"] += 1

                if job.duration_seconds:
                    platform_stats[platform]["durations"].append(job.duration_seconds)

            # Calculate rates
            result = {}
            for platform, stats in platform_stats.items():
                total = stats["total_jobs"]
                durations = stats["durations"]

                result[platform] = {
                    "total_jobs": total,
                    "successful_jobs": stats["successful_jobs"],
                    "failed_jobs": stats["failed_jobs"],
                    "success_rate": (
                        (stats["successful_jobs"] / total * 100) if total else 0.0
                    ),
                    "avg_duration": (
                        sum(durations) / len(durations) if durations else 0.0
                    ),
                }

            return result

        finally:
            session.close()

    def get_failure_trends(
        self, days: int = 30, workflow_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get daily failure trends.

        Args:
            days: Number of days to analyze
            workflow_name: Filter by workflow name

        Returns:
            List of daily statistics:
            [{
                "date": str,
                "total_runs": int,
                "failed_runs": int,
                "failure_rate": float
            }, ...]
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(WorkflowRun).filter(
                WorkflowRun.started_at >= cutoff_date
            )

            if workflow_name:
                query = query.filter_by(workflow_name=workflow_name)

            runs = query.all()

            # Group by date
            daily_stats = defaultdict(lambda: {"total": 0, "failed": 0})

            for run in runs:
                if run.started_at:
                    date_key = run.started_at.strftime("%Y-%m-%d")
                    daily_stats[date_key]["total"] += 1
                    if run.conclusion == "failure":
                        daily_stats[date_key]["failed"] += 1

            # Convert to list and sort by date
            trends = []
            for date, stats in sorted(daily_stats.items()):
                failure_rate = (
                    (stats["failed"] / stats["total"] * 100) if stats["total"] else 0.0
                )
                trends.append(
                    {
                        "date": date,
                        "total_runs": stats["total"],
                        "failed_runs": stats["failed"],
                        "failure_rate": failure_rate,
                    }
                )

            return trends

        finally:
            session.close()

    def get_flaky_tests(
        self, days: int = 30, min_runs: int = 3, flakiness_threshold: float = 20.0
    ) -> List[Dict]:
        """
        Identify flaky tests (tests with inconsistent pass/fail behavior).

        Args:
            days: Number of days to analyze
            min_runs: Minimum test executions required
            flakiness_threshold: Minimum failure rate % to consider flaky

        Returns:
            List of flaky tests:
            [{
                "test_name": str,
                "total_runs": int,
                "failures": int,
                "failure_rate": float,
                "platforms": List[str]
            }, ...]
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = session.query(WorkflowTestResult).filter(
                WorkflowTestResult.timestamp >= cutoff_date
            )

            test_results = query.all()

            # Group by test nodeid
            test_stats = defaultdict(
                lambda: {"total": 0, "failures": 0, "platforms": set()}
            )

            for result in test_results:
                # Extract test name from nodeid
                parts = result.test_nodeid.split("::")
                test_name = parts[-1] if parts else result.test_nodeid

                test_stats[test_name]["total"] += 1
                if result.outcome == "failed":
                    test_stats[test_name]["failures"] += 1
                if result.runner_os:
                    test_stats[test_name]["platforms"].add(result.runner_os)

            # Filter flaky tests
            flaky = []
            for test_name, stats in test_stats.items():
                if stats["total"] < min_runs:
                    continue

                failure_rate = (stats["failures"] / stats["total"]) * 100

                # Flaky: has failures but not 100% failure rate
                if (
                    flakiness_threshold <= failure_rate < 100
                    and stats["failures"] > 0
                ):
                    flaky.append(
                        {
                            "test_name": test_name,
                            "total_runs": stats["total"],
                            "failures": stats["failures"],
                            "failure_rate": failure_rate,
                            "platforms": sorted(list(stats["platforms"])),
                        }
                    )

            # Sort by failure rate descending
            flaky.sort(key=lambda x: x["failure_rate"], reverse=True)

            return flaky

        finally:
            session.close()

    def get_slowest_jobs(
        self, days: int = 30, limit: int = 10, workflow_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get slowest CI jobs.

        Args:
            days: Number of days to analyze
            limit: Maximum number of jobs to return
            workflow_name: Filter by workflow name

        Returns:
            List of slowest jobs:
            [{
                "job_name": str,
                "run_id": int,
                "duration_seconds": int,
                "platform": str,
                "status": str
            }, ...]
        """
        session = self.db_manager.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = (
                session.query(WorkflowJob)
                .join(WorkflowRun)
                .filter(WorkflowRun.started_at >= cutoff_date)
                .filter(WorkflowJob.duration_seconds.isnot(None))
            )

            if workflow_name:
                query = query.filter(WorkflowRun.workflow_name == workflow_name)

            jobs = query.order_by(WorkflowJob.duration_seconds.desc()).limit(limit).all()

            return [
                {
                    "job_name": job.job_name,
                    "run_id": job.run_id,
                    "duration_seconds": job.duration_seconds,
                    "platform": job.runner_os or "unknown",
                    "status": f"{job.status}/{job.conclusion}",
                }
                for job in jobs
            ]

        finally:
            session.close()

    def close(self):
        """Close database connection."""
        # DatabaseManager doesn't expose a close method
        pass
