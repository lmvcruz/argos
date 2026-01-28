# Test Failure Analysis Scripts

This directory contains scripts to help analyze test failures from both local runs and GitHub Actions.

## Scripts

### 1. `get-gh-action-logs.py`

Fetch and parse GitHub Actions logs for failed tests.

**Requirements:**
```bash
pip install requests
```

**Usage:**
```bash
# Fetch latest workflow run (no auth - rate limited)
python scripts/get-gh-action-logs.py

# With GitHub token (recommended for higher rate limits)
export GITHUB_TOKEN="ghp_your_token_here"
python scripts/get-gh-action-logs.py

# Fetch specific workflow
python scripts/get-gh-action-logs.py --workflow "Forge Tests"

# Fetch specific run by ID
python scripts/get-gh-action-logs.py --run-id 12345

# Show detailed failure context
python scripts/get-gh-action-logs.py --detailed

# Different repository
python scripts/get-gh-action-logs.py --owner username --repo reponame
```

**Features:**
- Fetches latest or specific GitHub Actions workflow run
- Extracts failed job logs
- Parses pytest failure information
- Shows clean summary of all failed tests
- Optional detailed failure context

**Getting a GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scope: `repo` (for private repos) or `public_repo` (for public repos)
4. Copy token and set as environment variable or pass via `--token`

---

### 2. `parse-test-failures.py`

Parse pytest output from local test runs or log files.

**Usage:**
```bash
# Parse from file
python scripts/parse-test-failures.py test-output.txt

# Pipe directly from pytest
pytest --tb=short 2>&1 | python scripts/parse-test-failures.py

# Save pytest output and parse later
pytest --tb=short > test-output.txt 2>&1
python scripts/parse-test-failures.py test-output.txt

# Show detailed failure context
python scripts/parse-test-failures.py --detailed test-output.txt

# Show only summary statistics
python scripts/parse-test-failures.py --summary-only test-output.txt
```

**Features:**
- Parses pytest output (FAILED and ERROR lines)
- Extracts test summary (passed/failed/skipped counts)
- Shows clean failure summaries
- Optional detailed failure context
- Works with piped input or files

---

## Example Workflows

### Check Latest GitHub Actions Failure

```bash
# Quick check of latest failure
python scripts/get-gh-action-logs.py --workflow "Forge Tests"

# Detailed analysis
export GITHUB_TOKEN="ghp_your_token"
python scripts/get-gh-action-logs.py --workflow "Forge Tests" --detailed
```

### Analyze Local Test Run

```bash
# Run tests and immediately parse failures
cd forge
pytest --tb=short 2>&1 | python ../scripts/parse-test-failures.py

# Or save for later analysis
pytest --tb=short > ../test-results.txt 2>&1
python ../scripts/parse-test-failures.py --detailed ../test-results.txt
```

### CI/CD Integration

Add to your workflow to save failure summaries:

```yaml
- name: Run tests
  run: pytest --tb=short 2>&1 | tee test-output.txt
  continue-on-error: true

- name: Parse failures
  if: failure()
  run: python scripts/parse-test-failures.py test-output.txt

- name: Upload failure report
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: test-failures
    path: test-output.txt
```

---

## Tips

### Rate Limits

GitHub API has rate limits:
- **Without token**: 60 requests/hour
- **With token**: 5000 requests/hour

Always use a token for frequent checks.

### Caching Logs

To avoid re-fetching logs, save them locally:

```bash
# Fetch and save
python scripts/get-gh-action-logs.py --run-id 12345 > failure-log.txt

# Parse saved log
python scripts/parse-test-failures.py failure-log.txt
```

### Combining Scripts

```bash
# Fetch from GitHub Actions and parse
python scripts/get-gh-action-logs.py --run-id 12345 | \
  grep -A 100 "Run tests with pytest" | \
  python scripts/parse-test-failures.py
```

---

## Troubleshooting

### "No workflow runs found"

- Check that the repository and workflow name are correct
- Verify you have permission to access the repository
- Try providing a GitHub token

### "Error: 'requests' module not found"

Install dependencies:
```bash
pip install requests
```

### "Could not fetch logs"

- Logs may not be available yet (workflow still running)
- Logs may have expired (GitHub keeps logs for 90 days)
- You may need authentication for private repositories

---

## See Also

- [GitHub Actions Workflow](.github/workflows/forge-tests.yml)
- [Pre-commit Checks](forge/scripts/pre-commit-check.py)
- [Copilot Instructions](.github/copilot-instructions.md)
