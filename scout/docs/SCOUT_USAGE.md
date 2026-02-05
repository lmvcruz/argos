# Scout CLI Usage Guide

Scout implements a **four-stage pipeline** for CI/CD data management:

1. **Fetch** - Download CI logs from GitHub Actions
2. **Save-CI** - Persist raw logs in Scout execution database
3. **Parse** - Transform logs using Anvil parsers
4. **Save-Analysis** - Store parsed results in Scout analysis database

Each stage can run **individually** or together via **sync**. Stages can be **skipped** independently.

---

## Case Identification

A **case** is uniquely identified by a **triple**:

```
(workflow_name, execution_id, job_id)

Where:
- execution_id = run_id (GitHub) OR execution_number (internal, linked)
- job_id = job_id (GitHub) OR action_name (user-friendly, linked)
```

**Scout automatically stores both identifiers**, so you can query using either:

```bash
# Using run_id
scout fetch --workflow-name "CI Tests" --run-id 123456789 --job-id abc123def

# Using execution number (if known)
scout fetch --workflow-name "CI Tests" --execution-number 42 --action-name "Python 3.10"

# Mixed combinations
scout fetch --workflow-name "CI Tests" --run-id 123456789 --action-name "Python 3.10"
```

---

## FETCH Command

Download CI logs from GitHub Actions.

### Fetch a Single Execution

Fetch a specific workflow run and job:

```bash
# Display to stdout
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def

# Save to file
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --output raw_logs.txt

# Save to execution database
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --save
```

### Fetch All Executions

Fetch all available runs from a workflow:

```bash
scout fetch --fetch-all \
  --workflow-name "CI Tests" \
  --save
```

### Fetch Last N Executions

Fetch the last N executions (sorted oldest-first):

```bash
# Last 10 executions from any workflow
scout fetch --fetch-last 10 --save

# Last 5 executions from specific workflow
scout fetch --fetch-last 5 \
  --workflow-name "CI Tests" \
  --save
```

---

## PARSE Command

Parse CI logs using Anvil parsers (supports: pytest, flake8, black, isort, pylint, coverage).

### Parse from File

Parse raw logs stored in a file:

```bash
# Display parsed results to stdout
scout parse --input raw_logs.txt

# Save parsed results to file
scout parse --input raw_logs.txt --output parsed_results.json

# Save to analysis database
scout parse --input raw_logs.txt --save
```

### Parse from Database

Parse logs already stored in execution database:

```bash
# Display parsed results
scout parse \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def

# Save to analysis database
scout parse \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --save
```

---

## SYNC Command

Run the complete four-stage pipeline with skip options.

### Sync a Single Execution

Fetch, parse, and save a specific execution:

```bash
scout sync \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def
```

All four stages run: fetch → save-ci → parse → save-analysis

### Sync with Skip Options

Run pipeline but skip certain stages:

```bash
# Fetch and save, but don't parse
scout sync \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --skip-parse

# Parse already-fetched data without saving raw logs
scout sync \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --skip-save-ci

# Use cached data (error if not found)
scout sync \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --skip-fetch

# Fetch and parse, but don't save to databases
scout sync \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --job-id abc123def \
  --skip-save-ci \
  --skip-save-analysis
```

### Sync All Executions

Process all executions through pipeline:

```bash
scout sync --fetch-all \
  --workflow-name "CI Tests"
```

### Sync Last N Executions

Process the last N executions (sorted oldest-first):

```bash
# Last 10 executions from any workflow
scout sync --fetch-last 10

# Last 5 from specific workflow
scout sync --fetch-last 5 \
  --workflow-name "CI Tests"
```

---

## Common Options

All commands support:

```bash
--verbose, -v              # Enable verbose output
--quiet, -q                # Suppress non-error output
--token TOKEN              # GitHub PAT (or use GITHUB_TOKEN env var)
--repo OWNER/REPO          # GitHub repo (or use GITHUB_REPO env var)
--db PATH                  # Scout database path (default: scout.db)
```

---

## Usage Examples

### Example 1: Quick CI Log Download

Download and display a job's logs:

```bash
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 1234567890 \
  --job-id 9876543210
```

### Example 2: Cache Logs for Later Analysis

Fetch and store logs, parse later:

```bash
# Stage 1: Fetch and cache
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 1234567890 \
  --job-id 9876543210 \
  --save

# Stage 2: Parse cached logs (hours later)
scout parse \
  --workflow-name "CI Tests" \
  --run-id 1234567890 \
  --job-id 9876543210 \
  --save
```

### Example 3: Full Pipeline with Selective Save

Fetch from GitHub, parse, but only save results (not raw logs):

```bash
scout sync \
  --workflow-name "CI Tests" \
  --run-id 1234567890 \
  --job-id 9876543210 \
  --skip-save-ci
```

### Example 4: Batch Process Recent Executions

Process last 5 runs through complete pipeline:

```bash
scout sync --fetch-last 5 \
  --workflow-name "Code Quality" \
  --verbose
```

### Example 5: Parse Multiple Log Files

Convert raw logs to Anvil format:

```bash
# File 1
scout parse --input job1_logs.txt --output job1_parsed.json

# File 2
scout parse --input job2_logs.txt --output job2_parsed.json

# Batch process with script
for log in *.log; do
  scout parse --input "$log" --output "${log%.log}.json"
done
```

---

## Data Recovery by Triple

Scout ensures all related identifiers are stored together. Recover any execution by knowing:

**Minimum required:**
- workflow_name
- (run_id OR execution_number)
- (job_id OR action_name)

```bash
# All of these retrieve the same execution:
scout parse --workflow-name "CI Tests" --run-id 123456 --job-id abc123
scout parse --workflow-name "CI Tests" --execution-number 42 --job-id abc123
scout parse --workflow-name "CI Tests" --run-id 123456 --action-name "Python 3.10"
scout parse --workflow-name "CI Tests" --execution-number 42 --action-name "Python 3.10"
```

---

## Database Schema

### Execution Database (`scout.db`)

**ExecutionLog** - Raw logs stored by fetch stage
```
- workflow_name
- run_id
- execution_number (linked)
- job_id
- action_name (linked)
- raw_content
- stored_at
```

### Analysis Database (same `scout.db`)

**AnalysisResult** - Parsed results stored by save-analysis stage
```
- workflow_name
- run_id
- execution_number (linked)
- job_id
- action_name (linked)
- analysis_type (pytest, flake8, etc.)
- parsed_data (JSON)
- parsed_at
```

---

## Error Handling

**Skip-fetch without cached data:** Error
```bash
scout sync --skip-fetch ... # ✗ Error: No cached data found
```

**Conflicting identifiers:** Error
```bash
scout fetch \
  --workflow-name "CI Tests" \
  --run-id 123456789 \
  --execution-number 999 # ✗ Error: Conflicting execution IDs
```

**Missing triple components:** Error
```bash
scout fetch --workflow-name "CI Tests" # ✗ Error: Missing execution and job IDs
```

---

## Configuration

Set defaults in `~/.scout/config.json`:

```json
{
  "github": {
    "token": "ghp_...",
    "repo": "owner/repo"
  },
  "database": {
    "path": "scout.db"
  }
}
```

Override with CLI arguments:

```bash
scout fetch ... --token ghp_xyz --repo user/repo --db /custom/path.db
```

---

## Future Enhancements

- [ ] Stdin piping: `echo "logs" | scout parse --input -`
- [ ] Advanced filtering: `--filter "failed tests"`
- [ ] Visualization: `scout report --format html`
- [ ] Incremental sync: `--since <timestamp>`
- [ ] Webhook integration: `scout serve --listen 0.0.0.0:8080`
