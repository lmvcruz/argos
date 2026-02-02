"""
Database schema for Scout CI data storage.

This module defines SQLAlchemy ORM models for storing GitHub Actions
workflow runs, jobs, test results, and failure patterns.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class WorkflowRun(Base):
    """
    GitHub Actions workflow run.

    Stores metadata about a complete workflow run including its status,
    conclusion, and timing information.

    Args:
        run_id: GitHub Actions run ID (unique identifier from GitHub API)
        workflow_name: Name of the workflow (e.g., "CI Tests")
        run_number: Sequential run number within the workflow
        event: Trigger event (push, pull_request, schedule, etc.)
        status: Current status (queued, in_progress, completed)
        conclusion: Final result if completed (success, failure, cancelled, etc.)
        branch: Git branch being tested
        commit_sha: Git commit SHA (40 character hex string)
        started_at: Timestamp when the run started
        completed_at: Timestamp when the run completed (None if still running)
        duration_seconds: Total run duration in seconds
        url: GitHub URL to view the run
        extra_metadata: Additional JSON metadata from GitHub API

    Examples:
        >>> run = WorkflowRun(
        ...     run_id=123456789,
        ...     workflow_name="CI Tests",
        ...     run_number=42,
        ...     event="push",
        ...     status="completed",
        ...     conclusion="success",
        ...     branch="main",
        ...     commit_sha="a" * 40,
        ...     started_at=datetime(2026, 2, 1, 10, 0),
        ...     completed_at=datetime(2026, 2, 1, 10, 15),
        ...     duration_seconds=900,
        ...     url="https://github.com/user/repo/actions/runs/123456789"
        ... )
    """

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(BigInteger, unique=True, nullable=False, index=True)
    workflow_name = Column(String(200), nullable=False)
    run_number = Column(Integer, nullable=True)
    event = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)
    conclusion = Column(String(20), nullable=True)
    branch = Column(String(200), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    url = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    jobs = relationship("WorkflowJob", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_workflow_run_number", "workflow_name", "run_number"),
        Index("idx_conclusion", "conclusion"),
        Index("idx_branch", "branch"),
    )

    def __repr__(self) -> str:
        """Return string representation of WorkflowRun."""
        return (
            f"<WorkflowRun(run_id={self.run_id}, "
            f"workflow='{self.workflow_name}', "
            f"conclusion='{self.conclusion}')>"
        )


class WorkflowJob(Base):
    """
    Individual job within a GitHub Actions workflow run.

    Represents a single job (e.g., test matrix entry) within a workflow run,
    including platform and Python version information.

    Args:
        job_id: GitHub Actions job ID (unique identifier from GitHub API)
        run_id: Foreign key to parent WorkflowRun
        job_name: Name of the job (e.g., "test (ubuntu-latest, 3.10)")
        runner_os: Operating system (ubuntu-latest, windows-latest, macos-latest)
        python_version: Python version being tested (e.g., "3.8", "3.10")
        status: Current status
        conclusion: Final result if completed
        started_at: Timestamp when the job started
        completed_at: Timestamp when the job completed
        duration_seconds: Total job duration in seconds
        logs_url: URL to download job logs
        extra_metadata: Additional JSON metadata

    Examples:
        >>> job = WorkflowJob(
        ...     job_id=987654321,
        ...     run_id=123456789,
        ...     job_name="test (ubuntu-latest, 3.10)",
        ...     runner_os="ubuntu-latest",
        ...     python_version="3.10",
        ...     status="completed",
        ...     conclusion="failure",
        ...     started_at=datetime(2026, 2, 1, 10, 0),
        ...     completed_at=datetime(2026, 2, 1, 10, 5),
        ...     duration_seconds=300,
        ...     logs_url="https://api.github.com/repos/.../actions/jobs/987654321/logs"
        ... )
    """

    __tablename__ = "workflow_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, unique=True, nullable=False, index=True)
    run_id = Column(BigInteger, ForeignKey("workflow_runs.run_id"), nullable=False)
    job_name = Column(String(200), nullable=False)
    runner_os = Column(String(50), nullable=True)
    python_version = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False)
    conclusion = Column(String(20), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    logs_url = Column(String(500), nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    # Relationships
    run = relationship("WorkflowRun", back_populates="jobs")
    test_results = relationship(
        "WorkflowTestResult", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_runner_os", "runner_os"),
        Index("idx_job_conclusion", "conclusion"),
        Index("idx_python_version", "python_version"),
    )

    def __repr__(self) -> str:
        """Return string representation of WorkflowJob."""
        return (
            f"<WorkflowJob(job_id={self.job_id}, "
            f"name='{self.job_name}', "
            f"conclusion='{self.conclusion}')>"
        )


class WorkflowTestResult(Base):
    """
    Test result extracted from a GitHub Actions job.

    Stores individual test execution results parsed from CI logs,
    enabling comparison between local and CI test execution.

    Args:
        job_id: Foreign key to parent WorkflowJob
        test_nodeid: Pytest node ID (e.g., "tests/test_file.py::test_function")
        outcome: Test result (passed, failed, skipped, error)
        duration: Test execution time in seconds
        error_message: Error message if test failed
        error_traceback: Full error traceback if test failed
        runner_os: Operating system where test ran
        python_version: Python version used
        timestamp: When the test was executed

    Examples:
        >>> result = WorkflowTestResult(
        ...     job_id=987654321,
        ...     test_nodeid="tests/test_parser.py::test_extract_version",
        ...     outcome="failed",
        ...     duration=0.05,
        ...     error_message="AssertionError: expected '1.0.0', got '1.0.1'",
        ...     runner_os="ubuntu-latest",
        ...     python_version="3.10",
        ...     timestamp=datetime(2026, 2, 1, 10, 3)
        ... )
    """

    __tablename__ = "workflow_test_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("workflow_jobs.job_id"), nullable=False)
    test_nodeid = Column(String(500), nullable=False, index=True)
    outcome = Column(String(20), nullable=False)
    duration = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    runner_os = Column(String(50), nullable=True)
    python_version = Column(String(20), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("WorkflowJob", back_populates="test_results")

    __table_args__ = (
        Index("idx_test_outcome", "test_nodeid", "outcome"),
        Index("idx_runner_os_test", "runner_os", "test_nodeid"),
        Index("idx_outcome", "outcome"),
    )

    def __repr__(self) -> str:
        """Return string representation of WorkflowTestResult."""
        return (
            f"<WorkflowTestResult(nodeid='{self.test_nodeid}', "
            f"outcome='{self.outcome}', "
            f"os='{self.runner_os}')>"
        )


class CIFailurePattern(Base):
    """
    Identified failure pattern in CI.

    Tracks recurring failure patterns across CI runs to help identify
    systematic issues like platform-specific failures, flaky tests,
    or setup problems.

    Args:
        pattern_type: Type of pattern (platform-specific, flaky, timeout, setup)
        test_nodeid: Pytest node ID (optional, None for non-test failures)
        runner_os: Operating system (optional, None if not platform-specific)
        failure_count: Number of times this pattern has been observed
        first_seen: Timestamp of first occurrence
        last_seen: Timestamp of most recent occurrence
        description: Human-readable description of the pattern
        suggested_fix: Optional suggestion for fixing the issue
        extra_metadata: Additional JSON metadata (error messages, stack traces, etc.)

    Examples:
        >>> pattern = CIFailurePattern(
        ...     pattern_type="platform-specific",
        ...     test_nodeid="tests/test_symlinks.py::test_create_symlink",
        ...     runner_os="windows-latest",
        ...     failure_count=15,
        ...     first_seen=datetime(2026, 1, 1),
        ...     last_seen=datetime(2026, 2, 1),
        ...     description="Symlink test fails on Windows due to permission issues",
        ...     suggested_fix="Skip test on Windows or use pytest.mark.skipif"
        ... )
    """

    __tablename__ = "ci_failure_patterns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(50), nullable=False, index=True)
    test_nodeid = Column(String(500), nullable=True, index=True)
    runner_os = Column(String(50), nullable=True, index=True)
    failure_count = Column(Integer, default=0, nullable=False)
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    __table_args__ = (Index("idx_pattern_type_os", "pattern_type", "runner_os"),)

    def __repr__(self) -> str:
        """Return string representation of CIFailurePattern."""
        return (
            f"<CIFailurePattern(type='{self.pattern_type}', "
            f"count={self.failure_count}, "
            f"os='{self.runner_os}')>"
        )
