"""
Scout API endpoints for CI data access and analysis.

Provides REST endpoints for querying CI workflow data, comparing runs,
analyzing failures, and detecting performance trends.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


def register_scout_endpoints(app, scout_db_path: Optional[str] = None):
    """
    Register Scout-related endpoints with the FastAPI app.

    Args:
        app: FastAPI application instance
        scout_db_path: Path to Scout database (default: .anvil/scout.db)
    """
    if scout_db_path is None:
        scout_db_path = ".anvil/scout.db"

    scout_db_path = Path(scout_db_path)

    # ===== Workflow Management =====

    @app.get("/api/scout/workflows")
    async def list_workflows(
        branch: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List workflow runs with optional filtering.

        Args:
            branch: Filter by branch name (optional)
            status: Filter by status (success, failure, pending) (optional)
            limit: Maximum number of results (default: 50)
            offset: Number of results to skip (default: 0)

        Returns:
            Dictionary with workflows list and pagination info
        """
        try:
            # Check if Scout module is available
            try:
                from scout.storage import DatabaseManager, WorkflowRun
            except ImportError:
                logger.warning(
                    "Scout module not found. Please ensure scout is installed.")
                return {
                    "error": "Scout module not available. Please install scout package.",
                    "workflows": [],
                    "sync_status": {
                        "last_sync": None,
                        "is_syncing": False,
                        "next_sync": None,
                    },
                    "total": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # Check if database exists
            if not scout_db_path.exists():
                logger.warning(
                    f"Scout database not found at {scout_db_path}. No data available.")
                return {
                    "error": f"Scout database not found at {scout_db_path}. Please run Scout sync first.",
                    "workflows": [],
                    "sync_status": {
                        "last_sync": None,
                        "is_syncing": False,
                        "next_sync": None,
                    },
                    "total": 0,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                # Build query
                query = session.query(WorkflowRun)

                if branch:
                    query = query.filter(WorkflowRun.branch == branch)
                if status:
                    query = query.filter(WorkflowRun.status == status)

                # Get total count before pagination
                total = query.count()

                # Apply pagination and ordering
                workflows_data = (
                    query.order_by(WorkflowRun.id.desc())
                    .offset(offset)
                    .limit(limit)
                    .all()
                )

                # Convert to dict format
                workflows = [
                    {
                        "id": w.id,
                        "run_id": w.run_id,
                        "workflow_name": w.workflow_name,
                        "branch": w.branch,
                        "status": w.status,
                        "conclusion": w.conclusion,
                        "started_at": w.started_at.isoformat() if w.started_at else None,
                        "completed_at": w.completed_at.isoformat() if w.completed_at else None,
                        "duration_seconds": w.duration_seconds,
                        "url": w.url,
                    }
                    for w in workflows_data
                ]
            finally:
                session.close()

            # Get last sync time
            last_sync = None
            if scout_db_path.exists():
                mtime = scout_db_path.stat().st_mtime
                last_sync = datetime.fromtimestamp(mtime).isoformat()

            return {
                "workflows": [
                    {
                        "id": w.id,
                        "run_id": w.run_id,
                        "name": w.workflow_name,
                        "run_number": w.run_number,
                        "branch": w.branch,
                        "status": w.status,
                        "conclusion": w.conclusion,
                        "started_at": w.started_at.isoformat() if w.started_at else None,
                        "completed_at": (
                            w.completed_at.isoformat() if w.completed_at else None
                        ),
                        "duration_seconds": w.duration_seconds,
                        "url": w.url,
                    }
                    for w in workflows
                ],
                "sync_status": {
                    "last_sync": last_sync,
                    "is_syncing": False,
                    "next_sync": (
                        datetime.fromisoformat(last_sync) + timedelta(hours=1)
                    ).isoformat()
                    if last_sync
                    else None,
                },
                "total": total,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}", exc_info=True)
            return {
                "error": f"Failed to fetch workflows: {str(e)}",
                "workflows": [],
                "sync_status": {
                    "last_sync": None,
                    "is_syncing": False,
                    "next_sync": None,
                },
                "total": 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

    @app.get("/api/scout/workflows/{workflow_id}")
    async def get_workflow_details(workflow_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific workflow run.

        Args:
            workflow_id: ID of the workflow run

        Returns:
            Workflow details including jobs and test results
        """
        try:
            from scout.storage import DatabaseManager, WorkflowRun, WorkflowJob

            if not scout_db_path.exists():
                return {"error": f"Scout database not found. No workflow data available."}

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                workflow = session.query(WorkflowRun).filter(
                    WorkflowRun.id == workflow_id).first()

                if not workflow:
                    return {"error": f"Workflow {workflow_id} not found"}

                # Get jobs for this workflow
                jobs = session.query(WorkflowJob).filter(
                    WorkflowJob.run_id == workflow.run_id).all()

                return {
                    "id": workflow.id,
                    "run_id": workflow.run_id,
                    "name": workflow.workflow_name,
                    "run_number": workflow.run_number,
                    "branch": workflow.branch,
                    "status": workflow.status,
                    "conclusion": workflow.conclusion,
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": (
                        workflow.completed_at.isoformat() if workflow.completed_at else None
                    ),
                    "duration_seconds": workflow.duration_seconds,
                    "url": workflow.url,
                    "jobs": [
                        {
                            "id": j.id,
                            "job_id": j.job_id,
                            "name": j.job_name,
                            "runner_os": j.runner_os,
                            "python_version": j.python_version,
                            "status": j.status,
                            "conclusion": j.conclusion,
                            "started_at": j.started_at.isoformat() if j.started_at else None,
                            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                            "duration_seconds": j.duration_seconds,
                            "logs_url": j.logs_url,
                        }
                        for j in jobs
                    ],
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get workflow details: {e}")
            return {"error": str(e)}

    # ===== Job Details =====

    @app.get("/api/scout/jobs/{job_id}/tests")
    async def get_job_tests(job_id: int) -> Dict[str, Any]:
        """
        Get test results for a specific job.

        Args:
            job_id: ID of the job

        Returns:
            List of test results for the job
        """
        try:
            from scout.storage import DatabaseManager, WorkflowTestResult

            if not scout_db_path.exists():
                return {"error": f"Scout database not found.", "job_id": job_id, "tests": []}

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                tests = session.query(WorkflowTestResult).filter(
                    WorkflowTestResult.job_id == job_id).all()

                return {
                    "job_id": job_id,
                    "tests": [
                        {
                            "id": t.id,
                            "nodeid": t.test_nodeid,
                            "outcome": t.outcome,
                            "duration": t.duration,
                            "error_message": t.error_message,
                            "runner_os": t.runner_os,
                            "python_version": t.python_version,
                            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        }
                        for t in tests
                    ],
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get job tests: {e}")
            return {"error": str(e), "job_id": job_id, "tests": []}

    # ===== Sync Status =====

    @app.get("/api/scout/sync-status")
    async def get_sync_status() -> Dict[str, Any]:
        """
        Get current sync status for Scout data.

        Returns:
            Sync status information including last sync time and stats
        """
        try:
            from scout.storage import DatabaseManager, WorkflowRun, WorkflowJob

            if not scout_db_path.exists():
                return {
                    "last_sync": None,
                    "status": "empty",
                    "workflow_count": 0,
                    "job_count": 0,
                    "next_sync": None,
                }

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                workflow_count = session.query(WorkflowRun).count()
                job_count = session.query(WorkflowJob).count()
            finally:
                session.close()

            # Check database file modification time
            mtime = scout_db_path.stat().st_mtime
            last_sync = datetime.fromtimestamp(mtime)

            return {
                "last_sync": last_sync.isoformat() if last_sync else None,
                "status": "synced" if workflow_count > 0 else "empty",
                "workflow_count": workflow_count,
                "job_count": job_count,
                "next_sync": (last_sync + timedelta(hours=1)).isoformat()
                if last_sync
                else None,
            }
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {"error": str(e), "status": "error"}

    # ===== Run Comparison =====

    @app.get("/api/scout/workflows/{workflow_id1}/compare/{workflow_id2}")
    async def compare_workflows(workflow_id1: int, workflow_id2: int) -> Dict[str, Any]:
        """
        Compare two workflow runs to identify differences.

        Args:
            workflow_id1: ID of first workflow
            workflow_id2: ID of second workflow

        Returns:
            Comparison results including job differences and test results
        """
        try:
            from scout.storage import DatabaseManager, WorkflowRun, WorkflowJob

            if not scout_db_path.exists():
                return {"error": "Scout database not found"}

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                w1 = session.query(WorkflowRun).filter(
                    WorkflowRun.id == workflow_id1).first()
                w2 = session.query(WorkflowRun).filter(
                    WorkflowRun.id == workflow_id2).first()

                if not w1 or not w2:
                    return {"error": "One or both workflows not found"}

                jobs1 = {j.job_id: j for j in session.query(
                    WorkflowJob).filter(WorkflowJob.run_id == w1.run_id).all()}
                jobs2 = {j.job_id: j for j in session.query(
                    WorkflowJob).filter(WorkflowJob.run_id == w2.run_id).all()}

                # Find differences
                common_jobs = set(jobs1.keys()) & set(jobs2.keys())
                new_jobs = set(jobs2.keys()) - set(jobs1.keys())
                removed_jobs = set(jobs1.keys()) - set(jobs2.keys())

                comparison = {
                    "workflow_1": {
                        "id": w1.id,
                        "run_number": w1.run_number,
                        "conclusion": w1.conclusion,
                        "duration": w1.duration_seconds,
                        "timestamp": w1.started_at.isoformat() if w1.started_at else None,
                    },
                    "workflow_2": {
                        "id": w2.id,
                        "run_number": w2.run_number,
                        "conclusion": w2.conclusion,
                        "duration": w2.duration_seconds,
                        "timestamp": w2.started_at.isoformat() if w2.started_at else None,
                    },
                    "duration_delta": (w2.duration_seconds or 0) - (w1.duration_seconds or 0),
                    "job_changes": {
                        "common": len(common_jobs),
                        "new": len(new_jobs),
                        "removed": len(removed_jobs),
                    },
                    "job_details": [
                        {
                            "job_id": jid,
                            "job_1_duration": jobs1[jid].duration_seconds,
                            "job_2_duration": jobs2[jid].duration_seconds,
                            "duration_delta": (
                                (jobs2[jid].duration_seconds or 0)
                                - (jobs1[jid].duration_seconds or 0)
                            ),
                            "status_change": (
                                jobs1[jid].conclusion,
                                jobs2[jid].conclusion,
                            ),
                        }
                        for jid in common_jobs
                    ],
                }

                return comparison
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to compare workflows: {e}")
            return {"error": str(e)}

    # ===== Failure Analysis =====

    @app.get("/api/scout/analytics/failures")
    async def get_failure_analytics(
        days: int = 7, limit: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze failure patterns over time.

        Args:
            days: Number of days to analyze (default: 7)
            limit: Maximum number of failures to return

        Returns:
            Failure patterns and statistics
        """
        try:
            from scout.storage import DatabaseManager, WorkflowTestResult

            if not scout_db_path.exists():
                return {"error": "Scout database not found", "total_failures": 0}

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                # Get failures from the last N days
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                failures = session.query(WorkflowTestResult).filter(
                    WorkflowTestResult.outcome == 'failed',
                    WorkflowTestResult.timestamp >= cutoff_date
                ).all()

                # Group by test and count
                failure_counts = Counter()
                failure_details = defaultdict(list)

                for f in failures:
                    failure_counts[f.test_nodeid] += 1
                    failure_details[f.test_nodeid].append(
                        {
                            "error_message": f.error_message,
                            "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                        }
                    )

                # Get top failures
                top_failures = failure_counts.most_common(limit)

                return {
                    "period_days": days,
                    "total_failures": len(failures),
                    "unique_failing_tests": len(failure_counts),
                    "top_failures": [
                        {
                            "test": test,
                            "count": count,
                            # Last 3 errors
                            "recent_errors": failure_details[test][-3:],
                        }
                        for test, count in top_failures
                    ],
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get failure analytics: {e}")
            return {"error": str(e), "total_failures": 0}

    # ===== Flaky Tests =====

    @app.get("/api/scout/analytics/flaky-tests")
    async def get_flaky_tests(days: int = 30, threshold: float = 0.3) -> Dict[str, Any]:
        """
        Detect flaky tests (tests that pass and fail intermittently).

        Args:
            days: Number of days to analyze (default: 30)
            threshold: Pass rate threshold for flakiness (0.0-1.0, default: 0.3)

        Returns:
            List of flaky tests with pass/fail rates
        """
        try:
            from scout.storage import DatabaseManager, WorkflowTestResult

            if not scout_db_path.exists():
                return {"error": "Scout database not found", "flaky_tests": []}

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                test_results = session.query(WorkflowTestResult).filter(
                    WorkflowTestResult.timestamp >= cutoff_date
                ).all()

                # Count pass/fail by test
                test_stats = defaultdict(
                    lambda: {"passed": 0, "failed": 0, "skipped": 0})

                for result in test_results:
                    test_stats[result.test_nodeid][result.outcome] += 1

                # Find flaky tests
                flaky_tests = []
                for test, stats in test_stats.items():
                    total = stats["passed"] + \
                        stats["failed"] + stats["skipped"]
                    if total == 0:
                        continue

                    pass_rate = stats["passed"] / total
                    fail_rate = stats["failed"] / total

                    # Flaky if both pass and fail rates are significant
                    if (
                        threshold <= pass_rate <= (1 - threshold)
                        and fail_rate > threshold
                    ):
                        flaky_tests.append(
                            {
                                "test": test,
                                "pass_rate": round(pass_rate, 2),
                                "fail_rate": round(fail_rate, 2),
                                "skip_rate": round(stats["skipped"] / total, 2),
                                "total_runs": total,
                            }
                        )

                # Sort by fail rate (most unstable first)
                flaky_tests.sort(key=lambda x: x["fail_rate"], reverse=True)

                return {
                    "period_days": days,
                    "flaky_threshold": threshold,
                    "flaky_tests": flaky_tests,
                    "flaky_count": len(flaky_tests),
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get flaky tests: {e}")
            return {"error": str(e), "flaky_tests": []}

    # ===== Performance Trending =====

    @app.get("/api/scout/analytics/performance")
    async def get_performance_trends(days: int = 30) -> Dict[str, Any]:
        """
        Get performance trends over time.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Performance metrics and trends
        """
        try:
            from scout.storage import DatabaseManager, WorkflowRun

            if not scout_db_path.exists():
                return {
                    "period_days": days,
                    "workflow_count": 0,
                    "durations": [],
                    "trend": "no_data",
                }

            db = DatabaseManager(str(scout_db_path))
            db.initialize()
            session = db.get_session()

            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                workflows = session.query(WorkflowRun).filter(
                    WorkflowRun.started_at >= cutoff_date
                ).all()

                if not workflows:
                    return {
                        "period_days": days,
                        "workflow_count": 0,
                        "durations": [],
                        "trend": "no_data",
                    }

                # Calculate trend
                durations = [
                    w.duration_seconds for w in workflows if w.duration_seconds]
                durations.sort()

                if len(durations) >= 2:
                    early_avg = sum(durations[: len(durations) // 2]) / (
                        len(durations) // 2
                    )
                    late_avg = sum(durations[len(durations) // 2:]) / (
                        len(durations) - len(durations) // 2
                    )
                    trend_pct = ((late_avg - early_avg) /
                                 early_avg * 100) if early_avg > 0 else 0
                    if trend_pct > 5:
                        trend = "increasing"
                    elif trend_pct < -5:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
                    trend_pct = 0

                return {
                    "period_days": days,
                    "workflow_count": len(workflows),
                    "avg_duration": sum(durations) / len(durations) if durations else 0,
                    "min_duration": min(durations) if durations else 0,
                    "max_duration": max(durations) if durations else 0,
                    "durations": durations,
                    "trend": trend,
                    "trend_percentage": round(trend_pct, 1),
                }
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {"error": str(e), "workflow_count": 0}

    logger.info("Scout endpoints registered successfully")
