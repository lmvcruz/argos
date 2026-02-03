# CI Quality Integration Guide

This guide explains how to download and analyze code quality data from GitHub Actions CI runs.

## Overview

The CI integration extends Phase 3 quality tracking to capture lint data from continuous integration runs. This enables:

- Comparing local development quality vs CI environment quality
- Identifying platform-specific code quality issues
- Tracking quality trends across different environments
- Ensuring consistent quality between development and production

## Prerequisites

1. GitHub Personal Access Token with `repo` scope
2. Completed CI run with lint artifacts
3. Python environment with `requests` library installed

## Setup

### 1. Install Required Dependencies

```bash
pip install requests
```

### 2. Get GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Save the token securely

### 3. Set Environment Variable (Recommended)

```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "your_token_here"

# Linux/macOS
export GITHUB_TOKEN="your_token_here"
```

## Usage

### Step 1: Trigger CI Run

Push code to GitHub or manually trigger a workflow to generate lint artifacts:

```bash
git push origin main
```

Wait for the CI workflow to complete. The workflows will automatically run lint checks and upload artifacts.

### Step 2: Find Run ID

Go to your GitHub repository → Actions tab and find the run ID in the URL:

```
https://github.com/owner/repo/actions/runs/12345678
                                            ^^^^^^^^ <- This is the run_id
```

### Step 3: Download CI Lint Data

Run the download script to fetch and store CI lint artifacts:

```bash
# Basic usage (uses GITHUB_TOKEN env var)
python scripts/download_ci_lint.py <run_id>

# Custom repository
python scripts/download_ci_lint.py <run_id> --repo owner/repo

# Custom database
python scripts/download_ci_lint.py <run_id> --db .anvil/history.db

# Specific projects only
python scripts/download_ci_lint.py <run_id> --projects forge anvil

# Pass token explicitly (not recommended for security)
python scripts/download_ci_lint.py <run_id> --token your_token_here
```

**Example:**

```bash
python scripts/download_ci_lint.py 12345678
```

**Output:**

```
🔍 Downloading CI lint artifacts for run: 12345678
  Repository: your-org/your-repo
  Projects: forge, anvil, scout

📦 Downloading artifacts for forge...
   ✅ Downloaded: lint-forge-ubuntu-py3.11 (3 files)
   ✅ Processed and stored: 125 violations

📦 Downloading artifacts for anvil...
   ✅ Downloaded: lint-anvil-ubuntu-py3.11 (3 files)
   ✅ Processed and stored: 87 violations

📦 Downloading artifacts for scout...
   ✅ Downloaded: lint-scout-ubuntu-py3.11 (3 files)
   ✅ Processed and stored: 43 violations

✅ CI lint data stored in: .anvil/history.db
   Total violations: 255 across 3 projects

📊 Next steps:
   1. Generate CI quality report:
      python scripts/generate_quality_report.py --space ci

   2. Compare local vs CI quality:
      python scripts/generate_quality_report.py --compare

   3. View specific validator:
      python scripts/generate_quality_report.py --space ci --validator flake8
```

### Step 4: Generate Reports

#### View CI Quality Report

```bash
python scripts/generate_quality_report.py --space ci --format html
```

Opens `quality-report.html` showing only CI quality data.

#### Compare Local vs CI Quality

```bash
python scripts/generate_quality_report.py --compare
```

Opens `quality-comparison.html` showing side-by-side comparison:

- **Local**: Quality from your development machine
- **CI**: Quality from GitHub Actions
- **Delta**: Difference highlighting platform-specific issues

#### Filter by Validator

```bash
# Only flake8 comparison
python scripts/generate_quality_report.py --compare --validator flake8

# Only black comparison
python scripts/generate_quality_report.py --compare --validator black

# Only isort comparison
python scripts/generate_quality_report.py --compare --validator isort
```

## Understanding the Comparison Report

The comparison report shows three validators side-by-side:

### Color Coding

- **Blue border**: Local quality metrics
- **Purple border**: CI quality metrics
- **Green delta** (↓): Local has fewer violations (better)
- **Red delta** (↑): Local has more violations (worse)
- **Gray delta** (=): Same quality level

### Metrics Displayed

For each validator:

- **Total Violations**: Total number of quality issues found
- **Errors**: Critical issues that should be fixed
- **Warnings**: Non-critical style issues
- **Info**: Informational messages
- **Last Run**: Timestamp of the most recent scan

### Interpreting Results

**Scenario 1: Local Better (↓ Green)**
```
flake8: Local (5) vs CI (15) - Local better by 10 ✅
```
Your local environment has better quality. Possible reasons:
- Pre-commit hooks are working
- Recent fixes not yet in CI
- CI environment has different lint configuration

**Scenario 2: CI Better (↓ Green under CI)**
```
flake8: Local (25) vs CI (10) - Local has more violations ⚠️
```
CI environment has better quality. Possible reasons:
- Local pre-commit hooks not running
- CI configuration more strict
- Local environment has uncommitted changes

**Scenario 3: Same Quality (= Gray)**
```
flake8: Local (10) vs CI (10) - Same quality level
```
Consistent quality between environments ✅

## Common Workflows

### Daily Development

```bash
# 1. Run local tests with quality checks
python scripts/run_local_tests.py forge/tests/

# 2. After CI completes, download CI data
python scripts/download_ci_lint.py <run_id>

# 3. Compare local vs CI
python scripts/generate_quality_report.py --compare
```

### Quality Gate Verification

```bash
# 1. Generate CI quality report
python scripts/generate_quality_report.py --space ci --format markdown

# 2. Check if violations exceed threshold
# (Manual review for now, automated gates planned)
```

### Historical Analysis

```bash
# View quality trends over last 30 days
python scripts/generate_quality_report.py --space ci --window 30

# View specific time window
python scripts/generate_quality_report.py --space ci --window 7
```

## Troubleshooting

### "Authentication failed"

**Problem**: GitHub API returns 401 Unauthorized

**Solutions**:
1. Verify token is valid: `echo $GITHUB_TOKEN`
2. Regenerate token with `repo` scope
3. Pass token explicitly: `--token your_token`

### "Artifact not found"

**Problem**: Script can't find lint artifacts

**Solutions**:
1. Verify CI run completed successfully
2. Check workflow has artifact upload step
3. Verify artifact retention (30 days default)
4. Check artifact name matches pattern: `lint-{project}-ubuntu-py3.11`

### "No data in comparison"

**Problem**: Comparison report shows "No CI data" or "No local data"

**Solutions**:
1. Run local tests first: `python scripts/run_local_tests.py`
2. Download CI data: `python scripts/download_ci_lint.py <run_id>`
3. Check database has both spaces: `sqlite3 .anvil/history.db "SELECT DISTINCT space FROM lint_summary;"`

### "Database locked"

**Problem**: SQLite database is locked

**Solutions**:
1. Close any open database connections
2. Check no other scripts are running
3. Restart Python interpreter

## Advanced Usage

### Custom Output Directory

```bash
python scripts/download_ci_lint.py <run_id> --output-dir .ci-artifacts-archive/
```

### Multiple Run Comparison

```bash
# Download multiple CI runs
python scripts/download_ci_lint.py 12345678
python scripts/download_ci_lint.py 12345679
python scripts/download_ci_lint.py 12345680

# View trends
python scripts/generate_quality_report.py --space ci --window 7
```

### SQL Queries

Query the database directly for custom analysis:

```bash
# Count violations by space
sqlite3 .anvil/history.db "
SELECT space, validator, SUM(total_violations)
FROM lint_summary
GROUP BY space, validator;"

# Get latest local vs CI counts
sqlite3 .anvil/history.db "
SELECT space, validator, total_violations, timestamp
FROM lint_summary
WHERE space IN ('local', 'ci')
ORDER BY timestamp DESC
LIMIT 10;"

# Calculate average quality by space
sqlite3 .anvil/history.db "
SELECT space, validator,
       AVG(total_violations) as avg_violations,
       COUNT(*) as scans
FROM lint_summary
GROUP BY space, validator;"
```

## Integration with CI/CD

### Automated Quality Gates

(Planned feature)

```yaml
# Future: .github/workflows/quality-gate.yml
- name: Check quality threshold
  run: |
    python scripts/generate_quality_report.py --space ci --format markdown > report.md
    python scripts/check_quality_threshold.py --max-violations 100
```

### Slack Notifications

(Planned feature)

```bash
# Future: Post comparison to Slack
python scripts/post_quality_to_slack.py <run_id> --webhook $SLACK_WEBHOOK
```

## Files Generated

- `.ci-artifacts/`: Temporary directory for downloaded artifacts (auto-created)
- `quality-comparison.html`: Local vs CI comparison report
- `quality-report.html`: Standard quality report
- `.anvil/test_comparison.db`: Test database (from test script)

## Database Schema

The CI integration uses the same database schema as local quality tracking:

- **lint_summary**: Aggregate metrics per execution
  - `space`: "local" or "ci" to differentiate environments
  - `execution_id`: Format for CI runs: "ci-{run_id}-{project}"

- **lint_violations**: Individual violations
  - Links to execution_id
  - Contains file path, line number, severity, code, message

- **code_quality_metrics**: Long-term statistics
  - Tracks trends across all spaces

## Security Best Practices

1. **Never commit tokens to git**: Use environment variables
2. **Use token with minimal scope**: Only `repo` access needed
3. **Rotate tokens regularly**: Invalidate old tokens
4. **Use GitHub Actions secrets**: For automated workflows
5. **Set token expiration**: Use expiring tokens when possible

## Next Steps

After setting up CI integration:

1. ✅ Run local quality checks regularly
2. ✅ Download CI data after each merge
3. ✅ Compare local vs CI to catch issues
4. ⏳ Set up automated quality gates (planned)
5. ⏳ Configure Slack notifications (planned)
6. ⏳ Add quality trend charts (planned)

## Support

For issues or questions:

1. Check TROUBLESHOOTING.md in docs/
2. Review GitHub Actions workflow logs
3. Query database directly to verify data
4. Open an issue on GitHub

---

**Last Updated**: 2024 (Phase 3 CI Integration)
