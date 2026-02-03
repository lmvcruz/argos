# Test Failure Analysis Scripts

This directory contains scripts to help analyze test failures from both local runs and GitHub Actions.

## Scripts

### 1. `get-gh-action-logs.py`

Fetch and parse GitHub Actions logs for failed tests.

**Requirements:**
```bash
pip install requests python-dotenv
```

**Setup (Recommended):**

Create a `.env` file in the project root (`argos/.env`):
```bash
GITHUB_TOKEN=your_github_token_here
```

The script will automatically load this token. The `.env` file is already in `.gitignore` so your token won't be committed.

**Usage:**

**Easiest Method (using .env file):**
```bash
# Just call the script - token loaded automatically from .env
python scripts/get-gh-action-logs.py --workflow "Forge Tests"
python scripts/get-gh-action-logs.py --workflow "Forge Tests" --detailed
python scripts/get-gh-action-logs.py --run-id 12345
```

**Alternative: Environment Variable (without .env file):**

PowerShell:
```powershell
$env:GITHUB_TOKEN = "your_github_token_here"
python scripts/get-gh-action-logs.py --workflow "Forge Tests"
```

Bash/Zsh:
```bash
export GITHUB_TOKEN="your_github_token_here"
python scripts/get-gh-action-logs.py --workflow "Forge Tests"
```

**More Options:**
```bash
# Fetch latest workflow run (no auth - rate limited to 60 requests/hour)
python scripts/get-gh-action-logs.py

# Show detailed failure context with error messages
python scripts/get-gh-action-logs.py --detailed

# Different repository
python scripts/get-gh-action-logs.py --owner username --repo reponame

# Pass token directly (not recommended - use environment variable instead)
python scripts/get-gh-action-logs.py --token "your_token" --workflow "Forge Tests"
```

**Features:**
- Fetches latest or specific GitHub Actions workflow run
- Extracts failed job logs
- Parses pytest failure information (FAILED and ERROR lines)
- **Extracts collection errors** (ModuleNotFoundError, ImportError, etc.)
- **Shows actual error messages** from pytest output
- Shows clean summary of all failed tests
- Optional detailed failure context
- ASCII-safe output (works in all terminals)

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

## Quality Tracking Scripts (Phase 3)

### 3. `run_local_tests.py`

Run tests with automatic coverage and quality tracking (Phase 1-3 integration).

**Usage:**
```bash
# Run all tests with coverage and quality checks
python scripts/run_local_tests.py

# Run specific test file
python scripts/run_local_tests.py forge/tests/test_argument_parser.py

# With custom coverage options
python scripts/run_local_tests.py --cov=forge/cli --cov-report=xml
```

**Features**:
- Automatic pytest execution
- Coverage data collection
- Lint scanning (flake8, black, isort)
- Quality metrics storage
- Summary output with all metrics

### 4. `generate_quality_report.py`

Generate HTML/Markdown quality reports from lint data.

**Usage:**
```bash
# Generate HTML quality report (all data)
python scripts/generate_quality_report.py

# Filter by space (local or CI)
python scripts/generate_quality_report.py --space local
python scripts/generate_quality_report.py --space ci

# Filter by validator
python scripts/generate_quality_report.py --validator flake8
python scripts/generate_quality_report.py --validator black

# Generate markdown report
python scripts/generate_quality_report.py --format markdown

# Time window (last N days)
python scripts/generate_quality_report.py --window 7

# Compare local vs CI quality
python scripts/generate_quality_report.py --compare

# Compare specific validator
python scripts/generate_quality_report.py --compare --validator flake8
```

**Output**:
- `quality-report.html`: Detailed HTML report with metrics
- `quality-report.md`: Markdown report for documentation
- `quality-comparison.html`: Side-by-side local vs CI comparison

### 5. `download_ci_lint.py` (CI Integration)

Download lint artifacts from GitHub Actions CI runs and store in database.

**Requirements:**
```bash
pip install requests
export GITHUB_TOKEN="your_token_here"  # or use .env file
```

**Usage:**
```bash
# Download CI lint data (basic - uses env var GITHUB_TOKEN)
python scripts/download_ci_lint.py <run_id>

# Example with specific run
python scripts/download_ci_lint.py 12345678

# Custom repository
python scripts/download_ci_lint.py 12345678 --repo owner/repo

# Custom database
python scripts/download_ci_lint.py 12345678 --db .anvil/history.db

# Specific projects only
python scripts/download_ci_lint.py 12345678 --projects forge anvil

# With token (alternative to env var)
python scripts/download_ci_lint.py 12345678 --token $GITHUB_TOKEN
```

**Features**:
- Downloads lint artifacts from GitHub Actions
- Parses flake8, black, isort output
- Stores in database with `space="ci"`
- Enables local vs CI comparison

**Finding Run ID**:
Go to GitHub Actions and find the run ID in the URL:
```
https://github.com/owner/repo/actions/runs/12345678
                                            ^^^^^^^^ <- This is the run_id
```

### Typical Workflow

**Daily Development**:
```bash
# 1. Run local tests with quality checks
python scripts/run_local_tests.py forge/tests/

# 2. View local quality report
python scripts/generate_quality_report.py --space local

# 3. After pushing to GitHub and CI completes
python scripts/download_ci_lint.py <run_id>

# 4. Compare local vs CI
python scripts/generate_quality_report.py --compare
```

---

## See Also

- [GitHub Actions Workflow](.github/workflows/forge-tests.yml)
- [Pre-commit Checks](forge/scripts/pre-commit-check.py)
- [Copilot Instructions](.github/copilot-instructions.md)
- [CI Quality Integration Guide](../docs/ci-quality-integration.md)
- [Quality Quick Reference](../docs/quality-quick-reference.md)
- [Phase 3 Complete](../docs/phase-3-complete.md)
