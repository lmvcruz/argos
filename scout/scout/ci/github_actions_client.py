"""
GitHub Actions client that integrates with Scout database.

This module provides a client that fetches GitHub Actions workflow data
and persists it to the Scout database using the storage schema.
"""

import re
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from scout.providers.base import CIProvider
from scout.storage import DatabaseManager, WorkflowJob, WorkflowRun


class GitHubActionsClient:
    """
    GitHub Actions client with database persistence.

    Fetches workflow runs and jobs from GitHub Actions API using a provider,
    and stores them in the Scout database for analysis.

    Args:
        provider: GitHub Actions provider instance
        db_manager: Database manager instance

    Examples:
        >>> from scout.providers.github_actions import GitHubActionsProvider
        >>> from scout.storage import DatabaseManager
        >>>
        >>> provider = GitHubActionsProvider("owner", "repo", "token")
        >>> db = DatabaseManager(db_path="scout.db")
        >>> db.initialize()
        >>>
        >>> client = GitHubActionsClient(provider=provider, db_manager=db)
        >>> runs = client.fetch_workflow_runs("CI Tests", limit=10)
    """

    def __init__(self, provider: CIProvider, db_manager: DatabaseManager):
        """
        Initialize GitHub Actions client.

        Args:
            provider: GitHub Actions provider instance
            db_manager: Database manager instance
        """
        self.provider = provider
        self.db = db_manager

    def fetch_workflow_runs(
        self, workflow: str, limit: int = 100
    ) -> List[WorkflowRun]:
        """
        Fetch workflow runs from GitHub and store in database.

        Fetches recent workflow runs using the provider and persists them
        to the database. If a run already exists (by run_id), it will be
        updated with the latest data.

        Args:
            workflow: Name of the workflow to fetch
            limit: Maximum number of runs to fetch

        Returns:
            List of WorkflowRun database objects

        Examples:
            >>> client = GitHubActionsClient(provider, db_manager)
            >>> runs = client.fetch_workflow_runs("CI Tests", limit=50)
            >>> len(runs) <= 50
            True
        """
        # Fetch from provider
        provider_runs = self.provider.get_workflow_runs(workflow, limit)

        # Store in database
        session = self.db.get_session()
        stored_runs = []

        for provider_run in provider_runs:
            # Check if run already exists
            existing_run = (
                session.query(WorkflowRun)
                .filter_by(run_id=int(provider_run.id))
                .first()
            )

            if existing_run:
                # Update existing run
                existing_run.status = provider_run.status
                existing_run.conclusion = provider_run.conclusion
                existing_run.completed_at = provider_run.updated_at
                existing_run.duration_seconds = self._calculate_duration(
                    provider_run.created_at, provider_run.updated_at
                )
                db_run = existing_run
            else:
                # Create new run
                db_run = WorkflowRun(
                    run_id=int(provider_run.id),
                    workflow_name=provider_run.workflow_name,
                    status=provider_run.status,
                    conclusion=provider_run.conclusion,
                    branch=provider_run.branch,
                    commit_sha=provider_run.commit_sha,
                    started_at=provider_run.created_at,
                    completed_at=provider_run.updated_at,
                    duration_seconds=self._calculate_duration(
                        provider_run.created_at, provider_run.updated_at
                    ),
                    url=provider_run.url,
                )
                session.add(db_run)

            stored_runs.append(db_run)

        session.commit()

        # Refresh objects to ensure they're fully loaded before session closes
        for run in stored_runs:
            session.refresh(run)

        session.close()

        return stored_runs

    def fetch_workflow_jobs(self, run_id: int) -> List[WorkflowJob]:
        """
        Fetch jobs for a workflow run and store in database.

        Args:
            run_id: Workflow run ID

        Returns:
            List of WorkflowJob database objects

        Examples:
            >>> jobs = client.fetch_workflow_jobs(run_id=123456789)
            >>> len(jobs) >= 1
            True
        """
        # Fetch from provider
        provider_jobs = self.provider.get_jobs(str(run_id))

        # Store in database
        session = self.db.get_session()
        stored_jobs = []

        for provider_job in provider_jobs:
            # Check if job already exists
            existing_job = (
                session.query(WorkflowJob).filter_by(job_id=int(provider_job.id)).first()
            )

            # Parse job name to extract runner_os and python_version
            runner_os, python_version = self._parse_job_name(provider_job.name)

            if existing_job:
                # Update existing job
                existing_job.status = provider_job.status
                existing_job.conclusion = provider_job.conclusion
                existing_job.completed_at = provider_job.completed_at
                existing_job.duration_seconds = self._calculate_duration(
                    provider_job.started_at, provider_job.completed_at
                )
                db_job = existing_job
            else:
                # Create new job
                db_job = WorkflowJob(
                    job_id=int(provider_job.id),
                    run_id=run_id,
                    job_name=provider_job.name,
                    runner_os=runner_os,
                    python_version=python_version,
                    status=provider_job.status,
                    conclusion=provider_job.conclusion,
                    started_at=provider_job.started_at,
                    completed_at=provider_job.completed_at,
                    duration_seconds=self._calculate_duration(
                        provider_job.started_at, provider_job.completed_at
                    ),
                    logs_url=provider_job.url,
                )
                session.add(db_job)

            stored_jobs.append(db_job)

        session.commit()

        # Refresh objects to ensure they're fully loaded before session closes
        for job in stored_jobs:
            session.refresh(job)

        session.close()

        return stored_jobs

    def get_workflow_run(self, run_id: int) -> Optional[WorkflowRun]:
        """
        Get a workflow run from database.

        Args:
            run_id: Workflow run ID

        Returns:
            WorkflowRun object or None if not found

        Examples:
            >>> run = client.get_workflow_run(run_id=123456789)
            >>> run.workflow_name
            'CI Tests'
        """
        session = self.db.get_session()
        run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
        session.close()
        return run

    def get_workflow_jobs(self, run_id: int) -> List[WorkflowJob]:
        """
        Get jobs for a workflow run from database.

        Args:
            run_id: Workflow run ID

        Returns:
            List of WorkflowJob objects

        Examples:
            >>> jobs = client.get_workflow_jobs(run_id=123456789)
            >>> len(jobs) >= 1
            True
        """
        session = self.db.get_session()
        jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()
        session.close()
        return jobs

    def list_recent_runs(self, limit: int = 100) -> List[WorkflowRun]:
        """
        List recent workflow runs from database.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of WorkflowRun objects, ordered by started_at descending

        Examples:
            >>> runs = client.list_recent_runs(limit=10)
            >>> len(runs) <= 10
            True
        """
        session = self.db.get_session()
        runs = (
            session.query(WorkflowRun)
            .order_by(WorkflowRun.started_at.desc())
            .limit(limit)
            .all()
        )
        session.close()
        return runs

    def get_failed_runs(self, limit: int = 100) -> List[WorkflowRun]:
        """
        Get failed workflow runs from database.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of WorkflowRun objects with conclusion='failure'

        Examples:
            >>> failed_runs = client.get_failed_runs(limit=10)
            >>> all(run.conclusion == 'failure' for run in failed_runs)
            True
        """
        session = self.db.get_session()
        runs = (
            session.query(WorkflowRun)
            .filter_by(conclusion="failure")
            .order_by(WorkflowRun.started_at.desc())
            .limit(limit)
            .all()
        )
        session.close()
        return runs

    def _parse_job_name(self, job_name: str) -> tuple:
        """
        Parse job name to extract runner OS and Python version.

        Parses job names like "test (ubuntu-latest, 3.10)" to extract
        the platform (ubuntu-latest) and Python version (3.10).

        Args:
            job_name: Job name from GitHub Actions

        Returns:
            Tuple of (runner_os, python_version), or (None, None) if not found

        Examples:
            >>> client = GitHubActionsClient(provider, db_manager)
            >>> client._parse_job_name("test (ubuntu-latest, 3.10)")
            ('ubuntu-latest', '3.10')
            >>> client._parse_job_name("lint")
            (None, None)
        """
        # Pattern: "name (platform, python_version)" or "name (platform)"
        # Examples:
        # - "test (ubuntu-latest, 3.10)"
        # - "test (windows-latest, 3.11)"
        # - "build (ubuntu-20.04, 3.9)"
        # - "test (ubuntu-latest)"
        # - "lint"

        pattern = r"\(([^,)]+)(?:,\s*([^)]+))?\)"
        match = re.search(pattern, job_name)

        if match:
            runner_os = match.group(1).strip()
            python_version = match.group(2).strip() if match.group(2) else None
            return runner_os, python_version

        return None, None

    def _calculate_duration(
        self, start: datetime, end: Optional[datetime]
    ) -> Optional[int]:
        """
        Calculate duration in seconds between two timestamps.

        Args:
            start: Start timestamp
            end: End timestamp (None if not completed)

        Returns:
            Duration in seconds, or None if end is None

        Examples:
            >>> from datetime import datetime
            >>> client = GitHubActionsClient(provider, db_manager)
            >>> start = datetime(2026, 2, 1, 10, 0, 0)
            >>> end = datetime(2026, 2, 1, 10, 5, 0)
            >>> client._calculate_duration(start, end)
            300
        """
        if end is None:
            return None

        delta = end - start
        return int(delta.total_seconds())
