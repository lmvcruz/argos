# Scout CI Inspection - Current Status Analysis

## Date: February 10, 2026

## Overview of Current Functionality

### ✅ What IS Working

#### 1. Log Fetching from Remote CI
**Status: FULLY FUNCTIONAL**

- Logs can be successfully fetched from GitHub Actions using the backend endpoint
- Command: `POST /api/scout/fetch-log/{run_id}`
- Backend calls: `python -m scout fetch --repo lmvcruz/argos --run-id {run_id}`
- **Data Storage**: Logs are stored in **Scout SQLite database**
  - **Location**: `~/.scout/lmvcruz/argos/scout.db`
  - **Table**: `execution_logs`
  - **Fields**:
    - `id` (INTEGER)
    - `workflow_name` (VARCHAR)
    - `run_id` (BIGINT)
    - `execution_number` (INTEGER)
    - `job_id` (BIGINT) - Foreign key to workflow_jobs
    - `action_name` (VARCHAR)
    - **`raw_content` (TEXT)** - The actual log content
    - `content_type` (VARCHAR) - e.g., 'github_actions'
    - `stored_at` (DATETIME)
    - `parsed` (INTEGER) - Flag for parsing status
    - `extra_metadata` (JSON)

**Verified Data:**
- Database has 115 execution logs with content
- Sample log sizes: 100KB-600KB per job
- Recent fetches:
  - Run 21786230446: 17 jobs fetched, all have `has_logs=1`
  - Run 21786230460: 16 jobs fetched, all have `has_logs=1`

#### 2. Log Display Endpoint
**Status: FULLY FUNCTIONAL**

- Endpoint: `GET /api/scout/show-log/{run_id}`
- **Returns**: Complete log data including:
  - Workflow name
  - All jobs for the run
  - For each job:
    - `job_id`, `job_name`
    - `status`, `conclusion`
    - `has_raw_log`: Boolean flag
    - **`raw_log`**: Full log content from `execution_logs.raw_content`
    - Test summary data

**Tested:**
```
Run 21786230446:
  ✓ Returns 17 jobs
  ✓ Each job has has_raw_log=True
  ✓ Log content lengths: 27KB-597KB
  ✓ HTTP 200 OK response
```

### ❌ What is NOT Working

#### 1. Frontend Display Issue
**Status: BUG CONFIRMED - Frontend Issue**

**Problem**: Previously fetched executions do not display log content after page refresh

**Evidence**:
1. Backend endpoint `/api/scout/show-log/{run_id}` **returns data correctly** (verified)
2. Database **contains log content** (verified)
3. Logs successfully retrieved and stored during fetch (verified)

**Root Cause**: Frontend not properly loading or displaying the data from show-log endpoint

**Investigation Needed**:
1. Check if frontend calls `/api/scout/show-log/{run_id}` when viewing an execution
2. Check if `CIInspection.tsx` properly extracts `raw_log` from response
3. Check if `LogViewer` component receives and displays the data
4. Check browser Network tab to see actual API calls and responses

**Database Flags**:
- `workflow_runs.has_logs` = 1 (set correctly)
- `workflow_runs.logs_downloaded_at` = timestamp (set correctly)
- `workflow_jobs.has_logs` = 1 (set correctly)
- `execution_logs.raw_content` = populated (confirmed)

#### 2. Parse Functionality
**Status: NOT IMPLEMENTED**

**Issue**: Parse command is NOT registered in Scout CLI

**What Exists**:
- ✅ `scout/cli/parse_commands.py` file with handlers:
  - `handle_parse_from_file_command()` - Parse logs from a file
  - `handle_parse_from_db_command()` - Parse logs from database
- ✅ Functions are imported in `scout/cli/__init__.py`
- ❌ **NOT registered in argument parser** in `scout/cli.py`

**Available Commands** (from `python -m scout --help`):
```
logs, analyze, trends, flaky, config, fetch, download, compare, patterns,
show, sync, anvil-compare, ci-failures, list, db-list, show-log, show-data
```

**Missing**: `parse` command

**What Can Be Done Manually**:
Currently, NO - you cannot manually parse logs using Scout CLI because:
1. The `parse` command is not registered in the CLI
2. The parse handlers exist but are not accessible via command line
3. The `show-data` command exists for viewing **already parsed** data, but there's no way to parse data first

## Database Structure Summary

### Scout Database Location
```
~/.scout/lmvcruz/argos/scout.db
```

### Key Tables

#### workflow_runs
- Stores CI workflow run metadata
- `run_id` (BIGINT, PRIMARY KEY)
- `has_logs` (INTEGER) - Flag indicating logs are downloaded
- `logs_downloaded_at` (DATETIME) - When logs were fetched

#### workflow_jobs
- Stores individual job information
- `job_id` (BIGINT, PRIMARY KEY)
- `run_id` (BIGINT, FOREIGN KEY)
- `job_name` (VARCHAR)
- `has_logs` (INTEGER) - Flag indicating logs are available

#### execution_logs
- Stores the actual raw log content
- `job_id` (BIGINT, FOREIGN KEY to workflow_jobs)
- `raw_content` (TEXT) - **THE ACTUAL LOG DATA**
- `content_type` (VARCHAR)
- `stored_at` (DATETIME)
- `parsed` (INTEGER) - Flag for parsing status

## Recommendations

### Fix #1: Frontend Display Issue (HIGH PRIORITY)
**Action**: Debug `CIInspection.tsx` to fix log display

1. Add browser console logging to track API calls
2. Verify `/api/scout/show-log/{run_id}` is called when viewing execution
3. Check response parsing in component
4. Verify `raw_log` data is passed to `LogViewer` component

### Fix #2: Implement Parse Command (MEDIUM PRIORITY)
**Action**: Register parse command in Scout CLI

1. Open `scout/scout/cli.py`
2. Find the subparsers section (around line 538)
3. Add parse command parser:
```python
parse_parser = subparsers.add_parser(
    "parse",
    help="Parse CI logs using Anvil validators",
    parents=[ci_parent],
)
parse_parser.add_argument("--input", help="Input file path")
parse_parser.add_argument("--output", help="Output file path")
parse_parser.add_argument("--save", action="store_true", help="Save to DB")
parse_parser.add_argument("--repo", help="Repository (owner/repo)")
parse_parser.add_argument("--run-id", type=int, help="Run ID")
```

4. Add command handler in main() function (around line 1046):
```python
elif args.command == "parse":
    from scout.cli.parse_commands import handle_parse_from_db_command, handle_parse_from_file_command
    if args.input:
        return handle_parse_from_file_command(args)
    else:
        return handle_parse_from_db_command(args)
```

5. Implement the actual Anvil parser integration in the handlers (currently TODO)

### Fix #3: Backend Parse Endpoint (LOW PRIORITY)
**Status**: Already returns proper 501 error with clear message
**Action**: Once Scout parse command is implemented, remove the 501 error and call the actual command

## Test Results

### Database Verification
```bash
$ python check_scout_db.py

Database path: C:\Users\l-cruz\.scout\lmvcruz\argos\scout.db
Database exists: True

Tables: ['workflow_runs', 'ci_failure_patterns', 'execution_logs',
         'analysis_results', 'workflow_jobs', 'workflow_test_results']

ExecutionLog: Total rows: 115, With content: 115
```

### Show-Log Endpoint Test
```bash
$ python test_showlog_endpoint.py

Testing show-log endpoint for run_id=21786230446
Status code: 200
Workflow: Anvil Tests
Total jobs: 17

Job: quality (ID: 62858077988)
  Status: completed / failure
  Has raw log: True
  Raw log length: 183359 characters

Job: lint (ID: 62858077995)
  Status: completed / success
  Has raw log: True
  Raw log length: 27210 characters

Job: coverage (ID: 62858077997)
  Status: completed / failure
  Has raw log: True
  Raw log length: 597732 characters
```

## Conclusion

**The backend and database are working correctly.** Logs are being fetched, stored with full content in the database, and the API endpoint returns the data properly.

**The issue is in the frontend** - the UI is not correctly loading or displaying the log data that is available from the backend.

**The parse functionality** doesn't exist as a CLI command yet, but the infrastructure (handlers and database schema) is in place to implement it.
