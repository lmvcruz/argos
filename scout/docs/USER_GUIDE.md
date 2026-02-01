# Scout User Guide

## Introduction

Scout is a CI/CD inspection and failure analysis tool, part of the Argos ecosystem. It helps you investigate test failures, analyze trends, and improve your CI/CD pipeline reliability.

## Installation

```bash
# From PyPI (when published)
pip install argos-scout

# From source (development)
git clone https://github.com/lmvcruz/argos.git
cd argos/scout
pip install -e ".[dev]"
```

## Quick Start

### GitHub Actions Integration

Scout currently supports GitHub Actions as its primary CI provider.

```python
from scout.providers import GitHubActionsProvider

# Initialize provider
provider = GitHubActionsProvider(
    owner="your-username",
    repo="your-repo",
    token="ghp_your_github_token"  # Optional but recommended
)

# Get recent workflow runs
runs = provider.get_workflow_runs(workflow="CI Tests", limit=10)
for run in runs:
    print(f"{run.id}: {run.status} - {run.conclusion}")

# Get specific run details
run = provider.get_workflow_run(run_id="123456")
print(f"Workflow: {run.workflow_name}")
print(f"Branch: {run.branch}")
print(f"Commit: {run.commit_sha}")

# Get jobs for a run
jobs = provider.get_jobs(run_id="123456")
for job in jobs:
    print(f"{job.name}: {job.conclusion}")

# Get logs for a specific job
logs = provider.get_logs(job_id="789")
for entry in logs[:10]:  # First 10 lines
    print(f"{entry.line_number}: {entry.content}")
```

## Authentication

### GitHub Personal Access Token

To avoid rate limits and access private repositories, create a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Action workflows
4. Generate and copy the token
5. Use it when initializing the provider:

```python
provider = GitHubActionsProvider(
    owner="user",
    repo="repo",
    token="ghp_xxxxxxxxxxxx"
)
```

### Environment Variable

You can also store the token in an environment variable:

```python
import os
from scout.providers import GitHubActionsProvider

token = os.getenv("GITHUB_TOKEN")
provider = GitHubActionsProvider(
    owner="user",
    repo="repo",
    token=token
)
```

## CI Provider Interface

Scout uses an abstract `CIProvider` interface that allows you to implement support for additional CI/CD platforms.

### Implementing a Custom Provider

```python
from scout.providers import CIProvider, WorkflowRun, Job, LogEntry
from typing import List

class CustomCIProvider(CIProvider):
    """Custom CI provider implementation."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def get_workflow_runs(self, workflow: str, limit: int = 10) -> List[WorkflowRun]:
        # Implement API call to get workflow runs
        pass

    def get_workflow_run(self, run_id: str) -> WorkflowRun:
        # Implement API call to get specific run
        pass

    def get_jobs(self, run_id: str) -> List[Job]:
        # Implement API call to get jobs
        pass

    def get_logs(self, job_id: str) -> List[LogEntry]:
        # Implement API call to get logs
        pass
```

## Data Models

### WorkflowRun

Represents a CI workflow run.

```python
@dataclass
class WorkflowRun:
    id: str                      # Unique identifier
    workflow_name: str           # Workflow name
    status: str                  # Current status
    conclusion: Optional[str]    # Final conclusion (if completed)
    branch: str                  # Git branch
    commit_sha: str             # Git commit SHA
    created_at: datetime        # Creation timestamp
    updated_at: datetime        # Last update timestamp
    url: str                    # URL to view run
```

### Job

Represents a job within a workflow run.

```python
@dataclass
class Job:
    id: str                         # Unique identifier
    name: str                       # Job name
    status: str                     # Current status
    conclusion: Optional[str]       # Final conclusion
    started_at: datetime           # Start timestamp
    completed_at: Optional[datetime]  # Completion timestamp
    url: str                       # URL to view job
```

### LogEntry

Represents a log entry from a job.

```python
@dataclass
class LogEntry:
    timestamp: datetime    # Entry timestamp
    line_number: int      # Line number in log
    content: str          # Log content
```

## Error Handling

Scout raises standard Python exceptions for error conditions:

```python
from requests.exceptions import HTTPError, Timeout, RequestException

try:
    runs = provider.get_workflow_runs("CI Tests")
except HTTPError as e:
    if e.response.status_code == 403:
        print("Rate limit exceeded or authentication failed")
    elif e.response.status_code == 404:
        print("Repository or workflow not found")
    else:
        print(f"HTTP error: {e}")
except Timeout:
    print("Request timed out")
except RequestException as e:
    print(f"Network error: {e}")
```

## Best Practices

### Rate Limiting

GitHub API has rate limits:
- **Authenticated requests**: 5,000 requests per hour
- **Unauthenticated requests**: 60 requests per hour

Always use a token for production use.

### Caching

For better performance, cache workflow runs and logs:

```python
import time
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_run(run_id: str):
    return provider.get_workflow_run(run_id)

# Cache expires after 5 minutes
run = get_cached_run("123456")
```

### Pagination

When retrieving many runs, use pagination:

```python
# Get last 50 runs
runs = provider.get_workflow_runs(workflow="CI Tests", limit=50)
```

## Examples

### Find Recent Failures

```python
provider = GitHubActionsProvider(owner="user", repo="repo", token=token)
runs = provider.get_workflow_runs("CI Tests", limit=20)

failed_runs = [r for r in runs if r.conclusion == "failure"]
print(f"Found {len(failed_runs)} failed runs in last 20:")

for run in failed_runs:
    print(f"\nRun {run.id} - {run.created_at}")
    jobs = provider.get_jobs(run.id)
    failed_jobs = [j for j in jobs if j.conclusion == "failure"]
    for job in failed_jobs:
        print(f"  ❌ {job.name}")
```

### Analyze Flaky Tests

```python
from collections import Counter

# Get last 50 runs
runs = provider.get_workflow_runs("CI Tests", limit=50)

job_results = Counter()
for run in runs:
    jobs = provider.get_jobs(run.id)
    for job in jobs:
        key = (job.name, job.conclusion)
        job_results[key] += 1

# Find jobs that sometimes pass, sometimes fail
for (name, conclusion), count in job_results.items():
    opposite_key = (name, "success" if conclusion == "failure" else "failure")
    if opposite_key in job_results:
        total = count + job_results[opposite_key]
        failure_rate = (job_results[(name, "failure")] / total) * 100
        print(f"{name}: {failure_rate:.1f}% failure rate (flaky)")
```

### Extract Error Messages from Logs

```python
import re

def extract_failures(logs):
    """Extract FAILED test lines from pytest output."""
    failures = []
    for entry in logs:
        if "FAILED" in entry.content:
            failures.append(entry.content)
    return failures

run = provider.get_workflow_run("123456")
jobs = provider.get_jobs(run.id)

for job in jobs:
    if job.conclusion == "failure":
        logs = provider.get_logs(job.id)
        failures = extract_failures(logs)
        if failures:
            print(f"\nJob: {job.name}")
            for failure in failures:
                print(f"  {failure}")
```

## Troubleshooting

### Rate Limit Exceeded

**Error**: `403 Forbidden - API rate limit exceeded`

**Solution**: Use a GitHub Personal Access Token for authentication.

### Authentication Failed

**Error**: `401 Unauthorized - Bad credentials`

**Solution**: Check that your token is valid and has the required scopes.

### Workflow Not Found

**Error**: `No workflow runs found for workflow "X"`

**Solution**: Verify the workflow name matches exactly (case-sensitive).

### Network Timeouts

**Error**: `Timeout: Connection timed out`

**Solution**: Check network connectivity or increase timeout:

```python
import requests
from scout.providers import GitHubActionsProvider

# Increase timeout (if you modify the provider)
session = requests.Session()
session.timeout = 30  # 30 seconds
```

## Next Steps

- Learn about failure analysis in the [Analysis Guide](ANALYSIS_GUIDE.md)
- Explore CI/CD trends in the [Trends Guide](TRENDS_GUIDE.md)
- Contribute to Scout development in [CONTRIBUTING.md](../CONTRIBUTING.md)

## Support

- GitHub Issues: https://github.com/lmvcruz/argos/issues
- Documentation: https://github.com/lmvcruz/argos/tree/main/scout/docs
