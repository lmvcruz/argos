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
- **Scout** → Collects CI execution data from GitHub Actions, stores in Scout DB
- **Anvil** → Manages local execution data, provides validator parsers
- **AnvilBridge** → Parser adapter (Scout uses Anvil parsers, NO database writes)
- **Lens** → Visualizes both Scout (CI) and Anvil (local) data
- **Forge, Verdict, Gaze** → Provide specialized analysis and reporting

**Database Separation:**
- **Scout DB** (`~/.scout/owner/repo/scout.db`): CI executions ONLY
- **Anvil DB** (`~/.anvil/project/anvil_stats.db`): LOCAL executions ONLY
- **No data flows between Scout DB and Anvil DB**

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

### Multi-Repository Support

Scout is designed to support multiple repositories on the same machine. Each repository gets its own isolated data directory:

```
~/.scout/
├── <owner1>/
│   ├── <repo1>/
│   │   ├── scout.db                    (SQLite database)
│   │   ├── .scoutrc                    (Configuration file)
│   │   └── logs/                       (Raw CI logs)
│   └── <repo2>/
│       ├── scout.db
│       ├── .scoutrc
│       └── logs/
└── <owner2>/
    └── <repo1>/
        ├── scout.db
        ├── .scoutrc
        └── logs/
```

This allows you to:
- Work with multiple repositories simultaneously
- Keep data for each repository isolated
- Switch between repositories easily
- Store credentials per-repo (optional, in `.scoutrc`)

### Authentication

Scout requires **three pieces of information** to access GitHub:
1. **GitHub Token** - Your personal access token
2. **Repository Owner** - GitHub username or organization (REQUIRED)
3. **Repository Name** - Name of the repository (REQUIRED)

The repository is now **required** for all Scout commands. It can be provided via **CLI arguments**, **environment variables**, or **.scoutrc config file**.

#### Token Configuration

**Method 1: Command-line argument** (highest priority)
```bash
scout fetch --repo owner/repo --token your_github_token --workflow test.yml
```

**Method 2: Environment variable**
```bash
export GITHUB_TOKEN=your_github_personal_access_token
scout fetch --repo owner/repo --workflow test.yml
```

**Method 3: .env file** (requires `pip install python-dotenv`)
```
GITHUB_TOKEN=your_github_personal_access_token
```

**Method 4: .scoutrc per-repo config file** (lowest priority)
Store credentials in `~/.scout/<owner>/<repo>/.scoutrc`:
```json
{
  "owner": "owner",
  "repo": "repo",
  "token": "your_github_personal_access_token"
}
```

Priority: CLI argument → environment variable → .env file → .scoutrc

#### Repository Configuration

Scout requires the repository in **`owner/repo` format**. This is now **REQUIRED** for all commands:

**Method 1: Command-line argument** (required or via env var)
```bash
scout fetch --repo owner/repo --workflow test.yml
scout list --repo owner/repo
scout db-list --repo owner/repo
```

**Method 2: Environment variable**
```bash
export GITHUB_REPO=owner/repo
scout fetch --workflow test.yml  # Will use GITHUB_REPO
```

#### Complete Examples

**Example 1: Using CLI arguments (explicit)**
```bash
scout fetch --repo lmvcruz/argos --token ghp_xxxxxxxxxxxxxxxxxxxx --workflow test.yml
```

**Example 2: Using environment variables**
```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
export GITHUB_REPO=lmvcruz/argos
scout fetch --workflow test.yml  # --repo and --token inherited from env
```

**Example 3: Using .env file**
Create `.env` in your working directory:
```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=lmvcruz/argos
```

Then run:
```bash
scout fetch --workflow test.yml
```

**Example 4: Using .scoutrc config file**
Create `~/.scout/lmvcruz/argos/.scoutrc`:
```json
{
  "owner": "lmvcruz",
  "repo": "argos",
  "token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}
```

Then run:
```bash
scout fetch --repo lmvcruz/argos --workflow test.yml
```

**Example 5: Multiple repositories**
```bash
# Switch between repos easily - Scout keeps data isolated
scout fetch --repo lmvcruz/argos --workflow test.yml        # Data → ~/.scout/lmvcruz/argos/
scout fetch --repo user/another-repo --workflow ci.yml      # Data → ~/.scout/user/another-repo/
scout db-list --repo lmvcruz/argos                          # Lists data from first repo
scout db-list --repo user/another-repo                      # Lists data from second repo
```

---

## 3. Functionalities

Scout provides 9 core commands organized into 3 groups. **All commands require `--repo`** (or `GITHUB_REPO` env var).

### 📥 Data Ingestion

**`scout fetch`** — Retrieve CI executions from GitHub Actions
```bash
scout fetch --repo owner/repo --workflow test.yml --branch main --limit 10
scout fetch --repo owner/repo --workflow test.yml  # Fetch latest runs
```
Stores executions in `~/.scout/owner/repo/scout.db`.

**`scout parse`** — Parse logs and extract test results
```bash
# Parse all jobs in a run
scout parse --repo owner/repo --run-id <run_id>

# Parse a specific job by name
scout parse --repo owner/repo --run-id <run_id> --job-name "coverage"

# Parse from file
scout parse --input log_file.txt --output results.json
```
Analyzes logs to extract test failures, coverage data, and linting issues. The `--job-name` parameter allows parsing individual jobs within a run for focused analysis.

### 💾 Local Database

**`scout db-list`** — List executions stored locally
```bash
scout db-list --repo owner/repo --workflow test.yml --last 20
```
Query the repo-specific Scout database without hitting GitHub API.

**`scout show-log`** — Display logs for a specific execution
```bash
scout show-log --repo owner/repo <run_id>
```
Shows raw job logs with test summaries from `~/.scout/owner/repo/logs/`.

**`scout show-data`** — Display parsed analysis data
```bash
scout show-data --repo owner/repo <run_id> --format json
```
Shows test statistics, failure patterns, and trends.

### 🔄 Combined Operations

**`scout sync`** — Fetch AND parse in one command
```bash
scout sync --repo owner/repo --workflow test.yml --limit 5
```
Special command combining fetch + parse for efficiency.

### Remote CI Queries

**`scout list`** — Query GitHub Actions directly (without local DB)
```bash
scout list --repo owner/repo --workflow test.yml --branch main
```
Live queries to GitHub; slower but always current.

**`scout analyze`** — Analyze a specific GitHub Actions run
```bash
scout analyze --repo owner/repo <run_id>
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

- **GitHub Personal Access Token** (classic or fine-grained)
- **Repository** (required for all commands, in `owner/repo` format)

Tokens can be provided via (in priority order):
1. `--token` command-line argument
2. `GITHUB_TOKEN` environment variable
3. `.env` file (via python-dotenv)
4. `~/.scout/<owner>/<repo>/.scoutrc` configuration file

Repository can be provided via:
1. `--repo` command-line argument (required)
2. `GITHUB_REPO` environment variable

Each repository stores its data in an isolated directory: `~/.scout/<owner>/<repo>/`

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

Stores raw CI logs separately for quick access without SQL queries. Each repository has its own isolated cache:

```
~/.scout/<owner>/<repo>/logs/
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
- **Multi-repo support**: Each repo's data is completely isolated in `~/.scout/<owner>/<repo>/`
- **Easy repo switching**: Use `--repo owner/repo` to work with different repositories

### 5.4 Integration with Anvil
Scout leverages Anvil's validator parsers through AnvilBridge:
- **Parser Adapter**: AnvilBridge provides access to Anvil's specialized parsers (black, flake8, pylint, pytest, etc.)
- **NO Database Writes**: AnvilBridge does NOT write to Anvil DB
- **Data Flow**: Scout extracts validator output from CI logs → AnvilBridge parses → Scout saves to Scout DB
- **Database Separation**: Anvil DB contains local data, Scout DB contains CI data

Example:
```python
from scout.integration.anvil_bridge import AnvilBridge, AnvilLogExtractor

# Extract validator output from CI log
extractor = AnvilLogExtractor()
black_output = extractor.extract_validator_output(ci_log, "black")

# Parse using Anvil's parser
bridge = AnvilBridge()
result = bridge.parse_validator_output("black", black_output, files)

# Scout saves result to Scout DB (NOT Anvil DB)
```

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
