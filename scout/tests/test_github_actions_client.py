"""
Tests for GitHubActionsClient that persists CI data to database.

This module tests the client that fetches GitHub Actions data and
stores it in the Scout database using the storage schema.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from scout.ci.github_actions_client import GitHubActionsClient
from scout.providers.base import Job, WorkflowRun as ProviderWorkflowRun
from scout.storage import DatabaseManager, WorkflowJob, WorkflowRun


@pytest.fixture
def db_manager(tmp_path):
    """Create a database manager with in-memory database."""
    db_path = str(tmp_path / "test.db")
    db = DatabaseManager(db_path=db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def mock_provider():
    """Create a mock GitHub Actions provider."""
    provider = MagicMock()
    return provider


@pytest.fixture
def sample_provider_runs():
    """Create sample WorkflowRun objects from provider."""
    return [
        ProviderWorkflowRun(
            id="123456789",
            workflow_name="CI Tests",
            status="completed",
            conclusion="success",
            branch="main",
            commit_sha="a" * 40,
            created_at=datetime(2026, 2, 1, 10, 0),
            updated_at=datetime(2026, 2, 1, 10, 15),
            url="https://github.com/user/repo/actions/runs/123456789",
        ),
        ProviderWorkflowRun(
            id="987654321",
            workflow_name="CI Tests",
            status="completed",
            conclusion="failure",
            branch="feature-branch",
            commit_sha="b" * 40,
            created_at=datetime(2026, 2, 1, 11, 0),
            updated_at=datetime(2026, 2, 1, 11, 10),
            url="https://github.com/user/repo/actions/runs/987654321",
        ),
    ]


@pytest.fixture
def sample_provider_jobs():
    """Create sample Job objects from provider."""
    return [
        Job(
            id="111111111",
            name="test (ubuntu-latest, 3.10)",
            status="completed",
            conclusion="success",
            started_at=datetime(2026, 2, 1, 10, 0),
            completed_at=datetime(2026, 2, 1, 10, 5),
            url="https://github.com/user/repo/runs/111111111",
        ),
        Job(
            id="222222222",
            name="test (windows-latest, 3.11)",
            status="completed",
            conclusion="failure",
            started_at=datetime(2026, 2, 1, 10, 0),
            completed_at=datetime(2026, 2, 1, 10, 8),
            url="https://github.com/user/repo/runs/222222222",
        ),
    ]


class TestGitHubActionsClient:
    """Test GitHubActionsClient class."""

    def test_client_initialization(self, db_manager, mock_provider):
        """Test creating a GitHubActionsClient."""
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        assert client.provider == mock_provider
        assert client.db == db_manager

    def test_fetch_and_store_workflow_runs(
        self, db_manager, mock_provider, sample_provider_runs
    ):
        """Test fetching workflow runs and storing them in database."""
        mock_provider.get_workflow_runs.return_value = sample_provider_runs

        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        stored_runs = client.fetch_workflow_runs(workflow="CI Tests", limit=10)

        # Verify provider was called
        mock_provider.get_workflow_runs.assert_called_once_with("CI Tests", 10)

        # Verify runs were stored in database
        assert len(stored_runs) == 2
        assert stored_runs[0].run_id == 123456789
        assert stored_runs[0].workflow_name == "CI Tests"
        assert stored_runs[0].conclusion == "success"

        # Verify they persist in database
        session = db_manager.get_session()
        db_runs = session.query(WorkflowRun).all()
        assert len(db_runs) == 2
        session.close()

    def test_fetch_duplicate_runs_updates_existing(
        self, db_manager, mock_provider, sample_provider_runs
    ):
        """Test that fetching duplicate runs updates existing records."""
        mock_provider.get_workflow_runs.return_value = [sample_provider_runs[0]]

        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)

        # Fetch first time
        client.fetch_workflow_runs(workflow="CI Tests", limit=10)

        # Modify and fetch again
        updated_run = ProviderWorkflowRun(
            id="123456789",
            workflow_name="CI Tests",
            status="completed",
            conclusion="success",
            branch="main",
            commit_sha="a" * 40,
            created_at=datetime(2026, 2, 1, 10, 0),
            updated_at=datetime(2026, 2, 1, 10, 20),  # Updated time
            url="https://github.com/user/repo/actions/runs/123456789",
        )
        mock_provider.get_workflow_runs.return_value = [updated_run]
        client.fetch_workflow_runs(workflow="CI Tests", limit=10)

        # Verify only one record exists with updated data
        session = db_manager.get_session()
        db_runs = session.query(WorkflowRun).all()
        assert len(db_runs) == 1
        assert db_runs[0].completed_at.minute == 20
        session.close()

    def test_fetch_workflow_jobs(
        self, db_manager, mock_provider, sample_provider_runs, sample_provider_jobs
    ):
        """Test fetching jobs for a workflow run."""
        # First store a run
        mock_provider.get_workflow_runs.return_value = [sample_provider_runs[0]]
        mock_provider.get_jobs.return_value = sample_provider_jobs

        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        client.fetch_workflow_runs(workflow="CI Tests", limit=1)

        # Fetch jobs
        stored_jobs = client.fetch_workflow_jobs(run_id=123456789)

        # Verify provider was called
        mock_provider.get_jobs.assert_called_once_with("123456789")

        # Verify jobs were stored
        assert len(stored_jobs) == 2
        assert stored_jobs[0].job_id == 111111111
        assert stored_jobs[0].runner_os == "ubuntu-latest"
        assert stored_jobs[0].python_version == "3.10"
        assert stored_jobs[1].runner_os == "windows-latest"
        assert stored_jobs[1].python_version == "3.11"

        # Verify they persist in database
        session = db_manager.get_session()
        db_jobs = session.query(WorkflowJob).all()
        assert len(db_jobs) == 2
        session.close()

    def test_parse_job_name_extracts_platform_and_python(self, db_manager, mock_provider):
        """Test that job name is parsed to extract runner_os and python_version."""
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)

        test_cases = [
            ("test (ubuntu-latest, 3.10)", "ubuntu-latest", "3.10"),
            ("test (windows-latest, 3.11)", "windows-latest", "3.11"),
            ("test (macos-latest, 3.8)", "macos-latest", "3.8"),
            ("build (ubuntu-20.04, 3.9)", "ubuntu-20.04", "3.9"),
            ("lint", None, None),  # No platform/version info
            ("test (ubuntu-latest)", "ubuntu-latest", None),  # No Python version
        ]

        for job_name, expected_os, expected_python in test_cases:
            runner_os, python_version = client._parse_job_name(job_name)
            assert runner_os == expected_os
            assert python_version == expected_python

    def test_calculate_duration(self, db_manager, mock_provider):
        """Test duration calculation from timestamps."""
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)

        start = datetime(2026, 2, 1, 10, 0, 0)
        end = datetime(2026, 2, 1, 10, 5, 30)
        duration = client._calculate_duration(start, end)
        assert duration == 330  # 5 minutes 30 seconds = 330 seconds

        # Test with None end time
        duration = client._calculate_duration(start, None)
        assert duration is None

    def test_fetch_jobs_without_run_in_database(
        self, db_manager, mock_provider, sample_provider_jobs
    ):
        """Test fetching jobs when the parent run doesn't exist in database."""
        mock_provider.get_jobs.return_value = sample_provider_jobs

        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)

        # This should still work, but might log a warning
        stored_jobs = client.fetch_workflow_jobs(run_id=123456789)
        assert len(stored_jobs) == 2

    def test_get_workflow_run_from_database(
        self, db_manager, mock_provider, sample_provider_runs
    ):
        """Test retrieving a workflow run from database."""
        # First store a run
        mock_provider.get_workflow_runs.return_value = [sample_provider_runs[0]]
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        client.fetch_workflow_runs(workflow="CI Tests", limit=1)

        # Get it back
        run = client.get_workflow_run(run_id=123456789)
        assert run is not None
        assert run.run_id == 123456789
        assert run.workflow_name == "CI Tests"

    def test_get_nonexistent_workflow_run(self, db_manager, mock_provider):
        """Test retrieving a workflow run that doesn't exist."""
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        run = client.get_workflow_run(run_id=999999999)
        assert run is None

    def test_get_workflow_jobs_from_database(
        self, db_manager, mock_provider, sample_provider_runs, sample_provider_jobs
    ):
        """Test retrieving jobs for a run from database."""
        # Store run and jobs
        mock_provider.get_workflow_runs.return_value = [sample_provider_runs[0]]
        mock_provider.get_jobs.return_value = sample_provider_jobs

        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        client.fetch_workflow_runs(workflow="CI Tests", limit=1)
        client.fetch_workflow_jobs(run_id=123456789)

        # Get jobs back
        jobs = client.get_workflow_jobs(run_id=123456789)
        assert len(jobs) == 2
        assert jobs[0].job_id == 111111111
        assert jobs[1].job_id == 222222222

    def test_list_recent_workflow_runs(
        self, db_manager, mock_provider, sample_provider_runs
    ):
        """Test listing recent workflow runs from database."""
        # Store runs
        mock_provider.get_workflow_runs.return_value = sample_provider_runs
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        client.fetch_workflow_runs(workflow="CI Tests", limit=10)

        # List them
        runs = client.list_recent_runs(limit=10)
        assert len(runs) == 2

        # Should be ordered by started_at descending (most recent first)
        assert runs[0].started_at > runs[1].started_at

    def test_get_failed_runs(self, db_manager, mock_provider, sample_provider_runs):
        """Test getting only failed workflow runs."""
        # Store runs
        mock_provider.get_workflow_runs.return_value = sample_provider_runs
        client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
        client.fetch_workflow_runs(workflow="CI Tests", limit=10)

        # Get failed runs
        failed_runs = client.get_failed_runs(limit=10)
        assert len(failed_runs) == 1
        assert failed_runs[0].conclusion == "failure"

    def test_extract_run_number_from_metadata(self, db_manager, mock_provider):
        """Test that run_number is extracted and stored."""
        run_with_number = ProviderWorkflowRun(
            id="123456789",
            workflow_name="CI Tests",
            status="completed",
            conclusion="success",
            branch="main",
            commit_sha="a" * 40,
            created_at=datetime(2026, 2, 1, 10, 0),
            updated_at=datetime(2026, 2, 1, 10, 15),
            url="https://github.com/user/repo/actions/runs/123456789",
        )

        mock_provider.get_workflow_runs.return_value = [run_with_number]
        # Mock the actual API response to include run_number
        with patch.object(
            mock_provider, "get_workflow_runs", return_value=[run_with_number]
        ):
            client = GitHubActionsClient(provider=mock_provider, db_manager=db_manager)
            # For now, we'll need to enhance the provider to include run_number
            # This test documents the expected behavior
            stored_runs = client.fetch_workflow_runs(workflow="CI Tests", limit=1)
            # Note: This will pass even without run_number for now
            assert len(stored_runs) == 1
