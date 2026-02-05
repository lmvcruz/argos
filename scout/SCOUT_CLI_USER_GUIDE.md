# Scout CLI User Guide

## Quick Start

Scout has been completely redesigned with a new 4-stage pipeline architecture and standardized parameter naming.

### Installation

The `scout` command is now available. Try:

```bash
scout --help
scout fetch --help
scout parse --help
scout sync --help
```

### Three Main Commands

1. **`scout fetch`** - Download CI logs from GitHub
2. **`scout parse`** - Transform logs using Anvil parsers
3. **`scout sync`** - Run complete pipeline (new!)

---

## Command Reference

### 1. `scout fetch` - Download CI Logs

Download raw CI execution logs from GitHub Actions.

#### Basic Usage

```bash
# Download and display logs
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Download and save to file
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output logs.txt

# Download and save to execution database
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-ci
```

#### Parameters

**Required:**
- `--workflow-name <NAME>` - Name of the workflow (e.g., "Tests", "Anvil Tests")

**Execution Identifier (one required):**
- `--run-id <ID>` - GitHub Actions numeric run ID
- `--execution-number <N>` - Human-readable number (e.g., "21")

**Job Identifier (optional unless used with --output or --save-ci):**
- `--job-id <ID>` - GitHub Actions numeric job ID
- `--action-name <NAME>` - Human-readable action name (e.g., "code quality")

**Output Options:**
- `--output <FILE>` - Save raw logs to text file
- `--save-ci` - Save to execution database (scout.db)
- `--ci-db <PATH>` - Custom path to execution database (default: scout.db)

**Common Options:**
- `--verbose` or `-v` - Show detailed progress
- `--quiet` or `-q` - Suppress output (errors still shown)
- `--token <TOKEN>` - GitHub token (or use GITHUB_TOKEN env var)

#### Examples

```bash
# Fetch with run-id and job-id
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Fetch with execution and action names
scout fetch --workflow-name "Anvil Tests" --execution-number "21" --action-name "code quality"

# Save to file for inspection
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output test_logs.txt

# Save to database for processing
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-ci

# Combined: Fetch and save both to file and database
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output logs.txt --save-ci

# Verbose mode to see what's happening
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" -v
```

---

### 2. `scout parse` - Transform and Analyze Logs

Parse CI logs using Anvil parsers and transform into standardized format.

#### Basic Usage

```bash
# Parse from file and display
scout parse --input logs.txt

# Parse from file and save results
scout parse --input logs.txt --output parsed.json

# Parse from file and save to analysis database
scout parse --input logs.txt --save-analysis

# Parse from execution database
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123"
```

#### Parameters

**Input Source (one required):**
- `--input <FILE>` - Read raw logs from file
- `--workflow-name <NAME>` - Query raw logs from execution database

**Case Identifiers (when using --workflow-name):**
- `--run-id <ID>` - GitHub Actions run ID
- `--execution-number <N>` - Execution number
- `--job-id <ID>` - GitHub Actions job ID
- `--action-name <NAME>` - Action name

**Output Options:**
- `--output <FILE>` - Save parsed results to JSON file
- `--save-analysis` - Save to analysis database
- `--analysis-db <PATH>` - Custom path to analysis database (default: scout-analysis.db)
- `--ci-db <PATH>` - Custom path to execution database (default: scout.db)

**Common Options:**
- `--verbose` or `-v` - Show detailed progress
- `--quiet` or `-q` - Suppress output

#### Examples

```bash
# Parse a single file
scout parse --input logs.txt

# Parse and save results to file
scout parse --input logs.txt --output parsed.json --verbose

# Parse from database using run-id and job-id
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Parse from database and save to analysis DB
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-analysis

# Parse with alternative identifiers
scout parse --workflow-name "Anvil Tests" --execution-number "21" --action-name "code quality" --save-analysis

# Dry-run: Parse without saving
scout parse --input logs.txt --output /dev/null
```

---

### 3. `scout sync` - Complete Pipeline (NEW!)

Run the entire 4-stage pipeline in one command: Fetch → Save-CI → Parse → Save-Analysis

The `sync` command offers great flexibility with multiple input modes and skip flags for selective execution.

#### Basic Usage

```bash
# Fetch all and sync
scout sync --fetch-all

# Fetch last 5 and sync
scout sync --fetch-last 5

# Fetch last 10 of specific workflow
scout sync --fetch-last 10 --filter-workflow "Tests"

# Process specific case
scout sync --workflow-name "Tests" --run-id 12345 --job-id "abc123"
```

#### Parameters

**Fetch Modes (mutually exclusive):**
- `--fetch-all` - Fetch all available executions
- `--fetch-last <N>` - Fetch last N executions (oldest-first ordering)
- `--workflow-name <NAME>` - Process specific workflow case

**Fetch Filtering (with --fetch-last):**
- `--filter-workflow <NAME>` - Filter fetched results by workflow name

**Case Identifiers (with --workflow-name):**
- `--run-id <ID>` - Run ID
- `--execution-number <N>` - Execution number
- `--job-id <ID>` - Job ID
- `--action-name <NAME>` - Action name

**Skip Flags (all optional):**
- `--skip-fetch` - Skip fetch (use cached data in execution DB)
- `--skip-save-ci` - Fetch but don't save raw logs
- `--skip-parse` - Skip parse stage
- `--skip-save-analysis` - Parse but don't save results

**Database Paths:**
- `--ci-db <PATH>` - Execution database (default: scout.db)
- `--analysis-db <PATH>` - Analysis database (default: scout-analysis.db)

**Common Options:**
- `--verbose` or `-v` - Show detailed progress
- `--quiet` or `-q` - Suppress output

#### Examples

**Simple Cases:**

```bash
# Fetch all recent and sync
scout sync --fetch-all --verbose

# Fetch last 5 and sync
scout sync --fetch-last 5

# Fetch last 10 of "Tests" workflow
scout sync --fetch-last 10 --filter-workflow "Tests"
```

**Specific Case:**

```bash
# Process single run/job
scout sync --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Using alternative identifiers
scout sync --workflow-name "Anvil Tests" --execution-number "21" --action-name "code quality"
```

**Conditional Execution (Skip Flags):**

```bash
# Use cached data (skip fetch)
scout sync --fetch-last 5 --skip-fetch

# Fetch but skip saving raw logs
scout sync --fetch-last 5 --skip-save-ci

# Fetch and save but skip parsing
scout sync --fetch-last 5 --skip-parse

# Parse but skip saving analysis
scout sync --fetch-last 5 --skip-save-analysis

# Dry-run: Fetch only, no saving
scout sync --fetch-last 5 --skip-save-ci --skip-parse
```

**Complex Workflows:**

```bash
# Re-analyze existing data without fetching
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch --skip-save-ci

# Update analysis only (assuming raw logs already saved)
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch

# Process last 20 but don't save analysis (review mode)
scout sync --fetch-last 20 --skip-save-analysis
```

---

## Workflow Examples

### Example 1: Quick Sync of Recent Runs

You want to fetch and process the last 5 test runs:

```bash
scout sync --fetch-last 5 --workflow-name "Tests"
```

This will:
1. Fetch the last 5 executions of "Tests" workflow
2. Save raw logs to scout.db
3. Parse using Anvil
4. Save analysis to scout-analysis.db

### Example 2: Manual Two-Step Process

You want to fetch and save first, then parse later:

```bash
# Step 1: Fetch and save
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-ci

# Step 2: Parse later
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-analysis
```

### Example 3: File-Based Processing

You want to analyze logs from a file without database:

```bash
# Get logs from somewhere
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output test.log

# Analyze locally
scout parse --input test.log --output results.json

# Review results
cat results.json
```

### Example 4: Skip-Based Workflows

You have existing raw logs, just want to parse and update analysis:

```bash
# Process with skip-fetch (errors if data not in DB)
scout sync --workflow-name "Tests" --run-id 12345 --job-id "abc123" --skip-fetch
```

Or fetch new data but don't save raw logs (only want analysis):

```bash
scout sync --fetch-last 10 --skip-save-ci
```

---

## Parameter Standardization

All commands use consistent parameter naming:

| Concept | Parameter | Type | Examples |
|---------|-----------|------|----------|
| Workflow Name | `--workflow-name` | string | "Tests", "Anvil Tests", "CI" |
| Run ID | `--run-id` | integer | 12345, 99999 |
| Execution Number | `--execution-number` | string | "21", "5", "#21" |
| Job ID | `--job-id` | string | "abc123def456" |
| Action Name | `--action-name` | string | "code quality", "unit tests" |

### Key Principle

You can provide **either** a numeric ID **or** a human-readable name for execution and job:
- Execution: `--run-id 12345` OR `--execution-number "21"`
- Job: `--job-id "abc123"` OR `--action-name "code quality"`

Scout automatically stores both representations, so you can query with either one.

---

## Database Organization

Scout uses two databases:

### 1. Execution Database (scout.db)

Stores raw CI logs from the **fetch** stage:

```
execution_logs:
  - workflow_name
  - run_id / execution_number (paired)
  - job_id / action_name (paired)
  - raw_log_text
  - fetch_timestamp
```

### 2. Analysis Database (scout-analysis.db)

Stores parsed results from the **parse** stage:

```
analysis_results:
  - workflow_name
  - run_id / execution_number (paired)
  - job_id / action_name (paired)
  - parsed_json
  - analysis_timestamp
```

---

## Error Handling

Scout always shows errors - no silent failures:

- If `--skip-fetch` but data not in execution DB → Error message
- If input file not found → Error message
- If case not found in database → Error message
- If GitHub API fails → Shows error, doesn't silently fall back

---

## Tips & Best Practices

### Tip 1: Use Descriptive Mode

Add `--verbose` for detailed output:

```bash
scout sync --fetch-last 5 --verbose
```

### Tip 2: Quiet Mode for Scripting

Use `--quiet` to suppress non-error output:

```bash
scout sync --fetch-last 5 --quiet  # Only show errors
```

### Tip 3: Check Database Before Skip-Fetch

Before using `--skip-fetch`, verify data exists:

```bash
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch
# Will error if run 12345 not in scout.db
```

### Tip 4: Dry-Run with Skip Flags

Test without saving using skip flags:

```bash
scout sync --fetch-last 5 --skip-save-ci --skip-parse
# Just fetches, doesn't save anything
```

### Tip 5: Batch Processing

Process recent runs in batches:

```bash
scout sync --fetch-last 20 --workflow-name "Tests"
```

---

## Architecture Reference

For detailed architecture information, see [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md)

### Four-Stage Pipeline

```
Stage 1: Fetch
  ↓
Stage 2: Save-CI (save raw logs)
  ↓
Stage 3: Parse (transform via Anvil)
  ↓
Stage 4: Save-Analysis (save parsed results)
```

Each stage can be skipped with `--skip-*` flags in the `sync` command.

---

## Troubleshooting

### "Error: Input file not found"

Check the file path:
```bash
scout parse --input test.log  # File must exist
```

### "Error: Case not found in database"

When using `--skip-fetch`, the data must exist:
```bash
# First, ensure data is saved:
scout fetch --workflow-name "Tests" --run-id 12345 --save-ci

# Then, process without fetch:
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch
```

### "Which identifiers should I use?"

Use whatever you have available:
- Have run ID? Use `--run-id 12345`
- Have execution number? Use `--execution-number "21"`
- Scout stores and retrieves both automatically

### "Can I use stdin piping?"

Not yet - planned for future release. For now, save to file first:
```bash
scout fetch ... --output temp.log
scout parse --input temp.log
```

---

## Transitioning from Old CLI

### Old Style (Still Works But Deprecated)

```bash
scout fetch --workflow "Tests" --last 5 --output data.json
scout parse --input data.json
scout ci show --run-id 12345
```

### New Style (Recommended)

```bash
scout sync --fetch-last 5 --workflow-name "Tests"
scout ci show --run-id 12345
```

The old commands still work for backwards compatibility but show a deprecation warning.

---

## Getting Help

- `scout --help` - Overview of all commands
- `scout fetch --help` - fetch command details
- `scout parse --help` - parse command details
- `scout sync --help` - sync command details
- [SCOUT_ARCHITECTURE.md](./SCOUT_ARCHITECTURE.md) - Complete architecture reference
