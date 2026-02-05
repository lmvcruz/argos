# Scout Simplified Workflow Commands

## Overview

Scout now includes simplified **`fetch`** and **`parse`** commands that provide an easier workflow for fetching and analyzing CI executions without requiring GitHub credentials for local database operations.

## New Commands

### 1. `scout fetch` - Fetch Recent Executions

Fetch the last N executions from a workflow and export them to a JSON file.

#### Usage

```bash
scout fetch --workflow "Workflow Name" --last N --output file.json [--branch BRANCH]
```

#### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--workflow` | string | Required | Workflow name to fetch |
| `--last` | int | 5 | Number of recent executions to fetch |
| `--output` | string | scout_executions.json | Output file for fetched data |
| `--branch` | string | Optional | Filter by branch name |
| `--token` | string | Optional | GitHub token (uses GITHUB_TOKEN env if not provided) |
| `--repo` | string | Optional | Repository in owner/repo format |
| `--verbose` | flag | False | Enable verbose output |
| `--quiet` | flag | False | Suppress non-error output |

#### Examples

```bash
# Fetch last 5 Anvil Tests executions
scout fetch --workflow "Anvil Tests" --last 5 --output test_runs.json

# Fetch last 10 from main branch
scout fetch --workflow "CI" --last 10 --branch main --output main_runs.json

# Fetch with GitHub API
scout fetch --workflow "Tests" --last 5 --token YOUR_TOKEN --repo owner/repo
```

#### Output

The command creates a JSON file with the following structure:

```json
{
  "workflow": "Anvil Tests",
  "fetched_at": "2026-02-05T14:30:42.986061",
  "count": 5,
  "runs": [
    {
      "run_id": 21589120797,
      "run_number": null,
      "status": "completed",
      "conclusion": "failure",
      "started_at": "2026-02-02 11:56:35",
      "completed_at": "2026-02-02 12:09:00",
      "duration_seconds": 745,
      "branch": "main",
      "commit_sha": "72de227bc86f876c5b7e4ecbe8bc7cc324de5b80",
      "url": "https://github.com/lmvcruz/argos/actions/runs/21589120797"
    }
    // ... more runs
  ]
}
```

### 2. `scout parse` - Parse Fetched Data

Parse fetched execution data and store it in the Scout database.

#### Usage

```bash
scout parse --input file.json [--output results.json] [--db scout.db]
```

#### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | string | Required | Input file with fetched execution data |
| `--output` | string | Optional | Output file for parsed results summary |
| `--db` | string | scout.db | Path to Scout database |
| `--token` | string | Optional | GitHub token (not required for local parsing) |
| `--repo` | string | Optional | Repository info (not required for local parsing) |
| `--verbose` | flag | False | Enable verbose output |
| `--quiet` | flag | False | Suppress non-error output |

#### Examples

```bash
# Parse fetched data
scout parse --input test_runs.json

# Parse with custom database and output
scout parse --input test_runs.json --db my_scout.db --output parse_results.json

# Parse silently
scout parse --input test_runs.json --quiet
```

#### Output

The command:
1. **Stores new runs in the database** (if not already present)
2. **Writes a summary JSON** with parsing results:

```json
{
  "parsed_at": "2026-02-05T14:30:46.814605",
  "executions_processed": 5,
  "executions_stored": 2,
  "database": "scout.db"
}
```

## Complete Workflow Example

### Step 1: Fetch Data

```bash
$ scout fetch --workflow "Anvil Tests" --last 5 --output anvil_runs.json

Fetching last 5 executions of 'Anvil Tests'...
✓ Fetched 5 execution(s)
✓ Saved to anvil_runs.json

Fetched executions:
  ✗ Run #None (21589120797)
      Status: failure | Started: 2026-02-02 11:56:35
  ✗ Run #None (21586114732)
      Status: failure | Started: 2026-02-02 10:17:37
  ✓ Run #None (21567116973)
      Status: success | Started: 2026-02-01 17:26:56
  ✗ Run #None (21563824299)
      Status: failure | Started: 2026-02-01 13:37:41
  ✗ Run #None (21562588398)
      Status: failure | Started: 2026-02-01 12:07:24

Next step: scout parse --input anvil_runs.json
```

### Step 2: Parse Data

```bash
$ scout parse --input anvil_runs.json --output parse_summary.json

Parsing execution data from anvil_runs.json...
✓ Parsed 5 execution(s)
✓ Stored 0 new execution(s) in database
✓ Database: scout.db

Example commands:
  scout ci show --run-id 21589120797
  scout ci analyze --window 30

✓ Summary written to parse_summary.json
```

### Step 3: Show Execution Details

```bash
$ scout ci show --run-id 21589120797

✗ Workflow Run: Anvil Tests #21589120797
Status: completed/failure
Branch: main
Commit: 72de227b
Duration: 745s (12m 25s)
Started: 2026-02-02 11:56:35
URL: https://github.com/lmvcruz/argos/actions/runs/21589120797

Jobs (17):

  Failed:
    ✗ test (macos-latest, 3.11) - 117s (job_id: 62204520068)

  Passed (16):
    ✓ quality - 96s (job_id: 62204519980)
    ✓ lint - 15s (job_id: 62204520007)
    // ... more jobs
```

## Key Features

✅ **No GitHub Token Required** - Works with local Scout database
✅ **Flexible Filtering** - Fetch by workflow name, branch, or count
✅ **JSON Format** - Easy to automate and integrate
✅ **Database Deduplication** - Only stores new runs
✅ **Next Steps Guidance** - CLI suggests follow-up commands
✅ **Summary Reports** - JSON output for parsing results

## Use Cases

### 1. Regular CI Monitoring

```bash
# Daily monitoring of CI executions
scout fetch --workflow "Tests" --last 10 --output $(date +%Y-%m-%d).json
scout parse --input $(date +%Y-%m-%d).json
```

### 2. Historical Analysis

```bash
# Collect runs over time
for workflow in "Build" "Test" "Deploy"; do
  scout fetch --workflow "$workflow" --last 20 --output ${workflow}_runs.json
  scout parse --input ${workflow}_runs.json
done

# Later, analyze trends
scout ci analyze --window 30
```

### 3. Post-Mortem Analysis

```bash
# When a failure occurs
scout fetch --workflow "CI" --last 5 --output incident.json
scout parse --input incident.json --output incident_analysis.json
scout ci show --run-id <run_id>
```

## Related Commands

After fetching and parsing, use these commands for deeper analysis:

```bash
# Show details of a specific run
scout ci show --run-id <run_id>

# Show details of a specific job
scout ci show --job-id <job_id> --run-id <run_id>

# Analyze failure patterns
scout ci analyze --window 30

# Detect flaky tests
scout flaky --threshold 0.2

# View trends
scout trends CI
```

## Integration with CI/CD

The commands can be integrated into scripts for automated monitoring:

```bash
#!/bin/bash

# Weekly CI health check
scout fetch --workflow "Integration Tests" --last 50 --output weekly_report.json
scout parse --input weekly_report.json --output summary.json

if [ -f summary.json ]; then
  cat summary.json
  # Send report via email, Slack, etc.
fi
```
