"""
Scout CI Inspection endpoints for Lens.

Provides REST API for browsing, analyzing, and comparing CI workflow data.
Integrates with Scout's database layer for workflow runs, jobs, and test results.
"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, Depends
from pydantic import BaseModel
import asyncio
import json
from pathlib import Path
import logging

from scout.storage import DatabaseManager
from scout.storage.schema import (
    WorkflowRun,
    WorkflowJob,
    WorkflowTestResult,
    AnalysisResult,
    ExecutionLog,
)
from lens.backend.database import ProjectDatabase

logger = logging.getLogger(__name__)


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


class ExecutionWithAvailability(BaseModel):
    """Execution summary with data availability flags."""

    run_id: int
    run_number: Optional[int] = None
    workflow_name: str
    status: str  # "success", "failure", "interrupted", "in progress"
    conclusion: Optional[str] = None
    branch: str
    commit_sha: str
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    url: Optional[str] = None
    has_logs: bool  # Whether logs have been downloaded
    has_parsed_data: bool  # Whether data has been parsed
    logs_downloaded_at: Optional[str] = None
    data_parsed_at: Optional[str] = None


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
# Helper Functions
# ============================================================================


async def get_active_project_dep():
    """
    Dependency to get the active project.

    Returns:
        Active project dict

    Raises:
        HTTPException: If no active project
    """
    projects_db = ProjectDatabase()
    project = projects_db.get_active_project()

    if not project:
        raise HTTPException(
            status_code=400,
            detail="No active project. Please select a project first."
        )

    return project.to_dict()


def get_scout_db_path(project: dict) -> str:
    """
    Get the Scout database path for the active project.

    Uses the repo-specific path: ~/.scout/<owner>/<repo>/scout.db

    Args:
        project: Project dict with 'repo' field (owner/repo format)

    Returns:
        Path to Scout database

    Raises:
        HTTPException: If invalid repo format
    """
    repo = project.get("repo")
    if not repo or "/" not in repo:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project repo format: {repo}. Expected 'owner/repo'"
        )

    owner, repo_name = repo.split("/", 1)
    db_path = Path.home() / ".scout" / owner / repo_name / "scout.db"

    return str(db_path)


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


@router.get("/runs/{run_id}/jobs", response_model=dict)
async def get_run_jobs(
    run_id: int,
    project: dict = Depends(get_active_project_dep)
) -> dict:
    """
    Get all jobs for a specific workflow run.

    Args:
        run_id: Workflow run ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with list of jobs for the run
    """
    try:
        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            # Get all jobs for this run
            jobs = (
                session.query(WorkflowJob)
                .filter_by(run_id=run_id)
                .order_by(WorkflowJob.job_name)
                .all()
            )

            if not jobs:
                # Run exists but no jobs found
                run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
                if not run:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Run not found: {run_id}"
                    )
                return {
                    "run_id": run_id,
                    "jobs": [],
                    "total": 0,
                }

            job_list = []
            for job in jobs:
                job_data = {
                    "id": str(job.job_id),
                    "name": job.job_name,
                    "status": job.conclusion or job.status or "unknown",
                    "result": "passed" if job.conclusion == "success" else "failed" if job.conclusion == "failure" else "pending",
                    "duration": job.duration_seconds or 0,
                    "runner_os": job.runner_os,
                    "python_version": job.python_version,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                }
                job_list.append(job_data)

            return {
                "run_id": run_id,
                "jobs": job_list,
                "total": len(job_list),
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching jobs for run {run_id}: {str(e)}"
        )


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
# Configuration Management
# ============================================================================


@router.get("/config")
async def get_config():
    """
    Get Scout configuration.

    Returns current configuration from environment or defaults.
    """
    return {
        "settings": {
            "githubToken": os.environ.get("GITHUB_TOKEN", ""),
            "githubRepo": os.environ.get("GITHUB_REPO", ""),
            "ciDbPath": os.environ.get("SCOUT_DB_PATH", "scout.db"),
            "analysisDbPath": os.environ.get("SCOUT_ANALYSIS_DB_PATH", "scout-analysis.db"),
            "fetchTimeout": int(os.environ.get("SCOUT_FETCH_TIMEOUT", "30")),
            "enableCache": os.environ.get("SCOUT_ENABLE_CACHE", "true").lower() == "true",
        }
    }


@router.post("/config")
async def save_config(settings: dict):
    """
    Save Scout configuration.

    Note: This updates environment variables for the current session.
    For persistent configuration, set environment variables before starting the backend.
    """
    if "githubToken" in settings:
        os.environ["GITHUB_TOKEN"] = settings["githubToken"]
    if "githubRepo" in settings:
        os.environ["GITHUB_REPO"] = settings["githubRepo"]
    if "ciDbPath" in settings:
        os.environ["SCOUT_DB_PATH"] = settings["ciDbPath"]
    if "analysisDbPath" in settings:
        os.environ["SCOUT_ANALYSIS_DB_PATH"] = settings["analysisDbPath"]
    if "fetchTimeout" in settings:
        os.environ["SCOUT_FETCH_TIMEOUT"] = str(settings["fetchTimeout"])
    if "enableCache" in settings:
        os.environ["SCOUT_ENABLE_CACHE"] = "true" if settings["enableCache"] else "false"

    return {"status": "success", "message": "Configuration saved for current session"}


# ============================================================================
# CI Execution Listing (light-weight, no fetch)
# ============================================================================


class ExecutionListItem(BaseModel):
    """Light-weight execution list item."""
    run_id: int
    run_number: Optional[int] = None
    workflow_name: str
    status: str
    conclusion: Optional[str] = None
    started_at: str
    branch: str
    commit_sha: str


@router.get("/executions", response_model=dict)
async def list_executions(
    project: dict = Depends(get_active_project_dep),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = None,
    branch: Optional[str] = None,
):
    """
    List CI executions from local Scout database.

    Returns workflow runs from the local Scout database with availability flags.
    This is a light-weight operation that doesn't trigger data fetches.

    Args:
        project: Active project (injected via dependency)
        limit: Maximum number of executions to return (1-500)
        status: Filter by status (success, failure, interrupted, in progress)
        branch: Filter by branch name

    Returns:
        Dictionary with executions list and metadata
    """
    try:
        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            query = session.query(WorkflowRun).order_by(
                WorkflowRun.started_at.desc()
            )

            # Apply filters
            if status:
                query = query.filter(WorkflowRun.status == status)
            if branch:
                query = query.filter(WorkflowRun.branch == branch)

            runs = query.limit(limit).all()

            executions = [
                ExecutionWithAvailability(
                    run_id=run.run_id,
                    run_number=run.run_number,
                    workflow_name=run.workflow_name,
                    status=run.status,
                    conclusion=run.conclusion,
                    started_at=run.started_at.isoformat() if run.started_at else "",
                    completed_at=run.completed_at.isoformat() if run.completed_at else None,
                    duration_seconds=run.duration_seconds,
                    branch=run.branch or "unknown",
                    commit_sha=run.commit_sha or "unknown",
                    url=run.url,
                    has_logs=bool(run.has_logs),
                    has_parsed_data=bool(run.has_parsed_data),
                    logs_downloaded_at=run.logs_downloaded_at.isoformat() if run.logs_downloaded_at else None,
                    data_parsed_at=run.data_parsed_at.isoformat() if run.data_parsed_at else None,
                )
                for run in runs
            ]

            return {
                "executions": [exec.dict() for exec in executions],
                "total": len(executions),
                "filters": {
                    "status": status,
                    "branch": branch,
                    "limit": limit,
                },
                "project": {
                    "repo": project.get("repo"),
                    "name": project.get("name"),
                },
                "database_path": db_path,
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing executions: {str(e)}"
        )


@router.post("/refresh", response_model=dict)
async def refresh_executions(
    project: dict = Depends(get_active_project_dep),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Refresh execution list by fetching from GitHub API and saving to local DB.

    This endpoint runs 'scout list' to fetch the latest workflow runs from
    GitHub and save metadata to the local Scout database.

    Args:
        project: Active project (injected via dependency)
        limit: Maximum number of executions to fetch (1-100)

    Returns:
        Dictionary with refresh status and updated execution count
    """
    try:
        repo = project.get("repo")
        if not repo or "/" not in repo:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid project repo format: {repo}"
            )

        # Run scout list command to fetch and save metadata
        cmd = [
            "python", "-m", "scout",
            "list",
            "--repo", repo,
            "--last", str(limit),
        ]

        # Add GitHub token if available
        token = project.get("token")
        if token:
            env = os.environ.copy()
            env["GITHUB_TOKEN"] = token
        else:
            env = None

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Scout list command failed: {result.stderr}"
            )

        # Parse output to get save count
        saved_count = 0
        updated_count = 0
        for line in result.stdout.split("\n"):
            if "Saved" in line and "updated" in line:
                # Extract numbers from "✓ Saved X new run(s), updated Y existing run(s)"
                parts = line.split()
                try:
                    saved_idx = parts.index("Saved") + 1
                    saved_count = int(parts[saved_idx])
                    updated_idx = parts.index("updated") + 1
                    updated_count = int(parts[updated_idx])
                except (ValueError, IndexError):
                    pass

        return {
            "success": True,
            "saved_count": saved_count,
            "updated_count": updated_count,
            "total_fetched": limit,
            "repo": repo,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="GitHub API request timed out"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error refreshing executions: {str(e)}"
        )


@router.post("/fetch-log/{run_id}", response_model=dict)
async def fetch_log(
    run_id: int,
    project: dict = Depends(get_active_project_dep),
):
    """
    Fetch logs for a specific workflow run.

    Downloads logs from GitHub Actions and saves them to the Scout database.

    Args:
        run_id: Workflow run ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with fetch status
    """
    logger.info(f"[FETCH_LOG] Starting fetch for run_id={run_id}")

    try:
        repo = project.get("repo")
        db_path = get_scout_db_path(project)

        logger.info(f"[FETCH_LOG] Repository: {repo}, DB path: {db_path}")

        # Run scout fetch command to download logs
        cmd = [
            "python", "-m", "scout",
            "fetch",
            "--repo", repo,
            "--run-id", str(run_id),
        ]

        # Add GitHub token if available
        token = project.get("token")
        if token:
            env = os.environ.copy()
            env["GITHUB_TOKEN"] = token
            logger.info(f"[FETCH_LOG] Using GitHub token (length: {len(token)})")
        else:
            env = None
            logger.warning("[FETCH_LOG] No GitHub token available - API rate limits may apply")

        logger.info(f"[FETCH_LOG] Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
            )

            logger.info(f"[FETCH_LOG] Command completed with return code: {result.returncode}")

            if result.stdout:
                logger.debug(f"[FETCH_LOG] STDOUT: {result.stdout[:500]}")
            if result.stderr:
                logger.debug(f"[FETCH_LOG] STDERR: {result.stderr[:500]}")

            if result.returncode != 0:
                error_msg = f"Scout fetch command failed: {result.stderr}"
                logger.error(f"[FETCH_LOG] {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=error_msg
                )

        except subprocess.TimeoutExpired as e:
            error_msg = f"Scout fetch command timed out after 120 seconds"
            logger.error(f"[FETCH_LOG] {error_msg}")
            raise HTTPException(
                status_code=504,
                detail=error_msg
            )

        # Update has_logs flag in database
        logger.info(f"[FETCH_LOG] Updating database flags for run_id={run_id}")

        try:
            db = DatabaseManager(db_path)
            db.initialize()
            session = db.get_session()

            try:
                run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
                if run:
                    run.has_logs = 1
                    run.logs_downloaded_at = datetime.utcnow()
                    session.commit()
                    logger.info(f"[FETCH_LOG] Updated has_logs flag for run_id={run_id}")
                else:
                    logger.warning(f"[FETCH_LOG] Run {run_id} not found in database")

            finally:
                session.close()

        except Exception as db_error:
            logger.error(f"[FETCH_LOG] Database error: {str(db_error)}", exc_info=True)
            # Don't fail the request if only DB update fails
            pass
        logger.info(f"[FETCH_LOG] Successfully completed fetch for run_id={run_id}")

        return {
            "success": True,
            "run_id": run_id,
            "message": "Logs fetched successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException as http_ex:
        logger.error(f"[FETCH_LOG] HTTP exception: {http_ex.detail}")
        raise
    except subprocess.TimeoutExpired:
        error_msg = "Log fetch request timed out after 120 seconds"
        logger.error(f"[FETCH_LOG] {error_msg}")
        raise HTTPException(
            status_code=504,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error fetching log: {str(e)}"
        logger.error(f"[FETCH_LOG] {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.post("/parse-data/{run_id}", response_model=dict)
async def parse_data(
    run_id: int,
    project: dict = Depends(get_active_project_dep),
):
    """
    Parse logs for a specific workflow run.

    Uses AnvilBridge to parse validator output from logs and save to database.

    Args:
        run_id: Workflow run ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with parse status
    """
    logger.info(f"[PARSE_DATA] Starting parse for run_id={run_id}")

    try:
        repo = project.get("repo")
        db_path = get_scout_db_path(project)

        logger.info(f"[PARSE_DATA] Repository: {repo}, DB path: {db_path}")

        # Run scout parse command
        cmd = [
            "python", "-m", "scout",
            "parse",
            "--repo", repo,
            "--run-id", str(run_id),
        ]

        logger.info(f"[PARSE_DATA] Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        logger.info(f"[PARSE_DATA] Command completed with return code: {result.returncode}")
        if result.stdout:
            logger.debug(f"[PARSE_DATA] STDOUT (first 500 chars): {result.stdout[:500]}")
        if result.stderr:
            logger.debug(f"[PARSE_DATA] STDERR: {result.stderr[:500]}")

        if result.returncode != 0:
            logger.error(f"[PARSE_DATA] Parse command failed with return code {result.returncode}")
            raise HTTPException(
                status_code=500,
                detail=f"Scout parse command failed: {result.stderr}"
            )

        # Parse the JSON output from Scout
        import json
        try:
            parsed_data = json.loads(result.stdout)
            logger.info(f"[PARSE_DATA] Successfully parsed JSON output. Status: {parsed_data.get('status')}")

            # Check if parsing was successful
            if parsed_data.get("status") == "not_implemented":
                logger.warning(f"[PARSE_DATA] Parse functionality returned not_implemented status")
                return {
                    "success": False,
                    "run_id": run_id,
                    "message": parsed_data.get("message", "Parse functionality not yet implemented"),
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except json.JSONDecodeError as e:
            logger.error(f"[PARSE_DATA] Failed to parse JSON output: {e}")
            logger.error(f"[PARSE_DATA] Raw output: {result.stdout}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse Scout output: {str(e)}"
            )

        # Update has_parsed_data flag in database
        logger.info(f"[PARSE_DATA] Updating database flags for run_id={run_id}")
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if run:
                run.has_parsed_data = 1
                run.data_parsed_at = datetime.utcnow()
                session.commit()
                logger.info(f"[PARSE_DATA] Updated has_parsed_data flag for run_id={run_id}")
            else:
                logger.warning(f"[PARSE_DATA] Run {run_id} not found in database")

        finally:
            session.close()

        logger.info(f"[PARSE_DATA] Successfully completed parse for run_id={run_id}")

        # Return the actual parsed data from Scout
        return {
            "success": True,
            "run_id": run_id,
            "message": "Data parsed successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "data": parsed_data,  # Include the actual parsed data
        }

    except HTTPException as http_ex:
        logger.error(f"[PARSE_DATA] HTTP exception: {http_ex.detail}")
        raise
    except subprocess.TimeoutExpired:
        error_msg = "Parse request timed out after 120 seconds"
        logger.error(f"[PARSE_DATA] {error_msg}")
        raise HTTPException(
            status_code=504,
            detail=error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error parsing data: {str(e)}"
        logger.error(f"[PARSE_DATA] {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )


@router.post("/fetch-job-log/{job_id}", response_model=dict)
async def fetch_job_log(
    job_id: int,
    project: dict = Depends(get_active_project_dep),
):
    """
    Fetch logs for a specific job within a workflow run.

    Downloads logs from GitHub Actions for a single job.

    Args:
        job_id: Job ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with fetch status and log content
    """
    logger.info(f"[FETCH_JOB_LOG] Starting fetch for job_id={job_id}")

    try:
        repo = project.get("repo")
        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            # Get job information
            job = session.query(WorkflowJob).filter_by(job_id=job_id).first()

            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job not found: {job_id}"
                )

            run_id = job.run_id
            logger.info(f"[FETCH_JOB_LOG] Job {job_id} belongs to run {run_id}")

            # Run scout fetch command for the entire run
            # (Scout fetches all jobs at once, so we fetch the run and extract the specific job)
            cmd = [
                "python", "-m", "scout",
                "fetch",
                "--repo", repo,
                "--run-id", str(run_id),
            ]

            token = project.get("token")
            if token:
                env = os.environ.copy()
                env["GITHUB_TOKEN"] = token
            else:
                env = None

            logger.info(f"[FETCH_JOB_LOG] Running fetch command for run {run_id}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Scout fetch failed: {result.stderr}"
                )

            # Now retrieve the specific job's log from database
            session.expire_all()  # Refresh session to get updated data
            job = session.query(WorkflowJob).filter_by(job_id=job_id).first()

            # Get execution log for this job
            exec_log = session.query(ExecutionLog).filter_by(
                run_id=run_id,
                job_id=job_id
            ).first()

            log_content = None
            if exec_log and exec_log.raw_content:
                log_content = exec_log.raw_content
                logger.info(f"[FETCH_JOB_LOG] Retrieved log content ({len(log_content)} chars) for job {job_id}")
            else:
                logger.warning(f"[FETCH_JOB_LOG] No log content found for job {job_id}")

            return {
                "success": True,
                "job_id": job_id,
                "run_id": run_id,
                "job_name": job.job_name if job else "Unknown",
                "has_log": log_content is not None,
                "log_content": log_content,
                "message": "Job log fetched successfully" if log_content else "Job log not available",
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail="Fetch request timed out after 120 seconds"
        )
    except Exception as e:
        logger.error(f"[FETCH_JOB_LOG] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch job log: {str(e)}"
        )


@router.post("/parse-job-data/{job_id}", response_model=dict)
async def parse_job_data(
    job_id: int,
    project: dict = Depends(get_active_project_dep),
):
    """
    Parse logs for a specific job.

    Analyzes logs for a single job and extracts test results, coverage, etc.

    Args:
        job_id: Job ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with parsed data for the job
    """
    logger.info(f"[PARSE_JOB_DATA] Starting parse for job_id={job_id}")

    try:
        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            # Get job and its log
            job = session.query(WorkflowJob).filter_by(job_id=job_id).first()

            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job not found: {job_id}"
                )

            exec_log = session.query(ExecutionLog).filter_by(
                job_id=job_id
            ).first()

            if not exec_log or not exec_log.raw_content:
                raise HTTPException(
                    status_code=404,
                    detail=f"No log content found for job {job_id}. Please fetch logs first."
                )

            logger.info(f"[PARSE_JOB_DATA] Parsing log for job {job.job_name}")

            # Parse the log content using Scout's parsers
            from scout.parsers.ci_log_parser import CILogParser

            parser = CILogParser()

            # Parse pytest output
            test_results = []
            test_summary = None
            failed_tests = []
            try:
                # parse_pytest_log returns a list of test results
                test_results = parser.parse_pytest_log(exec_log.raw_content)

                if test_results:
                    # Create summary from test results
                    passed_count = sum(1 for t in test_results if t.get("outcome") == "passed")
                    failed_count = sum(1 for t in test_results if t.get("outcome") == "failed")
                    skipped_count = sum(1 for t in test_results if t.get("outcome") == "skipped")
                    error_count = sum(1 for t in test_results if t.get("outcome") == "error")

                    test_summary = {
                        "passed": passed_count,
                        "failed": failed_count,
                        "skipped": skipped_count,
                        "errors": error_count,
                        "total": len(test_results)
                    }

                    # Extract failed tests with details
                    failed_tests = [
                        {
                            "test_name": test.get("test_nodeid", "Unknown"),
                            "error_message": test.get("error_message", ""),
                            "error_traceback": test.get("error_traceback", "")
                        }
                        for test in test_results
                        if test.get("outcome") in ["failed", "error"]
                    ][:10]  # Limit to first 10 failures

            except Exception as e:
                logger.warning(f"[PARSE_JOB_DATA] Failed to parse pytest output: {e}")

            # Parse coverage
            coverage = None
            try:
                coverage = parser.parse_coverage_log(exec_log.raw_content)
            except Exception as e:
                logger.warning(f"[PARSE_JOB_DATA] Failed to parse coverage: {e}")

            # Parse flake8
            flake8_issues = []
            try:
                flake8_issues = parser.parse_flake8_log(exec_log.raw_content)
            except Exception as e:
                logger.warning(f"[PARSE_JOB_DATA] Failed to parse flake8: {e}")

            # Build response
            parsed_data = {
                "status": "success",
                "job_id": job_id,
                "run_id": job.run_id,
                "job_name": job.job_name,
                "platform": job.runner_os,
                "python_version": job.python_version,
                "test_summary": test_summary,  # Already a dict or None
                "failed_tests": failed_tests,
                "coverage": coverage,
                "flake8_issues": flake8_issues[:20] if flake8_issues else [],  # Limit to 20
            }

            logger.info(f"[PARSE_JOB_DATA] Successfully parsed job {job_id}")

            return {
                "success": True,
                "job_id": job_id,
                "message": "Job data parsed successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "data": parsed_data,
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PARSE_JOB_DATA] Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse job data: {str(e)}"
        )


# ============================================================================
# Database Status & Diagnostics
# ============================================================================


@router.get("/database/status")
async def get_database_status():
    """
    Get Scout database status and statistics.

    Useful for debugging why no executions are found.
    """
    try:
        db_path = os.environ.get("SCOUT_DB_PATH", "scout.db")
        db_exists = Path(db_path).exists()

        if not db_exists:
            return {
                "exists": False,
                "path": str(db_path),
                "message": f"Database not found at {db_path}. Run 'scout sync' or 'scout fetch' to populate it."
            }

        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            total_workflows = session.query(WorkflowRun).count()
            total_jobs = session.query(WorkflowJob).count()
            total_tests = session.query(WorkflowTestResult).count()

            # Get recent workflow for timestamp check
            recent = session.query(WorkflowRun).order_by(
                WorkflowRun.started_at.desc()
            ).first()

            return {
                "exists": True,
                "path": str(db_path),
                "total_workflows": total_workflows,
                "total_jobs": total_jobs,
                "total_tests": total_tests,
                "last_workflow": recent.started_at.isoformat() if recent else None,
                "message": f"Database has {total_workflows} workflows, {total_jobs} jobs, {total_tests} tests"
            }
        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error checking database status: {str(e)}"
        )


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


# ============================================================================
# New Database Query Endpoints (list, db-list, show-log, show-data)
# ============================================================================


@router.get("/list", response_model=dict)
async def list_executions(
    workflow: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    last: int = Query(10, ge=1, le=100),
) -> dict:
    """
    List local executions from Scout database.

    This is similar to 'scout db-list' command - queries the local database.

    Args:
        workflow: Filter by workflow name (optional)
        branch: Filter by branch name (optional)
        status: Filter by status (optional)
        last: Limit to last N items (default: 10, max: 100)

    Returns:
        Dictionary with list of executions and metadata
    """
    try:
        db = DatabaseManager("scout.db")
        db.initialize()
        session = db.get_session()

        try:
            # Build query
            query = session.query(WorkflowRun)

            # Apply filters
            if workflow:
                query = query.filter(
                    WorkflowRun.workflow_name.ilike(f"%{workflow}%"))
            if branch:
                query = query.filter(WorkflowRun.branch == branch)
            if status:
                query = query.filter(WorkflowRun.status == status)

            # Get last N runs
            runs = (
                query.order_by(WorkflowRun.started_at.desc()).limit(last).all()
            )

            # Convert to response format
            executions = [
                {
                    "run_id": run.run_id,
                    "workflow_name": run.workflow_name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "branch": run.branch,
                    "started_at": run.started_at.isoformat()
                    if run.started_at else None,
                    "completed_at": run.completed_at.isoformat()
                    if run.completed_at else None,
                    "duration_seconds": run.duration_seconds,
                }
                for run in runs
            ]

            return {
                "executions": executions,
                "count": len(executions),
                "filters": {
                    "workflow": workflow,
                    "branch": branch,
                    "status": status,
                    "last": last,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing executions: {str(e)}"
        )


@router.get("/show-log/{run_id}", response_model=dict)
async def show_logs(
    run_id: int,
    project: dict = Depends(get_active_project_dep)
) -> dict:
    """
    Show logs for a specific workflow run from the database.

    This retrieves stored logs from the ExecutionLog table and returns
    the actual raw log content from GitHub Actions.

    Args:
        run_id: GitHub Actions workflow run ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with workflow run info and raw logs from jobs
    """
    try:
        from scout.storage.schema import ExecutionLog

        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            # Get workflow run
            run = session.query(WorkflowRun).filter_by(run_id=run_id).first()

            if not run:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow run not found: {run_id}",
                )

            # Get jobs for this run
            jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()

            # Build response with job information and raw logs
            job_logs = []
            for job in jobs:
                # Get raw logs from ExecutionLog table
                execution_log = (
                    session.query(ExecutionLog)
                    .filter_by(job_id=job.job_id)
                    .first()
                )

                # Get test results for this job to show as summary
                test_results = (
                    session.query(WorkflowTestResult).filter_by(
                        job_id=job.job_id
                    ).all()
                )

                job_log_data = {
                    "job_id": job.job_id,
                    "job_name": job.job_name,
                    "status": job.status,
                    "conclusion": job.conclusion,
                    "started_at": job.started_at.isoformat()
                    if job.started_at else None,
                    "completed_at": job.completed_at.isoformat()
                    if job.completed_at else None,
                    "has_raw_log": execution_log is not None,
                    "raw_log": execution_log.raw_content if execution_log else None,
                    "test_summary": {
                        "total": len(test_results),
                        "passed": sum(
                            1 for t in test_results if t.outcome == "passed"
                        ),
                        "failed": sum(
                            1 for t in test_results if t.outcome == "failed"
                        ),
                        "skipped": sum(
                            1 for t in test_results if t.outcome == "skipped"
                        ),
                    },
                }
                job_logs.append(job_log_data)

            return {
                "run_id": run.run_id,
                "workflow_name": run.workflow_name,
                "branch": run.branch,
                "status": run.status,
                "conclusion": run.conclusion,
                "started_at": run.started_at.isoformat()
                if run.started_at else None,
                "completed_at": run.completed_at.isoformat()
                if run.completed_at else None,
                "jobs": job_logs,
                "total_jobs": len(job_logs),
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving logs: {str(e)}"
        )


@router.get("/show-data/{run_id}", response_model=dict)
async def show_analysis_data(
    run_id: int,
    project: dict = Depends(get_active_project_dep)
) -> dict:
    """
    Show parsed analysis data for a specific workflow run.

    This is similar to 'scout show-data' command - displays analysis results.

    Args:
        run_id: GitHub Actions workflow run ID
        project: Active project (injected via dependency)

    Returns:
        Dictionary with analysis results and statistics
    """
    try:
        db_path = get_scout_db_path(project)
        db = DatabaseManager(db_path)
        db.initialize()
        session = db.get_session()

        try:
            # Get workflow run
            run = session.query(WorkflowRun).filter_by(run_id=run_id).first()

            if not run:
                raise HTTPException(
                    status_code=404,
                    detail=f"Workflow run not found: {run_id}",
                )

            # Get all test results for this run
            jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()
            all_tests = []
            for job in jobs:
                tests = (
                    session.query(WorkflowTestResult).filter_by(
                        job_id=job.job_id
                    ).all()
                )
                all_tests.extend(tests)

            # Calculate statistics
            total_tests = len(all_tests)
            passed_tests = sum(1 for t in all_tests if t.outcome == "passed")
            failed_tests = sum(1 for t in all_tests if t.outcome == "failed")
            skipped_tests = sum(1 for t in all_tests if t.outcome == "skipped")

            # Identify failure patterns
            failures = [t for t in all_tests if t.outcome == "failed"]
            failure_patterns = {}
            for failure in failures:
                # Simple pattern detection based on error message
                if "timeout" in (failure.error_message or "").lower():
                    key = "timeout"
                elif "platform" in (failure.error_message or "").lower():
                    key = "platform-specific"
                elif "setup" in (failure.error_message or "").lower():
                    key = "setup-failure"
                else:
                    key = "other"

                if key not in failure_patterns:
                    failure_patterns[key] = []
                failure_patterns[key].append(failure.test_nodeid)

            # Build analysis data
            analysis_data = {
                "run_id": run.run_id,
                "workflow_name": run.workflow_name,
                "branch": run.branch,
                "status": run.status,
                "started_at": run.started_at.isoformat()
                if run.started_at else None,
                "statistics": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests,
                    "pass_rate": (
                        (passed_tests / total_tests * 100)
                        if total_tests > 0 else 0
                    ),
                },
                "failure_patterns": failure_patterns,
                "jobs_count": len(jobs),
            }

            return analysis_data

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving analysis data: {str(e)}"
        )
