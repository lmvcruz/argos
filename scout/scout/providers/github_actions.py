"""
GitHub Actions CI provider implementation.

Provides integration with GitHub Actions API to retrieve workflow runs,
jobs, and logs.
"""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode

import requests
from requests.exceptions import (  # noqa: F401
    HTTPError,
    RequestException,
    Timeout,
)

from scout.providers.base import CIProvider, Job, LogEntry, WorkflowRun


class GitHubActionsProvider(CIProvider):
    """
    GitHub Actions CI provider implementation.

    Implements the CIProvider interface for GitHub Actions, providing
    methods to retrieve workflow runs, jobs, and logs from the GitHub API.

    Args:
        owner: GitHub repository owner (username or organization)
        repo: GitHub repository name
        token: GitHub personal access token (optional, but recommended to avoid rate limits)

    Examples:
        >>> provider = GitHubActionsProvider(
        ...     owner="user",
        ...     repo="myrepo",
        ...     token="ghp_xxxxxxxxxxxx"
        ... )
        >>> runs = provider.get_workflow_runs("CI Tests", limit=5)
        >>> len(runs) <= 5
        True
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        """
        Initialize GitHub Actions provider.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            token: GitHub personal access token (optional)
        """
        self.owner = owner
        self.repo = repo
        self.token = token

    def _get_headers(self) -> dict:
        """
        Get HTTP headers for GitHub API requests.

        Returns:
            Dictionary of headers including authentication if token provided
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO 8601 timestamp from GitHub API.

        Args:
            timestamp_str: ISO 8601 formatted timestamp string

        Returns:
            Parsed datetime object
        """
        # GitHub API returns timestamps like "2026-02-01T10:00:00Z"
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

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
            RequestException: For other network errors
        """
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/actions/runs"
        params = {"per_page": limit}
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"

        response = requests.get(full_url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        runs = []

        for run_data in data.get("workflow_runs", []):
            # Filter by workflow name if specified
            if workflow and run_data.get("name") != workflow:
                continue

            run = WorkflowRun(
                id=str(run_data["id"]),
                workflow_name=run_data["name"],
                status=run_data["status"],
                conclusion=run_data.get("conclusion"),
                branch=run_data["head_branch"],
                commit_sha=run_data["head_sha"],
                created_at=self._parse_timestamp(run_data["created_at"]),
                updated_at=self._parse_timestamp(run_data["updated_at"]),
                url=run_data["html_url"],
            )
            runs.append(run)

        return runs

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
            RequestException: For other network errors
        """
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()

        return WorkflowRun(
            id=str(data["id"]),
            workflow_name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            branch=data["head_branch"],
            commit_sha=data["head_sha"],
            created_at=self._parse_timestamp(data["created_at"]),
            updated_at=self._parse_timestamp(data["updated_at"]),
            url=data["html_url"],
        )

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
            RequestException: For other network errors
        """
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/jobs"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        data = response.json()
        jobs = []

        for job_data in data.get("jobs", []):
            job = Job(
                id=str(job_data["id"]),
                name=job_data["name"],
                status=job_data["status"],
                conclusion=job_data.get("conclusion"),
                started_at=self._parse_timestamp(job_data["started_at"]),
                completed_at=(
                    self._parse_timestamp(job_data["completed_at"])
                    if job_data.get("completed_at")
                    else None
                ),
                url=job_data["html_url"],
            )
            jobs.append(job)

        return jobs

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
            RequestException: For other network errors
        """
        url = f"{self.BASE_URL}/repos/{self.owner}/{self.repo}/actions/jobs/{job_id}/logs"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        # GitHub returns logs as plain text
        log_content = response.content.decode("utf-8")
        lines = log_content.strip().split("\n")

        log_entries = []
        for line_number, line in enumerate(lines, start=1):
            # Parse timestamp from log line if present
            # Format: "2026-02-01T10:00:00.000Z message"
            timestamp = None
            content = line

            if line and " " in line:
                timestamp_part = line.split(" ", 1)[0]
                try:
                    timestamp = self._parse_timestamp(timestamp_part)
                    content = line.split(" ", 1)[1] if len(line.split(" ", 1)) > 1 else line
                except (ValueError, IndexError):
                    # Not a valid timestamp, use whole line as content
                    timestamp = datetime.now()
                    content = line
            else:
                timestamp = datetime.now()

            entry = LogEntry(
                timestamp=timestamp,
                line_number=line_number,
                content=content,
            )
            log_entries.append(entry)

        return log_entries
