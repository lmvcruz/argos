# Scout v2 Quick Reference Guide

## Command Summary

### Fetch Command
**Purpose**: Download CI logs from GitHub Actions or mock data

```bash
# Basic usage
scout fetch --workflow-name "Tests" --run-id 12345 --job-id 67890

# With output file
scout fetch --workflow-name "Tests" --run-id 12345 --job-id 67890 --output raw.log

# Save to database
scout fetch --workflow-name "Tests" --run-id 12345 --job-id 67890 --save-ci

# With alternate identifiers
scout fetch --workflow-name "Tests" --execution-number 21 --action-name "test-suite"
```

**Options**:
- `--workflow-name` (required): Name of the workflow
- `--run-id` OR `--execution-number`: Case identifier
- `--job-id` OR `--action-name`: Job identifier
- `--output`: Save to file
- `--save-ci`: Save to database
- `--ci-db`: Database path (default: scout.db)
- `--verbose/-v`: Verbose output
- `--quiet/-q`: Suppress output

### Parse Command
**Purpose**: Parse logs and extract test results

```bash
# From file
scout parse --input raw.log --output parsed.json

# From file to database
scout parse --input raw.log --save-analysis

# From database
scout parse --workflow-name "Tests" --run-id 12345

# Preview
scout parse --input raw.log
```

**Options**:
- `--input` OR `--workflow-name`: Input source (mutually exclusive)
- `--run-id` OR `--execution-number`: For database queries
- `--job-id` OR `--action-name`: For database queries
- `--output`: Save to JSON file
- `--save-analysis`: Save to database
- `--ci-db`: Execution database (default: scout.db)
- `--analysis-db`: Analysis database (default: scout-analysis.db)
- `--verbose/-v`: Verbose output
- `--quiet/-q`: Suppress output

### Sync Command
**Purpose**: Orchestrate complete fetch→parse→save pipeline

```bash
# Process specific workflow
scout sync --workflow-name "Tests" --run-id 12345

# Fetch and process last 10 runs
scout sync --fetch-last 10

# Fetch and process last 10 tests runs
scout sync --fetch-last 10 --filter-workflow "integration-tests"

# Parse cached data (skip fetch)
scout sync --fetch-last 10 --skip-fetch

# Fetch only (skip parse)
scout sync --fetch-last 10 --skip-parse

# Parse but don't save results
scout sync --fetch-last 10 --skip-save-analysis
```

**Options**:
- `--fetch-all`: Fetch all available runs
- `--fetch-last N`: Fetch last N runs
- `--workflow-name`: Process specific workflow
- `--filter-workflow`: Filter for --fetch-last
- `--skip-fetch`: Skip fetch stage
- `--skip-save-ci`: Skip saving raw logs
- `--skip-parse`: Skip parse stage
- `--skip-save-analysis`: Skip saving results
- `--ci-db`: Execution database (default: scout.db)
- `--analysis-db`: Analysis database (default: scout-analysis.db)

## Pipeline Stages

```
Stage 1: FETCH
├─ Download logs from GitHub
├─ Output: Raw log text
└─ Storage: scout.db (ExecutionLog)

Stage 2: PARSE
├─ Transform logs
├─ Extract pass/fail counts
└─ Storage: scout-analysis.db (AnalysisResult)

Stage 3: SYNC
├─ Orchestrate stages 1-2
├─ Process batches
└─ Track statistics
```

## Databases

### scout.db (ExecutionLog)
Stores raw CI logs with metadata:
- workflow_name: Name of the workflow
- run_id: GitHub Actions run ID
- job_id: GitHub Actions job ID
- raw_content: Raw log text
- stored_at: Storage timestamp

### scout-analysis.db (AnalysisResult)
Stores parsed analysis results:
- workflow_name: Name of the workflow
- run_id: GitHub Actions run ID
- job_id: GitHub Actions job ID
- parsed_data: JSON with test results
- parsed_at: Analysis timestamp

## Parsing Logic

Current implementation uses pattern matching:
- `[PASS]` markers identify passed tests
- `[FAIL]` markers identify failed tests

Output structure:
```json
{
  "workflow_name": "Tests",
  "run_id": 12345,
  "summary": {
    "total_items": 10,
    "passed": 8,
    "failed": 2
  },
  "results": {
    "passed_tests": 8,
    "failed_tests": 2,
    "failures": [
      "[FAIL] test_feature_x failed",
      "[FAIL] test_feature_y failed"
    ]
  }
}
```

## Environment Variables

- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_REPO`: Repository in owner/repo format

## Example Workflows

### Daily Testing Pipeline
```bash
# Fetch last 50 test runs
scout sync --fetch-last 50

# Parse with results saved
# Generates: scout.db, scout-analysis.db
```

### Manual Log Analysis
```bash
# Step 1: Get the raw log
scout fetch --workflow-name "CI" --run-id 12345 --job-id 67890 --output raw.log

# Step 2: Parse and save
scout parse --input raw.log --output results.json --save-analysis

# Step 3: Review
cat results.json | jq '.summary'
```

### Batch Reprocessing
```bash
# Skip fetch, reparse with new rules
scout sync --fetch-last 100 --skip-fetch

# This uses cached data from scout.db
```

## Troubleshooting

### Parse fails with file not found
```bash
# Verify file exists
ls -l raw.log

# Check path is correct
scout parse --input ./logs/raw.log
```

### Database locked error
```bash
# Close other connections
# Remove *.db-journal files
rm scout.db-journal scout-analysis.db-journal

# Retry command
```

### No logs found in database
```bash
# Verify fetch saved to database
scout fetch --save-ci

# Check database
sqlite3 scout.db "SELECT COUNT(*) FROM execution_logs;"
```

## Performance Tips

1. **Use --skip-fetch** to reparse cached logs
2. **Use --fetch-last N** instead of --fetch-all for large datasets
3. **Use --skip-save-* to avoid I/O** when previewing
4. **Use --quiet mode** in scripts to reduce overhead

## Integration Points

- **GitHub API**: Will replace mock in fetch command
- **Anvil Parsers**: Will replace pattern matching in parse command
- **Reporting**: Can consume AnalysisResult table
- **Dashboards**: Can query both databases

## Testing

### Run Integration Tests
```bash
python test_integration.py
```

### Run End-to-End Tests
```bash
python test_e2e.py
```

### Run Unit Tests
```bash
pytest tests/test_cli_handlers.py -v
```

## Documentation

- `docs/SCOUT_V2_IMPLEMENTATION.md` - Detailed implementation
- `docs/SCOUT_V2_COMPLETE_SUMMARY.md` - Complete summary
- `docs/IMPLEMENTATION_CHECKLIST.md` - Checklist of features
