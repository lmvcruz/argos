# Scout API Reference

## Overview

This document provides detailed API documentation for Scout's core classes and methods.

## Modules

### scout.providers.base

Abstract base classes and data models for CI providers.

#### Classes

##### CIProvider

Abstract base class for CI provider implementations.

```python
class CIProvider(ABC):
    """Abstract base class for CI provider implementations."""
```

**Methods:**

- `get_workflow_runs(workflow: str, limit: int = 10) -> List[WorkflowRun]`

  Get recent workflow runs for a given workflow.

  **Parameters:**
  - `workflow` (str): Name of the workflow to retrieve runs for
  - `limit` (int): Maximum number of runs to retrieve (default: 10)

  **Returns:**
  - `List[WorkflowRun]`: List of workflow runs, ordered by most recent first

  **Raises:**
  - `HTTPError`: If API request fails
  - `Timeout`: If request times out
  - `RequestException`: For other network errors

- `get_workflow_run(run_id: str) -> WorkflowRun`

  Get details for a specific workflow run.

  **Parameters:**
  - `run_id` (str): Unique identifier for the workflow run

  **Returns:**
  - `WorkflowRun`: Workflow run details

  **Raises:**
  - `HTTPError`: If API request fails or run not found
  - `Timeout`: If request times out

- `get_jobs(run_id: str) -> List[Job]`

  Get all jobs for a specific workflow run.

  **Parameters:**
  - `run_id` (str): Unique identifier for the workflow run

  **Returns:**
  - `List[Job]`: List of jobs for the run

  **Raises:**
  - `HTTPError`: If API request fails
  - `Timeout`: If request times out

- `get_logs(job_id: str) -> List[LogEntry]`

  Get logs for a specific job.

  **Parameters:**
  - `job_id` (str): Unique identifier for the job

  **Returns:**
  - `List[LogEntry]`: List of log entries

  **Raises:**
  - `HTTPError`: If API request fails
  - `Timeout`: If request times out

##### WorkflowRun

Data model representing a CI workflow run.

```python
@dataclass
class WorkflowRun:
    id: str
    workflow_name: str
    status: str
    conclusion: Optional[str]
    branch: str
    commit_sha: str
    created_at: datetime
    updated_at: datetime
    url: str
```

**Attributes:**

- `id` (str): Unique identifier for the workflow run
- `workflow_name` (str): Name of the workflow
- `status` (str): Current status (e.g., "queued", "in_progress", "completed")
- `conclusion` (Optional[str]): Final conclusion if completed (e.g., "success", "failure", "cancelled")
- `branch` (str): Git branch being tested
- `commit_sha` (str): Git commit SHA
- `created_at` (datetime): When the run was created
- `updated_at` (datetime): When the run was last updated
- `url` (str): URL to view the run in the CI provider's UI

**Example:**

```python
run = WorkflowRun(
    id="123456",
    workflow_name="CI Tests",
    status="completed",
    conclusion="success",
    branch="main",
    commit_sha="abc123def456",
    created_at=datetime(2026, 2, 1, 10, 0, 0),
    updated_at=datetime(2026, 2, 1, 10, 15, 0),
    url="https://github.com/user/repo/actions/runs/123456"
)
```

##### Job

Data model representing a job within a workflow run.

```python
@dataclass
class Job:
    id: str
    name: str
    status: str
    conclusion: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    url: str
```

**Attributes:**

- `id` (str): Unique identifier for the job
- `name` (str): Name of the job
- `status` (str): Current status
- `conclusion` (Optional[str]): Final conclusion if completed
- `started_at` (datetime): When the job started
- `completed_at` (Optional[datetime]): When the job completed (None if still running)
- `url` (str): URL to view the job

**Example:**

```python
job = Job(
    id="789",
    name="test (ubuntu-latest, 3.10)",
    status="completed",
    conclusion="failure",
    started_at=datetime(2026, 2, 1, 10, 0, 0),
    completed_at=datetime(2026, 2, 1, 10, 5, 0),
    url="https://github.com/user/repo/actions/runs/123456/job/789"
)
```

##### LogEntry

Data model representing a single log entry.

```python
@dataclass
class LogEntry:
    timestamp: datetime
    line_number: int
    content: str
```

**Attributes:**

- `timestamp` (datetime): When the log entry was created
- `line_number` (int): Line number in the log file
- `content` (str): The log content

**Example:**

```python
entry = LogEntry(
    timestamp=datetime(2026, 2, 1, 10, 0, 0),
    line_number=42,
    content="Running tests..."
)
```

### scout.providers.github_actions

GitHub Actions provider implementation.

#### Classes

##### GitHubActionsProvider

GitHub Actions CI provider implementation.

```python
class GitHubActionsProvider(CIProvider):
    """GitHub Actions CI provider implementation."""

    BASE_URL = "https://api.github.com"
```

**Constructor:**

```python
def __init__(self, owner: str, repo: str, token: Optional[str] = None):
```

**Parameters:**
- `owner` (str): GitHub repository owner (username or organization)
- `repo` (str): GitHub repository name
- `token` (Optional[str]): GitHub personal access token (optional, but recommended)

**Example:**

```python
provider = GitHubActionsProvider(
    owner="octocat",
    repo="Hello-World",
    token="ghp_xxxxxxxxxxxx"
)
```

**Methods:**

All methods inherited from `CIProvider` are implemented. See CIProvider documentation above for method signatures and behavior.

**Private Methods:**

- `_get_headers() -> dict`

  Get HTTP headers for GitHub API requests, including authentication if token provided.

- `_parse_timestamp(timestamp_str: str) -> datetime`

  Parse ISO 8601 timestamp from GitHub API response.

**GitHub API Rate Limits:**

- **Authenticated requests**: 5,000 requests per hour
- **Unauthenticated requests**: 60 requests per hour

Always use a token for production use to avoid rate limiting.

**GitHub API Endpoints Used:**

- `GET /repos/{owner}/{repo}/actions/runs` - List workflow runs
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}` - Get workflow run
- `GET /repos/{owner}/{repo}/actions/runs/{run_id}/jobs` - List jobs
- `GET /repos/{owner}/{repo}/actions/jobs/{job_id}/logs` - Get job logs

## Usage Examples

### Basic Usage

```python
from scout.providers import GitHubActionsProvider

# Initialize provider
provider = GitHubActionsProvider(
    owner="your-username",
    repo="your-repo",
    token="your-github-token"
)

# Get recent workflow runs
runs = provider.get_workflow_runs(workflow="CI Tests", limit=10)

# Get specific run
run = provider.get_workflow_run(run_id="123456")

# Get jobs for run
jobs = provider.get_jobs(run_id="123456")

# Get logs for job
logs = provider.get_logs(job_id="789")
```

### Error Handling

```python
from requests.exceptions import HTTPError, Timeout

try:
    runs = provider.get_workflow_runs("CI Tests")
except HTTPError as e:
    if e.response.status_code == 403:
        print("Rate limit exceeded")
    elif e.response.status_code == 404:
        print("Repository not found")
except Timeout:
    print("Request timed out")
```

### Filtering and Analysis

```python
# Get failed runs
runs = provider.get_workflow_runs("CI Tests", limit=50)
failed_runs = [r for r in runs if r.conclusion == "failure"]

# Analyze job failures
for run in failed_runs:
    jobs = provider.get_jobs(run.id)
    failed_jobs = [j for j in jobs if j.conclusion == "failure"]
    print(f"Run {run.id}: {len(failed_jobs)} failed jobs")
```

## Type Hints

Scout uses type hints throughout. For best IDE support, use a type checker like mypy:

```bash
pip install mypy
mypy your_script.py
```

## Constants

### Status Values

Common status values from GitHub Actions:

- `"queued"` - Workflow/job is queued
- `"in_progress"` - Workflow/job is running
- `"completed"` - Workflow/job has finished

### Conclusion Values

Common conclusion values from GitHub Actions:

- `"success"` - Completed successfully
- `"failure"` - Failed
- `"cancelled"` - Cancelled by user
- `"skipped"` - Skipped
- `"timed_out"` - Timed out
- `"action_required"` - Action required
- `"neutral"` - Neutral conclusion

## See Also

- [User Guide](USER_GUIDE.md) - High-level usage guide
- [GitHub Actions API Documentation](https://docs.github.com/en/rest/actions) - Official API docs
