"""
Abstract base class for CI providers.

Defines the interface that all CI provider implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class WorkflowRun:
    """
    Represents a CI workflow run.

    Args:
        id: Unique identifier for the workflow run
        workflow_name: Name of the workflow
        status: Current status (queued, in_progress, completed, etc.)
        conclusion: Final conclusion if completed (success, failure, cancelled, etc.)
        branch: Git branch being tested
        commit_sha: Git commit SHA
        created_at: When the run was created
        updated_at: When the run was last updated
        url: URL to view the run in the CI provider's UI

    Examples:
        >>> run = WorkflowRun(
        ...     id="123456",
        ...     workflow_name="CI Tests",
        ...     status="completed",
        ...     conclusion="success",
        ...     branch="main",
        ...     commit_sha="abc123",
        ...     created_at=datetime(2026, 2, 1, 10, 0),
        ...     updated_at=datetime(2026, 2, 1, 10, 15),
        ...     url="https://github.com/user/repo/actions/runs/123456"
        ... )
        >>> run.id
        '123456'
    """

    id: str
    workflow_name: str
    status: str
    conclusion: Optional[str]
    branch: str
    commit_sha: str
    created_at: datetime
    updated_at: datetime
    url: str


@dataclass
class Job:
    """
    Represents a job within a workflow run.

    Args:
        id: Unique identifier for the job
        name: Name of the job
        status: Current status
        conclusion: Final conclusion if completed
        started_at: When the job started
        completed_at: When the job completed (None if still running)
        url: URL to view the job

    Examples:
        >>> job = Job(
        ...     id="789",
        ...     name="test (ubuntu-latest, 3.10)",
        ...     status="completed",
        ...     conclusion="failure",
        ...     started_at=datetime(2026, 2, 1, 10, 0),
        ...     completed_at=datetime(2026, 2, 1, 10, 5),
        ...     url="https://github.com/user/repo/runs/789"
        ... )
        >>> job.conclusion
        'failure'
    """

    id: str
    name: str
    status: str
    conclusion: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    url: str


@dataclass
class LogEntry:
    """
    Represents a single log entry from a job.

    Args:
        timestamp: When the log entry was created
        line_number: Line number in the log file
        content: The log content

    Examples:
        >>> entry = LogEntry(
        ...     timestamp=datetime(2026, 2, 1, 10, 0),
        ...     line_number=1,
        ...     content="Running tests..."
        ... )
        >>> entry.content
        'Running tests...'
    """

    timestamp: datetime
    line_number: int
    content: str


class CIProvider(ABC):
    """
    Abstract base class for CI provider implementations.

    This class defines the interface that all CI providers must implement
    to retrieve workflow runs, jobs, and logs.
    """

    @abstractmethod
    def get_workflow_runs(self, workflow: str, limit: int = 10) -> List[WorkflowRun]:
        """
        Get recent workflow runs for a given workflow.

        Args:
            workflow: Name of the workflow to retrieve runs for
            limit: Maximum number of runs to retrieve

        Returns:
            List of WorkflowRun objects, ordered by most recent first

        Raises:
            HTTPError: If API request fails
            Timeout: If request times out
        """
        pass

    @abstractmethod
    def get_workflow_run(self, run_id: str) -> WorkflowRun:
        """
        Get details for a specific workflow run.

        Args:
            run_id: Unique identifier for the workflow run

        Returns:
            WorkflowRun object with run details

        Raises:
            HTTPError: If API request fails or run not found
            Timeout: If request times out
        """
        pass

    @abstractmethod
    def get_jobs(self, run_id: str) -> List[Job]:
        """
        Get all jobs for a specific workflow run.

        Args:
            run_id: Unique identifier for the workflow run

        Returns:
            List of Job objects for the run

        Raises:
            HTTPError: If API request fails
            Timeout: If request times out
        """
        pass

    @abstractmethod
    def get_logs(self, job_id: str) -> List[LogEntry]:
        """
        Get logs for a specific job.

        Args:
            job_id: Unique identifier for the job

        Returns:
            List of LogEntry objects with log content

        Raises:
            HTTPError: If API request fails
            Timeout: If request times out
        """
        pass
