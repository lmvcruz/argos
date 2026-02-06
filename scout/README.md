# Scout - CI Execution Inspector

Scout is a **CI execution data collection and analysis tool** that bridges the gap between GitHub Actions and local development. It fetches CI logs, parses test results, detects failure patterns, and makes the data queryable locally.

## 1. Introduction

### Purpose
Scout solves a critical problem: **understanding why CI is failing**. It:
- Retrieves CI execution logs from GitHub Actions
- Parses test failures, error messages, and stack traces
- Detects patterns (flaky tests, recurring failures, platform-specific issues)
- Stores everything in a local database for fast querying
- Integrates with Anvil and Lens for visualization and analysis

### Name Origin
"Scout" reflects its role: it **scouts ahead** to GitHub Actions, retrieves CI data, and brings it back for analysis. Like a military scout gathering intelligence.

### Role in Argos Ecosystem
Scout is the **data ingestion layer** of Argos:
- **Scout** → Collects and analyzes CI data
- **Anvil** → Manages and processes the collected data
- **Lens** → Visualizes and explores patterns
- **Forge, Verdict, Gaze** → Provide specialized analysis and reporting

---

## 2. Installation

### Prerequisites
- Python 3.8+
- GitHub account (for accessing GitHub Actions)
- Git repository with GitHub Actions workflows

### Quick Install

```bash
cd scout
pip install -e ".[dev]"
```

### Authentication

Scout requires **three pieces of information** to access GitHub:
1. **GitHub Token** - Your personal access token
2. **Repository Owner** - GitHub username or organization
3. **Repository Name** - Name of the repository

All three can be provided via **CLI arguments**, **environment variables**, or **.env file**.

#### Token Configuration

**Method 1: Environment variable**
```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

**Method 2: .env file** (requires `pip install python-dotenv`)
```
GITHUB_TOKEN=your_github_personal_access_token
```

**Method 3: Command-line argument**
```bash
scout list --token your_github_token
```

Priority: CLI argument → environment variable → .env file

#### Repository Configuration

Scout requires the repository in **`owner/repo` format** (owner and repo are combined):

**Method 1: Environment variable**
```bash
export GITHUB_REPO=owner/repository_name
```

**Method 2: .env file**
```
GITHUB_REPO=owner/repository_name
```

**Method 3: Command-line argument**
```bash
scout list --repo owner/repository_name
```

#### Complete Example

Set all credentials via environment variables:
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
export GITHUB_REPO=lmvcruz/argos
scout list
```

Or set via .env file (`.env`):
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=lmvcruz/argos
```

Then run any Scout command:
```bash
scout list
scout fetch --all
scout db-list
```

Or override via CLI arguments:
```bash
scout list --token ghp_xxxxxxxxxxxxxxxxxxxx --repo lmvcruz/argos
```

---

## 3. Functionalities

Scout provides 9 core commands organized into 3 groups:

### 📥 Data Ingestion

**`scout fetch`** — Retrieve CI executions from GitHub Actions
```bash
scout fetch --workflow test.yml --branch main --last 10
scout fetch --all  # Fetch all workflows
```
Stores executions in local database.

**`scout parse`** — Parse logs and extract test results
```bash
scout parse <run_id> --format pytest
```
Analyzes logs to extract failures, stack traces, and error patterns.

### 💾 Local Database

**`scout db-list`** — List executions stored locally
```bash
scout db-list --workflow test.yml --status completed --last 20
```
Query the local Scout database without hitting GitHub API.

**`scout show-log`** — Display logs for a specific execution
```bash
scout show-log <run_id>
```
Shows raw job logs with test summaries.

**`scout show-data`** — Display parsed analysis data
```bash
scout show-data <run_id> --format json
```
Shows test statistics, failure patterns, and trends.

### 🔄 Combined Operations

**`scout sync`** — Fetch AND parse in one command
```bash
scout sync --workflow test.yml --last 5
```
Special command combining fetch + parse for efficiency.

### Remote CI Queries

**`scout list`** — Query GitHub Actions directly (without local DB)
```bash
scout list --workflow test.yml --branch main
```
Live queries to GitHub; slower but always current.

**`scout analyze`** — Analyze a specific GitHub Actions run
```bash
scout analyze <run_id>
```
Deep analysis of a single execution.

---

## 4. Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│         Scout CLI Interface                 │
│  (fetch, parse, list, show-log, show-data) │
└────────────┬────────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌──────────────┐  ┌──────────────────┐
│ GitHub API   │  │  Local Database  │
│  Provider    │  │   (SQLAlchemy)   │
└──────────────┘  └──────────────────┘
      │                    │
      │                    ▼
      │            ┌──────────────────┐
      │            │  Data Storage    │
      │            │ (WorkflowRun,    │
      │            │  WorkflowJob,    │
      │            │  TestResult,     │
      │            │  AnalysisResult) │
      │            └──────────────────┘
      │
      ▼
┌──────────────────┐
│  Log Parser      │
│ (Pytest, Unit,   │
│  Google Test)    │
└──────────────────┘
```

### How It Works

1. **Fetch Phase**: Connects to GitHub Actions, retrieves workflow runs and job logs
2. **Store Phase**: Saves data in two locations:
   - **SQLite Database**: Workflow metadata, job details, and parsed test results
   - **File Cache**: Raw CI logs organized by run ID and job ID
3. **Parse Phase**: Analyzes logs to extract test failures, patterns, and statistics
4. **Query Phase**: Provides fast local queries via CLI or API (can access both database and logs)

---

## 5. Implementation Details

### 5.1 Case Identification
Each CI execution is uniquely identified by:
- **Run ID** (GitHub workflow run number)
- **Job ID** (specific job within run)
- **Workflow Name** (e.g., `test.yml`)
- **Branch** (e.g., `main`, `develop`)

Supports both direct IDs and human-readable identifiers.

### 5.2 CI Authentication
- GitHub Personal Access Token (classic or fine-grained)
- Token provided via:
  - `GITHUB_TOKEN` environment variable
  - `--token` command-line argument
  - ⚠️ Config file support not yet implemented

### 5.3 Local Database Schema

Scout stores CI data in **two locations**:

#### SQLite Database (`scout.db`)

Stores structured metadata and parsed data:

**WorkflowRun** (Workflow execution metadata)
```python
- run_id (int, primary key)
- workflow_name (str)
- branch (str)
- status (str): queued, in_progress, completed
- conclusion (str): success, failure, neutral
- started_at, completed_at (datetime)
```

**WorkflowJob** (Individual job within run)
```python
- job_id (str, primary key)
- run_id (foreign key)
- job_name, runner_os, python_version
- status, conclusion
- log_content (text): raw logs stored here
```

**WorkflowTestResult** (Parsed test execution)
```python
- test_name (str)
- status (str): passed, failed, skipped
- duration_ms (int)
- error_message, stack_trace
- runner_os (str)
- python_version (str)
```

**AnalysisResult** (Failure patterns and trends)
```python
- run_id (foreign key)
- total_tests, passed, failed, skipped
- failure_patterns (json)
- flaky_tests (json)
```

#### File System Cache (Log Storage)

Stores raw CI logs separately for quick access without SQL queries:

```
~/.scout/logs/
├── run_123456/
│   ├── job_1.log          # Raw log lines
│   ├── job_1.meta         # Metadata (retrieved_at, size, etc.)
│   ├── job_2.log
│   └── job_2.meta
├── run_123457/
│   ├── job_1.log
│   └── job_1.meta
```

This dual-storage approach allows:
- **Fast queries** on database (structured data, patterns, statistics)
- **Raw log access** via file cache (complete log content, debugging)

### 5.4 Integration with Anvil
Scout provides data to Anvil via:
- **Direct database access** (shared SQLite file)
- **REST API** (planned)
- **JSON export** (for batch processing)

### 5.5 Integration with Lens
Lens queries Scout data through:
- **REST API endpoints** (`/api/scout/list`, `/api/scout/show-log`, etc.)
- **WebSocket** (for live updates)
- **Direct database** (for advanced queries)

### 5.6 Error Handling
- **Network errors**: Retries with exponential backoff
- **GitHub rate limits**: Respects 429 responses, waits appropriately
- **Parse failures**: Logs errors, continues with partial data
- **Database errors**: Transaction rollback, detailed logging

### 5.7 Logging
- **File logging**: `~/.scout/logs/scout.log`
- **Console logging**: Configurable verbosity (`-v`, `-vv`, `-q`)
- **Structured logging**: JSON format for machine parsing
- **Debug mode**: `scout --debug` for detailed tracing

### 5.8 Dependencies
Core dependencies:
- `requests` — HTTP requests to GitHub API
- `sqlalchemy` — ORM for database
- `pydantic` — Data validation
- `click` — CLI framework
- `pytest` — Test framework (for parsing)

---

## 6. Test Strategy

### Test Organization
```
tests/
├── test_cli.py              # Command-line interface tests
├── test_cli_handlers.py     # Command handler logic
├── test_providers.py        # GitHub API provider
├── test_storage.py          # Database operations
├── test_failure_parser.py   # Log parsing
├── test_ci_log_parser.py    # CI log format parsing
├── test_analysis.py         # Pattern detection
└── test_integration.py      # End-to-end tests
```

### Coverage Goals
- **Line coverage**: 90%+
- **Critical path coverage**: 100%
  - Database operations
  - GitHub API interactions
  - Test failure parsing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scout

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v
```

---

## 7. Future Enhancements

### Short Term
- [ ] Batch processing for large workflow histories
- [ ] Export to CSV/JSON formats
- [ ] Cache GitHub API responses to reduce rate limiting
- [ ] Additional test framework parsers (Jest, Mocha, etc.)

### Medium Term
- [ ] Machine learning for failure prediction
- [ ] Integration with issue tracking (GitHub Issues, Jira)
- [ ] Slack/email notifications for critical failures
- [ ] Web UI for live monitoring

### Long Term
- [ ] Multi-repository support
- [ ] Historical trend analysis and forecasting
- [ ] Automated remediation suggestions
- [ ] Integration with multiple CI providers (GitLab CI, CircleCI, Jenkins)

---

## Quick Reference

See [Command Summary](docs/QUICK_REFERENCE.md) for complete command listing.

For detailed examples and workflows, see [Scout CLI Database Commands Guide](docs/scout-cli-database-commands.md).

---

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run pre-commit checks
python scripts/pre-commit-check.py

# Build and test
pytest
```
