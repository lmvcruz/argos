# Scout CLI Architecture - Complete Redesign

## Overview

Scout has four operational stages in a pipeline:

1. **Fetch** - Download CI logs from GitHub Actions
2. **Save-CI** - Store raw logs in Scout execution database
3. **Parse** - Transform logs via Anvil parsers to standardized format
4. **Save-Analysis** - Store parsed results in Scout analysis database

Each stage can run independently or as part of an integrated `sync` workflow.

## Case Identification

All Scout operations work with a **case**, identified by three components:

### Primary Identifiers (One Required from Each Pair)

**Execution Identifier:**
- `--run-id <ID>` - GitHub Actions run ID (numeric)
- `--execution-number <N>` - Human-readable execution number (e.g., "#21")

**Job Identifier:**
- `--job-id <ID>` - GitHub Actions job ID (numeric)
- `--action-name <NAME>` - Human-readable action name (e.g., "code quality")

### Required Identifier

- `--workflow-name <NAME>` - GitHub Actions workflow name (ALWAYS required)

### Complete Case Triple

A case is fully identified by: `(workflow_name, execution_id, job_id)`

Scout automatically stores and retrieves both representations:
- If you provide `--run-id`, Scout also stores/retrieves `--execution-number`
- If you provide `--execution-number`, Scout can query the mapping to get `--run-id`
- Same applies for `--job-id` ↔ `--action-name`

## Command Structure

### 1. `scout fetch` - Download CI Logs

Download raw CI logs from GitHub Actions.

**Modes:**

```bash
# Mode 1: Fetch and display only
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Mode 2: Fetch and save to file (skip DB)
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output logs.txt

# Mode 3: Fetch and save to execution database
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-ci
```

**Arguments:**

- `--workflow-name` (required) - Workflow name
- `--run-id` (optional) - GitHub run ID
- `--execution-number` (optional) - Execution number (alternative to --run-id)
- `--job-id` (optional) - GitHub job ID
- `--action-name` (optional) - Action name (alternative to --job-id)
- `--output <FILE>` (optional) - Save to text file instead of stdout
- `--save-ci` (optional) - Save raw logs to execution database

**Output:**
- stdout: Raw log text
- File: If `--output` specified
- Database: If `--save-ci` specified

**Errors:**
- Always show errors (never silently fail)

---

### 2. `scout parse` - Transform and Analyze Logs

Parse CI logs using Anvil parsers and optionally save results.

**Modes:**

```bash
# Mode 1: Parse from file and display
scout parse --input logs.txt

# Mode 2: Parse from file and save to file
scout parse --input logs.txt --output parsed.json

# Mode 3: Parse from file and save to analysis database
scout parse --input logs.txt --save-analysis

# Mode 4: Parse from execution database using case triple
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Mode 5: Parse from database and save to analysis database
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-analysis
```

**Arguments:**

- `--input <FILE>` (optional) - Input file with raw logs (for Mode 1-3)
- `--output <FILE>` (optional) - Output file for parsed results
- `--workflow-name <NAME>` (optional) - For database-sourced parse (Mode 4-5)
- `--run-id <ID>` (optional) - For database-sourced parse
- `--execution-number <N>` (optional) - Alternative to --run-id
- `--job-id <ID>` (optional) - For database-sourced parse
- `--action-name <NAME>` (optional) - Alternative to --job-id
- `--save-analysis` (optional) - Save parsed results to analysis database

**Output:**
- stdout: Parsed JSON
- File: If `--output` specified
- Database: If `--save-analysis` specified

**Error Handling:**
- Always show errors if case not found in database
- No silent fallback behavior

---

### 3. `scout sync` - Complete Pipeline (New!)

Run all four stages in sequence with flexible input modes.

**Modes:**

```bash
# Mode 1: Fetch all recent and sync
scout sync --fetch-all

# Mode 2: Fetch last N and sync
scout sync --fetch-last 10

# Mode 3: Fetch last N of specific workflow
scout sync --fetch-last 5 --workflow-name "Tests"

# Mode 4: Process specific case
scout sync --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Mode 5-8: Any of above with skip flags
scout sync --fetch-last 5 --skip-fetch      # Use cached data, skip fetch
scout sync --fetch-last 5 --skip-save-ci    # Fetch but don't save
scout sync --fetch-last 5 --skip-parse      # Fetch/save but don't parse
scout sync --fetch-last 5 --skip-save-analysis  # Parse but don't save analysis
```

**Arguments - Fetch Modes:**

- `--fetch-all` - Fetch all available executions (exclusive group)
- `--fetch-last <N>` - Fetch last N executions (exclusive group)
- `--workflow-name <NAME>` - Filter by workflow when using `--fetch-last`
- Case identifiers: `--run-id`, `--execution-number`, `--job-id`, `--action-name`

**Arguments - Skip Flags (All Optional):**

- `--skip-fetch` - Skip fetch stage (error if data not in execution DB)
- `--skip-save-ci` - Fetch but don't save to execution DB
- `--skip-parse` - Skip parse stage
- `--skip-save-analysis` - Parse but don't save to analysis DB

**Behavior:**

- Fetches oldest-first (chronological order)
- Each stage depends on previous stage completion
- `--skip-fetch` errors if case data not in execution DB
- Full error reporting at each stage
- Atomic transactions per case

**Output:**
- Stdout: Progress and summary per case
- Automatic organization in databases by workflow_name, run_id, job_id

---

## Parameter Standardization

All commands use consistent parameter names:

| Purpose | Flags | Type | Example |
|---------|-------|------|---------|
| Workflow | `--workflow-name` | string | "Tests", "Anvil Tests" |
| Execution ID | `--run-id` OR `--execution-number` | int / string | 12345 or "#21" |
| Job ID | `--job-id` OR `--action-name` | string | "abc123" or "code quality" |

**Implementation Rule:**
- Store both representations in database
- User can query with either
- Scout automatically populates both on retrieval

---

## Database Storage

### Execution Database (scout.db - execution_logs table)

Stores raw CI logs from fetch stage.

```
execution_logs:
  - workflow_name
  - run_id
  - execution_number (auto-populated from run_id)
  - job_id
  - action_name (auto-populated from job_id)
  - raw_log_text
  - fetch_timestamp
```

### Analysis Database (scout-analysis.db - analysis_results table)

Stores parsed results from parse stage.

```
analysis_results:
  - workflow_name
  - run_id
  - execution_number
  - job_id
  - action_name
  - parsed_json
  - analysis_timestamp
```

---

## Workflow Examples

### Example 1: Quick Analysis of Single Run

```bash
# Fetch, parse, and analyze in one command
scout sync --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Or manually with three steps:
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-ci
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-analysis
scout ci analyze --run-id 12345
```

### Example 2: Batch Process Recent Tests

```bash
# Fetch and process last 5 test runs
scout sync --fetch-last 5 --workflow-name "Tests"

# Skip upload if already have data
scout sync --fetch-last 5 --workflow-name "Tests" --skip-fetch
```

### Example 3: Fetch Without Storage

```bash
# Get logs without saving anywhere
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123"

# Save to file for manual inspection
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc123" --output logs.txt
```

### Example 4: Parse Already-Fetched Data

```bash
# Parse from file
scout parse --input logs.txt --output parsed.json

# Parse from database and save results
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc123" --save-analysis
```

### Example 5: Conditional Sync

```bash
# Fetch and parse, but skip saving parsed results (dry-run)
scout sync --fetch-last 5 --skip-save-analysis

# Fetch but skip saving raw logs (only want analysis)
scout sync --fetch-last 5 --skip-save-ci
```

---

## CLI Hierarchy

```
scout
├── fetch          [Download logs]
│   ├── --workflow-name (required)
│   ├── --run-id | --execution-number
│   ├── --job-id | --action-name
│   ├── --output [file]
│   └── --save-ci
│
├── parse          [Transform logs]
│   ├── --input [file] OR (--workflow-name + case identifiers)
│   ├── --output [file]
│   └── --save-analysis
│
├── sync           [Complete pipeline]
│   ├── --fetch-all | --fetch-last N
│   ├── --workflow-name [filter]
│   ├── --run-id | --execution-number
│   ├── --job-id | --action-name
│   ├── --skip-fetch
│   ├── --skip-save-ci
│   ├── --skip-parse
│   └── --skip-save-analysis
│
├── ci             [Existing commands]
│   ├── analyze
│   ├── logs
│   ├── fetch
│   ├── parse
│   ├── show
│   └── sync
│
└── [other existing commands]
    ├── trends
    ├── flaky
    ├── logs
    ├── analyze
    └── config
```

---

## Implementation Notes

### Edge Cases Handled

1. **Duplicate Prevention**: Check database for existing case before storing
2. **Atomic Operations**: Each case processes as a unit; partial failures reported
3. **Mapping Auto-Population**: When given run_id, automatically fetch and store execution_number
4. **Error Visibility**: All errors shown immediately (no silent skips)
5. **Chronological Order**: `--fetch-last` returns oldest-first for consistent processing

### Future Enhancements (Not Now)

- Stdin piping: `echo "..." | scout parse --input -`
- Timestamp-based queries
- Re-run job disambiguation
- Caching strategies
- Parallel processing

---

## Migration from Old CLI

### Old Style (Current)
```bash
scout fetch --workflow "Tests" --last 5 --output file.json
scout parse --input file.json --output parsed.json
scout ci show --run-id 12345
```

### New Style (Target)
```bash
scout sync --fetch-last 5 --workflow-name "Tests"
scout ci show --run-id 12345
```

Or with full control:
```bash
scout fetch --workflow-name "Tests" --run-id 12345 --save-ci
scout parse --workflow-name "Tests" --run-id 12345 --save-analysis
scout ci show --run-id 12345
```
