"""
Tests for CI provider abstraction.

Tests the abstract CI provider interface and GitHub Actions implementation.
Following TDD approach: write tests first, then implement to make them pass.
"""

from datetime import datetime
from typing import List
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import HTTPError, RequestException, Timeout

from scout.providers import CIProvider, GitHubActionsProvider, Job, LogEntry, WorkflowRun


class TestCIProviderInterface:
    """Test the abstract CI provider interface definition."""

    def test_provider_interface_is_abstract(self):
        """Test that CIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            CIProvider()

    def test_provider_interface_requires_get_workflow_runs(self):
        """Test that subclasses must implement get_workflow_runs."""

        class IncompleteProvider(CIProvider):
            def get_workflow_run(self, run_id: str) -> WorkflowRun:
                pass

            def get_jobs(self, run_id: str) -> List[Job]:
                pass

            def get_logs(self, job_id: str) -> List[LogEntry]:
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_provider_interface_requires_get_workflow_run(self):
        """Test that subclasses must implement get_workflow_run."""

        class IncompleteProvider(CIProvider):
            def get_workflow_runs(self, workflow: str, limit: int = 10) -> List[WorkflowRun]:
                pass

            def get_jobs(self, run_id: str) -> List[Job]:
                pass

            def get_logs(self, job_id: str) -> List[LogEntry]:
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_provider_interface_requires_get_jobs(self):
        """Test that subclasses must implement get_jobs."""

        class IncompleteProvider(CIProvider):
            def get_workflow_runs(self, workflow: str, limit: int = 10) -> List[WorkflowRun]:
                pass

            def get_workflow_run(self, run_id: str) -> WorkflowRun:
                pass

            def get_logs(self, job_id: str) -> List[LogEntry]:
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_provider_interface_requires_get_logs(self):
        """Test that subclasses must implement get_logs."""

        class IncompleteProvider(CIProvider):
            def get_workflow_runs(self, workflow: str, limit: int = 10) -> List[WorkflowRun]:
                pass

            def get_workflow_run(self, run_id: str) -> WorkflowRun:
                pass

            def get_jobs(self, run_id: str) -> List[Job]:
                pass

        with pytest.raises(TypeError):
            IncompleteProvider()


class TestWorkflowRunModel:
    """Test the WorkflowRun data model."""

    def test_workflow_run_creation_with_all_fields(self):
        """Test creating a WorkflowRun with all fields."""
        run = WorkflowRun(
            id="123456",
            workflow_name="CI Tests",
            status="completed",
            conclusion="success",
            branch="main",
            commit_sha="abc123def",
            created_at=datetime(2026, 2, 1, 10, 0, 0),
            updated_at=datetime(2026, 2, 1, 10, 15, 0),
            url="https://github.com/user/repo/actions/runs/123456",
        )

        assert run.id == "123456"
        assert run.workflow_name == "CI Tests"
        assert run.status == "completed"
        assert run.conclusion == "success"
        assert run.branch == "main"
        assert run.commit_sha == "abc123def"
        assert run.url == "https://github.com/user/repo/actions/runs/123456"

    def test_workflow_run_creation_with_optional_fields(self):
        """Test creating a WorkflowRun with optional conclusion field."""
        run = WorkflowRun(
            id="123456",
            workflow_name="CI Tests",
            status="in_progress",
            conclusion=None,
            branch="main",
            commit_sha="abc123def",
            created_at=datetime(2026, 2, 1, 10, 0, 0),
            updated_at=datetime(2026, 2, 1, 10, 15, 0),
            url="https://github.com/user/repo/actions/runs/123456",
        )

        assert run.conclusion is None


class TestJobModel:
    """Test the Job data model."""

    def test_job_creation_with_all_fields(self):
        """Test creating a Job with all fields."""
        job = Job(
            id="789",
            name="test (ubuntu-latest, 3.10)",
            status="completed",
            conclusion="failure",
            started_at=datetime(2026, 2, 1, 10, 0, 0),
            completed_at=datetime(2026, 2, 1, 10, 5, 0),
            url="https://github.com/user/repo/actions/runs/123456/job/789",
        )

        assert job.id == "789"
        assert job.name == "test (ubuntu-latest, 3.10)"
        assert job.status == "completed"
        assert job.conclusion == "failure"

    def test_job_creation_with_optional_fields(self):
        """Test creating a Job with optional completed_at field."""
        job = Job(
            id="789",
            name="test",
            status="in_progress",
            conclusion=None,
            started_at=datetime(2026, 2, 1, 10, 0, 0),
            completed_at=None,
            url="https://github.com/user/repo/actions/runs/123456/job/789",
        )

        assert job.completed_at is None


class TestLogEntryModel:
    """Test the LogEntry data model."""

    def test_log_entry_creation(self):
        """Test creating a LogEntry."""
        entry = LogEntry(
            timestamp=datetime(2026, 2, 1, 10, 0, 0),
            line_number=42,
            content="Running tests...",
        )

        assert entry.timestamp == datetime(2026, 2, 1, 10, 0, 0)
        assert entry.line_number == 42
        assert entry.content == "Running tests..."


class TestGitHubActionsProvider:
    """Test the GitHub Actions provider implementation."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock HTTP response."""
        mock = Mock()
        mock.status_code = 200
        mock.raise_for_status = Mock()
        return mock

    @pytest.fixture
    def provider(self):
        """Create a GitHubActionsProvider instance."""
        return GitHubActionsProvider(owner="testuser", repo="testrepo", token="test_token_123")

    def test_github_actions_provider_initialization(self):
        """Test GitHub Actions provider initialization."""
        provider = GitHubActionsProvider(owner="user", repo="repo", token="token123")

        assert provider.owner == "user"
        assert provider.repo == "repo"
        assert provider.token == "token123"

    def test_github_actions_provider_initialization_without_token(self):
        """Test GitHub Actions provider initialization without token."""
        provider = GitHubActionsProvider(owner="user", repo="repo")

        assert provider.owner == "user"
        assert provider.repo == "repo"
        assert provider.token is None

    @patch("scout.providers.github_actions.requests.get")
    def test_get_workflow_runs_success(self, mock_get, provider, mock_response):
        """Test successful retrieval of workflow runs."""
        mock_response.json.return_value = {
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 123456,
                    "name": "CI Tests",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "abc123",
                    "created_at": "2026-02-01T10:00:00Z",
                    "updated_at": "2026-02-01T10:15:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/123456",
                },
                {
                    "id": 123457,
                    "name": "CI Tests",
                    "status": "completed",
                    "conclusion": "failure",
                    "head_branch": "main",
                    "head_sha": "def456",
                    "created_at": "2026-02-01T09:00:00Z",
                    "updated_at": "2026-02-01T09:15:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/123457",
                },
            ],
        }
        mock_get.return_value = mock_response

        runs = provider.get_workflow_runs(workflow="CI Tests", limit=2)

        assert len(runs) == 2
        assert runs[0].id == "123456"
        assert runs[0].workflow_name == "CI Tests"
        assert runs[0].status == "completed"
        assert runs[0].conclusion == "success"
        assert runs[1].conclusion == "failure"

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "per_page=2" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == "token test_token_123"

    @patch("scout.providers.github_actions.requests.get")
    def test_get_workflow_run_success(self, mock_get, provider, mock_response):
        """Test successful retrieval of a specific workflow run."""
        mock_response.json.return_value = {
            "id": 123456,
            "name": "CI Tests",
            "status": "completed",
            "conclusion": "success",
            "head_branch": "main",
            "head_sha": "abc123",
            "created_at": "2026-02-01T10:00:00Z",
            "updated_at": "2026-02-01T10:15:00Z",
            "html_url": "https://github.com/user/repo/actions/runs/123456",
        }
        mock_get.return_value = mock_response

        run = provider.get_workflow_run(run_id="123456")

        assert run.id == "123456"
        assert run.workflow_name == "CI Tests"
        assert run.conclusion == "success"

        # Verify API call
        mock_get.assert_called_once()
        assert "actions/runs/123456" in mock_get.call_args[0][0]

    @patch("scout.providers.github_actions.requests.get")
    def test_get_jobs_success(self, mock_get, provider, mock_response):
        """Test successful retrieval of jobs for a workflow run."""
        mock_response.json.return_value = {
            "total_count": 2,
            "jobs": [
                {
                    "id": 789,
                    "name": "test (ubuntu-latest, 3.10)",
                    "status": "completed",
                    "conclusion": "failure",
                    "started_at": "2026-02-01T10:00:00Z",
                    "completed_at": "2026-02-01T10:05:00Z",
                    "html_url": "https://github.com/user/repo/runs/789",
                },
                {
                    "id": 790,
                    "name": "test (ubuntu-latest, 3.11)",
                    "status": "completed",
                    "conclusion": "success",
                    "started_at": "2026-02-01T10:00:00Z",
                    "completed_at": "2026-02-01T10:04:00Z",
                    "html_url": "https://github.com/user/repo/runs/790",
                },
            ],
        }
        mock_get.return_value = mock_response

        jobs = provider.get_jobs(run_id="123456")

        assert len(jobs) == 2
        assert jobs[0].id == "789"
        assert jobs[0].name == "test (ubuntu-latest, 3.10)"
        assert jobs[0].conclusion == "failure"
        assert jobs[1].conclusion == "success"

    @patch("scout.providers.github_actions.requests.get")
    def test_get_logs_success(self, mock_get, provider, mock_response):
        """Test successful retrieval of logs for a job."""
        mock_response.content = b"""2026-02-01T10:00:00.000Z Running tests...
2026-02-01T10:00:01.000Z test_example.py::test_one PASSED
2026-02-01T10:00:02.000Z test_example.py::test_two FAILED
"""
        mock_get.return_value = mock_response

        logs = provider.get_logs(job_id="789")

        assert len(logs) == 3
        assert logs[0].line_number == 1
        assert "Running tests" in logs[0].content
        assert logs[1].line_number == 2
        assert "PASSED" in logs[1].content
        assert logs[2].line_number == 3
        assert "FAILED" in logs[2].content

    @patch("scout.providers.github_actions.requests.get")
    def test_authentication_with_token(self, mock_get, provider, mock_response):
        """Test that authentication token is included in requests."""
        mock_response.json.return_value = {"workflow_runs": []}
        mock_get.return_value = mock_response

        provider.get_workflow_runs(workflow="test")

        headers = mock_get.call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test_token_123"

    @patch("scout.providers.github_actions.requests.get")
    def test_authentication_without_token(self, mock_get, mock_response):
        """Test requests without authentication token."""
        provider = GitHubActionsProvider(owner="user", repo="repo")
        mock_response.json.return_value = {"workflow_runs": []}
        mock_get.return_value = mock_response

        provider.get_workflow_runs(workflow="test")

        headers = mock_get.call_args[1]["headers"]
        assert "Authorization" not in headers

    @patch("scout.providers.github_actions.requests.get")
    def test_rate_limiting_error_handling(self, mock_get, provider):
        """Test handling of GitHub API rate limiting."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "message": "API rate limit exceeded",
            "documentation_url": (
                "https://docs.github.com/rest/overview/" "resources-in-the-rest-api#rate-limiting"
            ),
        }
        mock_response.raise_for_status.side_effect = HTTPError("403 Client Error: Forbidden")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError, match="403"):
            provider.get_workflow_runs(workflow="test")

    @patch("scout.providers.github_actions.requests.get")
    def test_404_not_found_error_handling(self, mock_get, provider):
        """Test handling of 404 errors for non-existent resources."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError("404 Client Error: Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(HTTPError, match="404"):
            provider.get_workflow_run(run_id="999999")

    @patch("scout.providers.github_actions.requests.get")
    def test_network_timeout_error_handling(self, mock_get, provider):
        """Test handling of network timeout errors."""
        mock_get.side_effect = Timeout("Connection timed out")

        with pytest.raises(Timeout, match="timed out"):
            provider.get_workflow_runs(workflow="test")

    @patch("scout.providers.github_actions.requests.get")
    def test_generic_request_error_handling(self, mock_get, provider):
        """Test handling of generic request errors."""
        mock_get.side_effect = RequestException("Network error")

        with pytest.raises(RequestException, match="Network error"):
            provider.get_workflow_runs(workflow="test")

    @patch("scout.providers.github_actions.requests.get")
    def test_malformed_response_handling(self, mock_get, provider):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON"):
            provider.get_workflow_runs(workflow="test")

    @patch("scout.providers.github_actions.requests.get")
    def test_pagination_support(self, mock_get, provider, mock_response):
        """Test that pagination parameters are correctly set."""
        mock_response.json.return_value = {"workflow_runs": []}
        mock_get.return_value = mock_response

        provider.get_workflow_runs(workflow="test", limit=50)

        call_url = mock_get.call_args[0][0]
        # When workflow is specified, fetch_limit = limit * 10 (capped at 100)
        # So for limit=50, fetch_limit=min(500, 100)=100
        assert "per_page=100" in call_url

    @patch("scout.providers.github_actions.requests.get")
    def test_workflow_name_filtering(self, mock_get, provider, mock_response):
        """Test filtering workflow runs by workflow name."""
        mock_response.json.return_value = {
            "workflow_runs": [
                {
                    "id": 1,
                    "name": "CI Tests",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "abc",
                    "created_at": "2026-02-01T10:00:00Z",
                    "updated_at": "2026-02-01T10:15:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/1",
                },
                {
                    "id": 2,
                    "name": "Other Workflow",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "def",
                    "created_at": "2026-02-01T10:00:00Z",
                    "updated_at": "2026-02-01T10:15:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/2",
                },
            ]
        }
        mock_get.return_value = mock_response

        runs = provider.get_workflow_runs(workflow="CI Tests")

        # Should filter to only "CI Tests" workflow
        assert len(runs) == 1
        assert runs[0].workflow_name == "CI Tests"

    @patch("scout.providers.github_actions.requests.get")
    def test_get_logs_with_invalid_timestamps(self, mock_get, provider, mock_response):
        """Test handling of log lines with invalid or missing timestamps."""
        mock_response.content = b"""not-a-timestamp This line has invalid timestamp
Line without space
2026-02-01T10:00:00.000Z Valid timestamp line
"""
        mock_get.return_value = mock_response

        logs = provider.get_logs(job_id="789")

        assert len(logs) == 3
        # Invalid timestamp line should still parse
        assert "invalid timestamp" in logs[0].content.lower()
        # Line without space should parse
        assert logs[1].content == "Line without space"
        # Valid timestamp should parse correctly
        assert "Valid timestamp line" in logs[2].content

    @patch("scout.providers.github_actions.requests.get")
    def test_get_logs_with_empty_lines(self, mock_get, provider, mock_response):
        """Test handling of empty log lines."""
        mock_response.content = b"""2026-02-01T10:00:00.000Z First line

2026-02-01T10:00:02.000Z Third line
"""
        mock_get.return_value = mock_response

        logs = provider.get_logs(job_id="789")

        # Should handle empty lines
        assert len(logs) == 3
        assert logs[1].content == ""
