# CI Test Data Sync - Quick Reference

## 🚀 Quick Start

### Prerequisites
1. GITHUB_TOKEN in `.env` file
2. Python dependencies installed

### Sync a CI Run

```bash
# From project root
python scripts/sync_ci_to_anvil.py <run_id>

# Example
python scripts/sync_ci_to_anvil.py 21589120797
```

### View Results

```bash
# Check database
python scripts/check_db.py

# Generate HTML report
cd lens
python -m lens report test-execution --db ../.anvil/history.db --format html --output ../report.html

# Open report
start ../report.html
```

---

## 📋 Common Commands

### Get Latest CI Run ID

```bash
# From Scout
cd scout
python -m scout.cli ci show --latest
```

### Sync Multiple Runs

```bash
# Sync runs one by one
python scripts/sync_ci_to_anvil.py 21589120797
python scripts/sync_ci_to_anvil.py 21589120796
python scripts/sync_ci_to_anvil.py 21589120795
```

### Query CI Data

```bash
# View CI executions in database
sqlite3 .anvil/history.db "SELECT COUNT(*) FROM execution_history WHERE space='ci';"

# View by platform
sqlite3 .anvil/history.db "
  SELECT json_extract(metadata, '$.platform'), COUNT(*)
  FROM execution_history
  WHERE space='ci'
  GROUP BY json_extract(metadata, '$.platform');
"

# View by Python version
sqlite3 .anvil/history.db "
  SELECT json_extract(metadata, '$.python_version'), COUNT(*)
  FROM execution_history
  WHERE space='ci'
  GROUP BY json_extract(metadata, '$.python_version');
"
```

---

## 🔍 Troubleshooting

### "GITHUB_TOKEN not found"

**Solution**: Add to `.env` file:
```env
GITHUB_TOKEN=ghp_your_token_here
```

### "No module named dotenv"

**Solution**: Install python-dotenv:
```bash
pip install python-dotenv
```

### "Run not found"

**Solution**: Verify run ID exists:
```bash
cd scout
python -m scout.cli ci show --run-id <run_id>
```

### "No pytest output found"

**Reason**: Some jobs (like lint, quality) don't run pytest tests.
**Expected**: Parser will skip these jobs (no error).

---

## 📊 Expected Output

### Successful Sync

```
✓ Loaded environment from D:\playground\argos\.env
================================================================================
SYNCING CI RUN 21589120797 TO ANVIL DATABASE
================================================================================

1. Connecting to GitHub Actions...

2. Fetching run 21589120797 details...
   Workflow: Anvil Tests
   Status: completed
   Conclusion: success
   Branch: main

3. Fetching jobs for run 21589120797...
   Found 17 jobs

4. Connecting to Anvil database: .anvil/history.db

5. Processing job: test (ubuntu-latest, 3.11)
   Job ID: 62204520085
   Status: completed
   Conclusion: success
   Downloading logs...
   Log size: 137557 bytes
   Parsing pytest output...
   Found 1039 test results
   ✓ Stored 1039 test results

[... more jobs ...]

6. Updating entity statistics...
   ✓ Updated statistics for 1054 entities

================================================================================
SYNC COMPLETE
================================================================================

Summary:
  CI Run: 21589120797
  Jobs Processed: 16
  Test Results Stored: 16624
  Database: .anvil/history.db
```

### Database Growth

| Metric | Before | After Sync | Delta |
|--------|--------|------------|-------|
| Total Executions | 1,875 | 18,499 | +16,624 |
| Entities | 15 | 1,054 | +1,039 |
| CI Executions | 0 | 16,624 | +16,624 |

---

## 🎯 What Gets Synced

### Per Job

- **Test Results**: All PASSED/FAILED/SKIPPED/ERROR tests
- **Metadata**:
  - Platform (ubuntu-latest, windows-latest, macos-latest)
  - Python version (3.8, 3.9, 3.10, 3.11, 3.12)
  - Run URL (link to GitHub Actions run)
  - Job name
  - Workflow name
  - Branch name
  - Timestamp (job start time)

### Database Storage

```python
ExecutionHistory(
    execution_id="ci-{run_id}-{job_id}",
    entity_id="path/to/test.py::test_name",
    space="ci",  # ← Differentiates from local tests
    metadata={
        "platform": "ubuntu-latest",
        "python_version": "3.11",
        "run_url": "https://github.com/...",
        ...
    }
)
```

---

## 📈 Reports

### HTML Report

**Command**:
```bash
cd lens
python -m lens report test-execution --db ../.anvil/history.db --format html --output ../report.html
start ../report.html
```

**Includes**:
- Total executions (local + CI)
- Success rate
- Flaky test detection
- Slowest tests
- Execution trends

### Future: Space-Filtered Reports

```bash
# CI only
lens report test-execution --space ci --format html

# Local only
lens report test-execution --space local --format html

# Comparison
lens report comparison --local-vs-ci --format html
```

---

## 💡 Tips

### Finding Run IDs

1. **GitHub UI**: Go to Actions → Workflow → Click run → URL contains run ID
   ```
   https://github.com/lmvcruz/argos/actions/runs/21589120797
                                                  ^^^^^^^^^^ Run ID
   ```

2. **Scout CLI**:
   ```bash
   cd scout
   python -m scout.cli ci list --limit 10
   ```

3. **API**:
   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" \
     https://api.github.com/repos/lmvcruz/argos/actions/runs
   ```

### Selective Syncing

**Sync only successful runs**:
- Check conclusion before syncing
- Use Scout CLI to filter by status

**Sync by date range**:
- Query GitHub Actions API for runs in date range
- Loop through run IDs

**Avoid re-syncing**:
- Check if `execution_id` already exists in database
- Skip if already synced

---

## 🔗 Related Documentation

- [CI Integration Success Report](ci-integration-success.md) - Complete results
- [Scout → Anvil → Lens PoC](scout-anvil-lens-poc.md) - Architecture overview
- [Scout → Anvil → Lens Integration Plan](scout-anvil-lens-integration-plan.md) - Implementation roadmap

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](../forge/docs/TROUBLESHOOTING.md)
2. Review error messages in terminal output
3. Verify `.env` file has GITHUB_TOKEN
4. Check database with `scripts/check_db.py`

---

**Last Updated**: February 2, 2026
**Tested With**: Run 21589120797 (16,624 test results)
