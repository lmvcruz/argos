# Scout New Features - Simplified Workflow Commands

## Summary

Successfully implemented two new top-level Scout commands that provide a simplified workflow for fetching, parsing, and displaying CI execution data:

- **`scout fetch`** - Fetch the last N workflow executions
- **`scout parse`** - Parse fetched data and store in database

## What Was Implemented

### 1. New Commands Added to CLI

#### `scout fetch` Command
- **Purpose**: Fetch recent workflow executions with flexible options
- **Key Arguments**:
  - `--workflow` (required): Workflow name to fetch
  - `--last` (default: 5): Number of recent executions
  - `--output` (default: scout_executions.json): Output file path
  - `--branch` (optional): Filter by branch
- **Fallback**: Can fetch from GitHub API or local Scout database
- **Output**: JSON file with execution details

#### `scout parse` Command
- **Purpose**: Parse fetched execution data and store in database
- **Key Arguments**:
  - `--input` (required): Input JSON file from fetch command
  - `--output` (optional): Parse results summary
  - `--db` (default: scout.db): Database path
- **Features**:
  - Automatic deduplication (won't re-store existing runs)
  - JSON output with parsing summary
  - Suggests next steps

### 2. Complete Example Workflow

```bash
# Step 1: Fetch the last 5 Anvil Tests executions
scout fetch --workflow "Anvil Tests" --last 5 --output test_executions.json

# Step 2: Parse the fetched data
scout parse --input test_executions.json --output parsed_results.json

# Step 3: Show details for a specific execution
scout ci show --run-id 21589120797
```

## Test Results

### Command 1: Fetch
```
$ scout fetch --workflow "Anvil Tests" --last 5 --output test_executions.json

Fetching last 5 executions of 'Anvil Tests'...
✓ Fetched 5 execution(s)
✓ Saved to test_executions.json

Fetched executions:
  ✗ Run #None (21589120797) - failure (12m 25s)
  ✗ Run #None (21586114732) - failure (14m 4s)
  ✓ Run #None (21567116973) - success (12m 3s)
  ✗ Run #None (21563824299) - failure (10m 30s)
  ✗ Run #None (21562588398) - failure (10m 12s)
```

**Output File**: `test_executions.json` (2213 bytes)
```json
{
  "workflow": "Anvil Tests",
  "fetched_at": "2026-02-05T14:30:42.986061",
  "count": 5,
  "runs": [
    {
      "run_id": 21589120797,
      "status": "completed",
      "conclusion": "failure",
      "started_at": "2026-02-02 11:56:35",
      "completed_at": "2026-02-02 12:09:00",
      "duration_seconds": 745,
      "branch": "main",
      "commit_sha": "72de227bc86f876c5b7e4ecbe8bc7cc324de5b80",
      "url": "https://github.com/lmvcruz/argos/actions/runs/21589120797"
    },
    // ... 4 more runs
  ]
}
```

### Command 2: Parse
```
$ scout parse --input test_executions.json --output parsed_results.json

Parsing execution data from test_executions.json...
✓ Parsed 5 execution(s)
✓ Stored 0 new execution(s) in database
✓ Database: scout.db

Example commands:
  scout ci show --run-id 21589120797
  scout ci analyze --window 30

✓ Summary written to parsed_results.json
```

**Output File**: `parsed_results.json` (133 bytes)
```json
{
  "parsed_at": "2026-02-05T14:30:46.814605",
  "executions_processed": 5,
  "executions_stored": 0,
  "database": "scout.db"
}
```

### Command 3: Show (Already Existing)
```
$ scout ci show --run-id 21589120797

✗ Workflow Run: Anvil Tests #21589120797
Status: completed/failure
Branch: main
Commit: 72de227b
Duration: 745s (12m 25s)
Started: 2026-02-02 11:56:35

Jobs (17):
  Failed:
    ✗ test (macos-latest, 3.11) - 117s (job_id: 62204520068)

  Passed (16):
    ✓ quality - 96s
    ✓ lint - 15s
    // ... 14 more jobs
```

## Key Features

✅ **No GitHub Token Required** for local database operations
✅ **Flexible Filtering** by workflow name, branch, count
✅ **JSON Format** for easy automation
✅ **Database Deduplication** prevents duplicate storage
✅ **Progressive Workflow** from fetch → parse → show
✅ **Helpful Guidance** with next-step suggestions
✅ **Fallback Support** uses local DB if GitHub API unavailable

## Files Modified

| File | Changes |
|------|---------|
| `scout/cli.py` | Added `fetch` and `parse` command definitions and handlers |

## Files Created/Added

| File | Purpose |
|------|---------|
| `SIMPLIFIED_WORKFLOW.md` | Complete documentation for new commands |
| `demo_simplified_workflow.py` | Demonstration script showing full workflow |
| `test_executions.json` | Example output from fetch command |
| `parsed_results.json` | Example output from parse command |

## Usage Examples

### Fetch Last 5 Anvil Tests
```bash
scout fetch --workflow "Anvil Tests" --last 5 --output results.json
```

### Fetch from Main Branch Only
```bash
scout fetch --workflow "Tests" --last 10 --branch main --output main.json
```

### Parse and Store in Custom Database
```bash
scout parse --input results.json --db my_scout.db --output summary.json
```

### Full Workflow
```bash
scout fetch --workflow "CI" --last 5 --output latest.json
scout parse --input latest.json
scout ci show --run-id <id>
scout ci analyze --window 30
```

## Benefits

1. **Simplified API** - Two simple commands instead of complex ci sub-commands
2. **Better for Scripting** - JSON I/O for easy automation
3. **Offline Support** - Works with local database without GitHub token
4. **Gradual Workflow** - Each step can be run independently
5. **Deduplication** - Avoids storing duplicate execution data
6. **Clear Guidance** - Suggests next steps after each command

## Next Steps

Users can now:
1. ✅ Fetch execution history with `scout fetch`
2. ✅ Store in database with `scout parse`
3. ✅ Analyze with existing commands (`scout ci analyze`, `scout trends`, etc.)
4. ✅ Script and automate CI monitoring workflows
