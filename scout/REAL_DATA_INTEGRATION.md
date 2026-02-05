# Scout Real CI Data Integration - Complete

Scout now fetches **real data from GitHub Actions** CI/CD pipeline.

## Configuration

Credentials are stored in `.env`:

```dotenv
GITHUB_TOKEN=github_pat_11AFIVP6I0MieJNDCGNhy7_...
GITHUB_REPO=lmvcruz/argos
```

The `scout` CLI automatically loads these when you run any command.

## Usage

### Fetch Latest Workflow Runs

```bash
scout sync --fetch-last 5 -v
```

This will:
1. **[1/4] Fetch**: Download the last 5 workflow runs from `lmvcruz/argos` GitHub Actions
2. **[2/4] Save-CI**: Store all raw logs in `scout.db` execution database
3. **[3/4] Parse**: Analyze the logs for test results and failures
4. **[4/4] Save-Analysis**: Store parsed analysis in `scout-analysis.db`

### Filter by Workflow

```bash
scout sync --fetch-last 10 --filter-workflow "Scout Tests" -v
```

Only processes the "Scout Tests" workflow.

### Skip Stages

```bash
# Skip fetching, use cached data
scout sync --skip-fetch -v

# Fetch but don't save
scout sync --skip-save-ci -v
```

## What Gets Fetched

The sync command fetches:
- ✅ **Workflow runs**: All runs from the repository
- ✅ **Jobs**: All jobs within each workflow run
- ✅ **Logs**: Complete log output for each job
- ✅ **Metadata**: Run ID, job ID, workflow name, timestamps

## Real Data Pipeline

1. **GitHub Actions API** →
2. **Raw Log Storage** (scout.db) →
3. **Log Parsing** (pattern matching) →
4. **Analysis Storage** (scout-analysis.db)

## Example Output

```
[sync] Starting complete pipeline...
[sync] Mode: Fetch last 1 executions
Starting sync pipeline...
[sync] Fetching from GitHub API: lmvcruz/argos
  [1/4] Fetch: Processing 16 executions...
  [2/4] Save-CI: 16 logs saved to database
  [3/4] Parse: Parsing 16 logs with Anvil...
    Scout Tests (run 21712457060):
      - Passed: X
      - Failed: Y
  [4/4] Save-Analysis: Saved 16 results to database

--- Sync Summary ---
Fetched: 16
Parsed: 16
Failed: 0
```

## Parser Format

The current parser looks for these test markers in logs:
- `[PASS]` - Passed test
- `[FAIL]` - Failed test

Real GitHub Actions logs use different formats (✓, ✗, error output, etc.), so you may need to customize the parser for your specific CI format.

## No More Mock Data ✅

- ✅ Mock data completely removed
- ✅ Real GitHub API integration complete
- ✅ Environment variables from .env
- ✅ Databases store only real CI data
- ✅ Full 4-stage pipeline operational
