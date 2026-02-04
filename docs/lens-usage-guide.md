# Lens Usage Guide

## Overview

**Lens** is a CI/CD analytics platform that helps you:
- Monitor CI health and pass rates across platforms (Windows, Linux, macOS)
- Detect flaky tests with detailed failure analysis
- Compare local execution results vs CI results
- Analyze platform-specific failure patterns
- Generate reproduction scripts for CI failures

## Architecture

```
GitHub Actions CI Runs
        ↓
    Scout (CI log parser)
        ↓
Anvil (Execution database)
        ↓
   Lens Backend (FastAPI)
        ↓
Lens Frontend (React)
```

## Getting Started

### 1. Start the Lens Backend and Frontend

**Terminal 1 - Backend:**
```bash
cd d:\playground\argos\lens
python -m uvicorn lens.backend.server:app --host 127.0.0.1 --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd d:\playground\argos\lens\frontend
npm run dev
```

Then open: **http://localhost:3000**

### 2. Sync CI Data from GitHub

Go to the **"GitHub Sync"** page in Lens and:

1. Create a GitHub Personal Access Token:
   - Visit: https://github.com/settings/tokens
   - Click "Generate new token" (classic)
   - Give it `repo` scope access
   - Copy the token

2. In Lens, enter:
   - GitHub Token: `ghp_xxxxx...` (or set `GITHUB_TOKEN` env var)
   - Repository Owner: `lmvcruz` (or your GitHub username)
   - Repository Name: `argos` (or your repo name)

3. Click **"Sync CI Data from GitHub"**

   This will:
   - Fetch all GitHub Actions workflow runs
   - Parse pytest output, linting results, and coverage data
   - Store everything in Anvil database (`.anvil/execution.db`)

### 3. View CI Analytics

#### **CI Health Dashboard**
- Real-time pass rate trends
- Platform distribution (Windows, Linux, macOS)
- Recent execution history
- Success/failure statistics

#### **Local vs CI Comparison**
- Search for a test by node ID or file path
- Compare results between your local machine and CI
- See which platforms have issues

#### **Flaky Tests**
- Configurable failure threshold
- Lookback period (number of CI runs to analyze)
- Severity recommendations (high/moderate/minor)
- Failure rate percentages

#### **Failure Patterns**
- Platform-specific failures (Windows-only, Linux-only, etc.)
- Platform-specific reproduction commands
- Docker commands for testing in containers
- Common causes and debugging tips

## API Integration

### REST Endpoints

**Check Server Health:**
```bash
curl http://localhost:8001/api/health
```

**Sync CI Data from GitHub:**
```bash
curl -X POST "http://localhost:8001/api/ci/sync?github_token=ghp_xxx&owner=lmvcruz&repo=argos"
```

**Get CI Executions:**
```bash
curl "http://localhost:8001/api/ci/executions?limit=50"
```

**Get CI Statistics:**
```bash
curl "http://localhost:8001/api/ci/statistics"
```

**Compare Entity (Test):**
```bash
curl "http://localhost:8001/api/comparison/entity/test::TestClass::test_method"
```

**Get Flaky Tests:**
```bash
curl "http://localhost:8001/api/comparison/flaky?threshold=3&lookback_runs=10"
```

**Get Platform-Specific Failures:**
```bash
curl "http://localhost:8001/api/comparison/platform-specific-failures"
```

## Database

CI data is stored in: `.anvil/execution.db`

This SQLite database contains:
- Execution history (test results, coverage, linting)
- Platform information (Windows, Linux, macOS)
- Timestamp information for trend analysis

## Troubleshooting

### "Backend Server Unavailable"
Make sure the backend is running on port 8001:
```bash
cd d:\playground\argos\lens
python -m uvicorn lens.backend.server:app --host 127.0.0.1 --port 8001
```

### "No CI data available"
Click the **"GitHub Sync"** button in the sidebar to sync CI data first.

### "GitHub token required"
- Ensure you have a valid GitHub token with `repo` scope
- Either pass it to the sync endpoint or set `GITHUB_TOKEN` environment variable

### Port Already in Use
If port 8001 is in use, you can use a different port:
```bash
python -m uvicorn lens.backend.server:app --host 127.0.0.1 --port 8002
```

Then update `lens/frontend/vite.config.js`:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8002',
    changeOrigin: true,
  },
  '/ws': {
    target: 'ws://localhost:8002',
    ws: true,
  },
},
```

## Integration with Scout and Anvil

Lens automatically integrates with:

**Scout** - CI log parser at `d:\playground\argos\scout`
- Extracts test results, linting issues, coverage data from GitHub Actions logs
- Identifies platform-specific failures

**Anvil** - Execution database at `d:\playground\argos\anvil`
- Stores CI execution history
- Provides queries for trend analysis
- Supports platform filtering and comparisons

## Real-World Workflow

1. **Run your CI/CD pipeline** on GitHub Actions
   - Tests fail on Windows, pass on Linux
   - Some tests are flaky (intermittent failures)

2. **Sync with Lens**
   - Click "GitHub Sync" in Lens
   - Wait for sync to complete

3. **Analyze with Lens**
   - View CI Dashboard → See Windows has higher failure rate
   - Go to Failure Patterns → Identify Windows-only issues
   - Check Flaky Tests → See which tests fail intermittently
   - Use Comparison to test locally and compare results

4. **Debug and Fix**
   - Generate reproduction script for Windows failures
   - Run in Docker container on Windows image
   - Fix the code
   - Push to GitHub
   - Lens shows improved metrics in next sync

## Advanced Usage

### Custom Analysis

For custom CI analysis, you can directly access the Anvil database:

```python
from anvil.storage import ExecutionDatabase, CIStorageLayer

db = ExecutionDatabase(".anvil/execution.db")
ci_storage = CIStorageLayer(db)

# Get all CI executions
executions = ci_storage.get_ci_executions(limit=100)

# Get statistics by platform
stats = ci_storage.get_ci_statistics_by_platform()

# Compare a test locally vs in CI
comparison = ci_storage.compare_local_vs_ci("test::TestClass::test_method")

# Get flaky tests
flaky = ci_storage.get_flaky_tests_in_ci(threshold=3)
```

### WebSocket Streaming

Lens backend supports WebSocket for real-time streaming:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'ci_sync_completed') {
    console.log('CI sync finished:', message.status);
  }
};
```

## Next Steps

- **Phase 0.9**: End-to-end testing with real CI workflows
- **Phase 1.0**: Production deployment and documentation
- **Future**: Machine learning for failure prediction, automated remediation
