# Scout Fetch Command - Real Data Only

The `scout fetch` command now works **exclusively with real CI data**. No more mock data.

## Usage

### Option 1: Pipe Real Logs from a File

```bash
cat github-actions-logs.txt | scout fetch \
  --workflow-name "api-tests" \
  --run-id 100 \
  --job-id 200 \
  --save-ci
```

### Option 2: Generate Logs and Pipe

```bash
# Example: Real logs from GitHub Actions
echo "[INFO] Starting tests
[PASS] test_login_flow
[PASS] test_dashboard_load
[FAIL] test_export_pdf: timeout
[INFO] Tests completed" | scout fetch \
  --workflow-name "frontend-tests" \
  --run-id 101 \
  --job-id 201 \
  --save-ci
```

### Option 3: Save to File First, Then Process

```bash
# Fetch and save to file
cat logs.txt | scout fetch \
  --workflow-name "api-tests" \
  --run-id 100 \
  --job-id 200 \
  --output saved-logs.txt

# Then parse
scout parse --input saved-logs.txt --save-analysis
```

## Arguments

- `--workflow-name`: Name of the GitHub Actions workflow (required)
- `--run-id` or `--execution-number`: Run identifier (at least one required)
- `--job-id` or `--action-name`: Job identifier (at least one required)
- `--output`: Optional file to save the raw logs
- `--save-ci`: Save to execution database (scout.db)
- `--verbose` / `-v`: Show detailed progress
- `--quiet` / `-q`: Suppress output

## Error Handling

If you run the fetch command without piping input:

```bash
$ scout fetch --workflow-name "api-tests" --run-id 100 --job-id 200
Error: No input data provided
Please pipe log data via stdin:
  cat log.txt | scout fetch --workflow-name ... --run-id ...

Or set GITHUB_TOKEN to fetch from GitHub Actions API
```

**Solution**: Always pipe real log data via stdin or use a file.

## Future: GitHub API Integration

When `GITHUB_TOKEN` is set, the fetch command will eventually support direct GitHub Actions API queries:

```bash
export GITHUB_TOKEN="ghp_xxxxx"
scout fetch --workflow-name "tests" --run-id 100 --job-id 200
```

This feature is coming in a future version.

## Complete Workflow Example

```bash
# Step 1: Fetch real logs and save to database
cat production-logs.txt | scout fetch \
  --workflow-name "production-tests" \
  --run-id 200 \
  --job-id 400 \
  --save-ci \
  -v

# Step 2: Parse the logs
scout parse \
  --workflow-name "production-tests" \
  --run-id 200 \
  --save-analysis \
  -v

# Step 3: View results with sync
scout sync -v
```

## Valid Log Format

The fetch command accepts logs with test markers:

```
[INFO] Starting job
[PASS] test_name - description
[FAIL] test_name - failure reason
[WARN] test_name - warning
[ERROR] test_name - error message
[INFO] Job completed
```

Any log format works, but the parse command specifically looks for `[PASS]` and `[FAIL]` markers to extract statistics.
