"""
Scout CI Inspection endpoints for Lens.

Provides REST API for browsing, analyzing, and comparing CI workflow data.
Integrates with Scout's database layer for workflow runs, jobs, and test results.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket
from pydantic import BaseModel
import asyncio
import json
from pathlib import Path

from scout.storage import DatabaseManager
from scout.storage.schema import (
    WorkflowRun,
    WorkflowJob,
    WorkflowTestResult,
    AnalysisResult,
)


# ============================================================================
# Models for request/response
# ============================================================================


class WorkflowRunSummary(BaseModel):
    """Summary of a workflow run."""

    run_id: int
    run_number: int
    workflow_name: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: str  # "success", "failure", "cancelled", etc.
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    branch: str
    commit_sha: str
    url: Optional[str] = None


class WorkflowJobSummary(BaseModel):
    """Summary of a job within a workflow run."""

    job_id: str
    job_name: str
    status: str
    conclusion: str
    runner_os: Optional[str] = None
    python_version: Optional[str] = None
    duration_seconds: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    test_count: Optional[int] = None
    passed_count: Optional[int] = None
    failed_count: Optional[int] = None


class TestResult(BaseModel):
    """Individual test result from a job."""

    test_nodeid: str
    outcome: str  # "passed", "failed", "skipped", "error"
    duration: Optional[float] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    timestamp: Optional[str] = None


class FailurePattern(BaseModel):
    """Pattern identified in failures."""

    pattern_type: str  # "timeout", "platform-specific", "setup", "dependency"
    description: str
    count: int
    test_nodeids: List[str]
    suggested_fix: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of failure analysis."""

    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    window_days: int
    patterns: dict  # By type


class ComparisonResult(BaseModel):
    """Result of comparing two workflow runs."""

    workflow_1_id: int
    workflow_2_id: int
    passed_in_both: int
    failed_in_both: int
    failed_in_first_only: int
    failed_in_second_only: int
    flaky_tests: int
    details: dict


class FlakyTest(BaseModel):
    """Flaky test details."""

    test_nodeid: str
    pass_rate: float
    fail_rate: float
    total_runs: int
    last_failed: Optional[str] = None
    trend: str  # "stable", "improving", "degrading"


class SyncStatus(BaseModel):
    """Overall Scout database sync status."""

    last_sync: Optional[str] = None
    total_workflows: int
    total_jobs: int
    total_test_results: int
    is_syncing: bool
    sync_progress: Optional[float] = None


# ============================================================================
# Router setup
# ============================================================================

router = APIRouter(prefix="/api/scout", tags=["scout-ci"])


# ============================================================================
# Workflow Browsing Endpoints
# ============================================================================


@router.get("/workflows", response_model=dict)
async def list_workflows(
    limit: int = Query(20, le=100),
    status: Optional[str] = Query(None),
    workflow_name: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
) -> dict:
    """
    List workflow runs from the Scout database.

    Args:
        limit: Maximum number of runs to return (default: 20, max: 100)
        status: Filter by status ("completed", "in_progress", "queued") or None for all
        workflow_name: Filter by workflow name (optional)
        branch: Filter by branch name (optional)

    Returns:
        Dictionary with workflows list and metadata
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Build query
            query = session.query(WorkflowRun)

            # Apply filters
            if status:
                query = query.filter(WorkflowRun.status == status)
            if workflow_name:
                query = query.filter(
                    WorkflowRun.workflow_name.ilike(f"%{workflow_name}%"))
            if branch:
                query = query.filter(WorkflowRun.branch == branch)

            # Order by most recent first, limit results
            workflows = (
                query.order_by(WorkflowRun.started_at.desc()
                               ).limit(limit).all()
            )

            # Convert to response model
            run_summaries = [
                WorkflowRunSummary(
                    run_id=w.run_id,
                    run_number=w.run_number,
                    workflow_name=w.workflow_name,
                    status=w.status,
                    conclusion=w.conclusion,
                    started_at=w.started_at.isoformat() if w.started_at else "",
                    completed_at=w.completed_at.isoformat() if w.completed_at else None,
                    duration_seconds=w.duration_seconds,
                    branch=w.branch,
                    commit_sha=w.commit_sha or "",
                    url=w.url,
                ).dict()
                for w in workflows
            ]

            return {
                "workflows": run_summaries,
                "total": len(run_summaries),
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching workflows: {str(e)}")


@router.get("/workflows/{run_id}", response_model=dict)
async def get_workflow_details(run_id: int) -> dict:
    """
    Get detailed information about a specific workflow run.

    Args:
        run_id: GitHub Actions workflow run ID

    Returns:
        Dictionary with run details and jobs
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Get workflow run
            run = session.query(WorkflowRun).filter_by(run_id=run_id).first()

            if not run:
                raise HTTPException(
                    status_code=404, detail=f"Workflow run not found: {run_id}")

            # Get jobs for this run
            jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()

            # Convert jobs to response format
            job_summaries = []
            for job in jobs:
                # Count test results for this job
                test_results = (
                    session.query(WorkflowTestResult).filter_by(
                        job_id=job.job_id).all()
                )
                passed = sum(1 for t in test_results if t.outcome == "passed")
                failed = sum(1 for t in test_results if t.outcome == "failed")

                job_summaries.append(
                    WorkflowJobSummary(
                        job_id=job.job_id,
                        job_name=job.job_name,
                        status=job.status,
                        conclusion=job.conclusion,
                        runner_os=job.runner_os,
                        python_version=job.python_version,
                        duration_seconds=job.duration_seconds,
                        started_at=job.started_at.isoformat() if job.started_at else None,
                        completed_at=job.completed_at.isoformat() if job.completed_at else None,
                        test_count=len(test_results),
                        passed_count=passed,
                        failed_count=failed,
                    ).dict()
                )

            return {
                "run_id": run.run_id,
                "run_number": run.run_number,
                "workflow_name": run.workflow_name,
                "status": run.status,
                "conclusion": run.conclusion,
                "started_at": run.started_at.isoformat() if run.started_at else "",
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "duration_seconds": run.duration_seconds,
                "branch": run.branch,
                "commit_sha": run.commit_sha,
                "url": run.url,
                "jobs": job_summaries,
                "total_jobs": len(jobs),
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching workflow details: {str(e)}")


@router.get("/jobs/{job_id}", response_model=dict)
async def get_job_details(job_id: str, include_tests: bool = Query(True)) -> dict:
    """
    Get detailed information about a specific job.

    Args:
        job_id: Job ID
        include_tests: Whether to include test results

    Returns:
        Dictionary with job details and optionally test results
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Get job
            job = session.query(WorkflowJob).filter_by(job_id=job_id).first()

            if not job:
                raise HTTPException(
                    status_code=404, detail=f"Job not found: {job_id}")

            response = {
                "job_id": job.job_id,
                "run_id": job.run_id,
                "job_name": job.job_name,
                "status": job.status,
                "conclusion": job.conclusion,
                "runner_os": job.runner_os,
                "python_version": job.python_version,
                "duration_seconds": job.duration_seconds,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }

            # Include test results if requested
            if include_tests:
                test_results = (
                    session.query(WorkflowTestResult)
                    .filter_by(job_id=job_id)
                    .order_by(WorkflowTestResult.outcome, WorkflowTestResult.test_nodeid)
                    .all()
                )

                response["tests"] = [
                    TestResult(
                        test_nodeid=t.test_nodeid,
                        outcome=t.outcome,
                        duration=t.duration,
                        error_message=t.error_message,
                        error_traceback=t.error_traceback,
                        timestamp=t.timestamp.isoformat() if t.timestamp else None,
                    ).dict()
                    for t in test_results
                ]
                response["test_count"] = len(test_results)

                # Summary counts
                response["passed_count"] = sum(
                    1 for t in test_results if t.outcome == "passed")
                response["failed_count"] = sum(
                    1 for t in test_results if t.outcome == "failed")
                response["skipped_count"] = sum(
                    1 for t in test_results if t.outcome == "skipped")

            return response

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching job details: {str(e)}")


# ============================================================================
# Analysis Endpoints
# ============================================================================


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_failures(
    window_days: int = Query(30),
    runner_os: Optional[List[str]] = Query(None),
    workflow_name: Optional[str] = Query(None),
) -> AnalysisResult:
    """
    Analyze failure patterns in CI data.

    Args:
        window_days: Time window in days to analyze (default: 30)
        runner_os: List of OS to filter by (optional)
        workflow_name: Filter by workflow name (optional)

    Returns:
        Analysis result with patterns and statistics
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Calculate time window
            cutoff_date = datetime.utcnow() - timedelta(days=window_days)

            # Query runs in window
            query = session.query(WorkflowRun).filter(
                WorkflowRun.started_at >= cutoff_date)

            if workflow_name:
                query = query.filter(
                    WorkflowRun.workflow_name == workflow_name)

            runs = query.all()

            if not runs:
                return AnalysisResult(
                    total_runs=0,
                    successful_runs=0,
                    failed_runs=0,
                    success_rate=0.0,
                    window_days=window_days,
                    patterns={},
                )

            # Count results
            total_runs = len(runs)
            successful_runs = sum(1 for r in runs if r.conclusion == "success")
            failed_runs = sum(1 for r in runs if r.conclusion == "failure")
            success_rate = (successful_runs / total_runs *
                            100) if total_runs > 0 else 0

            # Analyze failure patterns
            patterns = {
                "timeout": [],
                "platform-specific": [],
                "setup": [],
                "dependency": [],
            }

            # Get failed tests
            failed_jobs = session.query(WorkflowJob).filter_by(
                conclusion="failure").all()

            for job in failed_jobs:
                # Filter by runner OS if specified
                if runner_os and job.runner_os not in runner_os:
                    continue

                tests = session.query(WorkflowTestResult).filter_by(
                    job_id=job.job_id).all()

                for test in tests:
                    if test.outcome == "failed" and test.error_message:
                        # Detect pattern type based on error message
                        error_lower = test.error_message.lower()

                        if "timeout" in error_lower or "timed out" in error_lower:
                            pattern_type = "timeout"
                        elif (
                            "windows" in error_lower
                            or "linux" in error_lower
                            or "macos" in error_lower
                        ):
                            pattern_type = "platform-specific"
                        elif (
                            "setup" in error_lower
                            or "import" in error_lower
                            or "config" in error_lower
                        ):
                            pattern_type = "setup"
                        elif "dependency" in error_lower or "module" in error_lower:
                            pattern_type = "dependency"
                        else:
                            continue  # Skip unknown patterns

                        # Add to patterns
                        pattern_found = False
                        for pattern in patterns[pattern_type]:
                            if pattern["test_nodeid"] == test.test_nodeid:
                                pattern["count"] += 1
                                pattern_found = True
                                break

                        if not pattern_found:
                            patterns[pattern_type].append(
                                {
                                    "test_nodeid": test.test_nodeid,
                                    "description": test.error_message.split("\n")[0],
                                    "count": 1,
                                }
                            )

            return AnalysisResult(
                total_runs=total_runs,
                successful_runs=successful_runs,
                failed_runs=failed_runs,
                success_rate=success_rate,
                window_days=window_days,
                patterns=patterns,
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing failures: {str(e)}")


# ============================================================================
# Comparison Endpoints
# ============================================================================


@router.post("/compare", response_model=ComparisonResult)
async def compare_workflow_runs(
    workflow_id_1: int = Query(...),
    workflow_id_2: int = Query(...),
) -> ComparisonResult:
    """
    Compare test results between two workflow runs.

    Args:
        workflow_id_1: First workflow run ID
        workflow_id_2: Second workflow run ID

    Returns:
        Comparison results
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Get jobs for both workflows
            jobs_1 = session.query(WorkflowJob).filter_by(
                run_id=workflow_id_1).all()
            jobs_2 = session.query(WorkflowJob).filter_by(
                run_id=workflow_id_2).all()

            # Collect all test results
            tests_1 = {}
            for job in jobs_1:
                results = session.query(WorkflowTestResult).filter_by(
                    job_id=job.job_id).all()
                for test in results:
                    tests_1[test.test_nodeid] = test.outcome

            tests_2 = {}
            for job in jobs_2:
                results = session.query(WorkflowTestResult).filter_by(
                    job_id=job.job_id).all()
                for test in results:
                    tests_2[test.test_nodeid] = test.outcome

            # Compare
            passed_in_both = sum(
                1
                for nodeid in tests_1
                if nodeid in tests_2
                and tests_1[nodeid] == "passed"
                and tests_2[nodeid] == "passed"
            )
            failed_in_both = sum(
                1
                for nodeid in tests_1
                if nodeid in tests_2
                and tests_1[nodeid] == "failed"
                and tests_2[nodeid] == "failed"
            )
            failed_in_first_only = sum(
                1
                for nodeid in tests_1
                if nodeid not in tests_2 or tests_2[nodeid] != "failed"
            )
            failed_in_second_only = sum(
                1
                for nodeid in tests_2
                if nodeid not in tests_1 or tests_1[nodeid] != "failed"
            )
            flaky = sum(
                1
                for nodeid in tests_1
                if nodeid in tests_2 and tests_1[nodeid] != tests_2[nodeid]
            )

            return ComparisonResult(
                workflow_1_id=workflow_id_1,
                workflow_2_id=workflow_id_2,
                passed_in_both=passed_in_both,
                failed_in_both=failed_in_both,
                failed_in_first_only=failed_in_first_only,
                failed_in_second_only=failed_in_second_only,
                flaky_tests=flaky,
                details={},
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error comparing workflows: {str(e)}")


# ============================================================================
# Health/Metrics Endpoints
# ============================================================================


@router.get("/health/flaky-tests", response_model=dict)
async def get_flaky_tests(
    threshold: float = Query(0.5),
    min_runs: int = Query(5),
) -> dict:
    """
    Detect flaky tests in CI data.

    Args:
        threshold: Flakiness threshold (0.0-1.0, default: 0.5 for 50% pass rate)
        min_runs: Minimum number of runs to consider (default: 5)

    Returns:
        List of flaky tests with metrics
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Get all test results
            all_tests = session.query(WorkflowTestResult).all()

            # Group by test nodeid
            test_outcomes = {}
            for test in all_tests:
                if test.test_nodeid not in test_outcomes:
                    test_outcomes[test.test_nodeid] = []
                test_outcomes[test.test_nodeid].append(test.outcome)

            # Calculate flakiness
            flaky_tests = []
            for nodeid, outcomes in test_outcomes.items():
                if len(outcomes) < min_runs:
                    continue

                passed = sum(1 for o in outcomes if o == "passed")
                failed = sum(1 for o in outcomes if o == "failed")
                total = len(outcomes)

                pass_rate = passed / total if total > 0 else 0
                fail_rate = failed / total if total > 0 else 0

                # Check if flaky (pass rate between threshold and 1.0)
                if 0 < pass_rate < (1 - threshold):
                    flaky_tests.append(
                        FlakyTest(
                            test_nodeid=nodeid,
                            pass_rate=pass_rate,
                            fail_rate=fail_rate,
                            total_runs=total,
                            last_failed=None,  # Could compute from timestamp
                            trend="stable",  # Could compute from historical data
                        ).dict()
                    )

            # Sort by pass rate (most flaky first)
            flaky_tests.sort(key=lambda t: t["pass_rate"])

            return {
                "flaky_tests": flaky_tests,
                "total_found": len(flaky_tests),
                "threshold": threshold,
                "min_runs": min_runs,
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error detecting flaky tests: {str(e)}")


@router.get("/sync-status", response_model=SyncStatus)
async def get_sync_status() -> SyncStatus:
    """
    Get current Scout database sync status.

    Returns:
        Sync status with workflow/job/test counts
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            total_workflows = session.query(WorkflowRun).count()
            total_jobs = session.query(WorkflowJob).count()
            total_tests = session.query(WorkflowTestResult).count()

            # Get most recent workflow
            last_run = session.query(WorkflowRun).order_by(
                WorkflowRun.started_at.desc()).first()

            return SyncStatus(
                last_sync=last_run.started_at.isoformat() if last_run else None,
                total_workflows=total_workflows,
                total_jobs=total_jobs,
                total_test_results=total_tests,
                is_syncing=False,
                sync_progress=None,
            )

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting sync status: {str(e)}")


# ============================================================================
# WebSocket for Real-Time Progress (for future sync operations)
# ============================================================================


@router.websocket("/ws/sync-progress/{job_id}")
async def sync_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time sync progress updates.

    Clients can connect to receive progress updates while a sync operation runs.
    """
    await websocket.accept()

    try:
        # Simulate progress updates (in real implementation, would track actual job)
        for i in range(0, 101, 10):
            await websocket.send_json(
                {
                    "job_id": job_id,
                    "stage": "fetch" if i < 30 else "parse" if i < 70 else "save",
                    "percentage": i,
                    "message": f"Processing {i}% complete",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            await asyncio.sleep(1)  # Simulate work

        # Final message
        await websocket.send_json(
            {
                "job_id": job_id,
                "stage": "complete",
                "percentage": 100,
                "message": "Sync completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        await websocket.send_json(
            {
                "job_id": job_id,
                "stage": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    finally:
        await websocket.close()
