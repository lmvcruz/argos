# Local Test Execution Tracking

## Overview

To enable meaningful local vs CI comparisons in Lens, all local test executions should be recorded in the Anvil database with `space="local"`.

## Quick Start

### Install Required Package

```bash
pip install pytest-json-report
```

### Run Tests with History Tracking

```bash
# Run all tests
python scripts/run_local_tests.py

# Run specific test file
python scripts/run_local_tests.py forge/tests/test_models.py

# Run with pytest options
python scripts/run_local_tests.py -v -k test_validation

# Run specific module tests
python scripts/run_local_tests.py forge/tests/
python scripts/run_local_tests.py anvil/tests/
python scripts/run_local_tests.py scout/tests/
```

## What Gets Tracked

Each test execution records:

```python
ExecutionHistory(
    execution_id="local-20260202-143052",
    entity_id="forge/tests/test_models.py::test_validation",
    entity_type="test",
    timestamp=datetime.now(),
    status="PASSED",  # or FAILED, SKIPPED, ERROR
    duration=0.123,
    space="local",  # ← Differentiates from CI
    metadata={
        "source": "run_local_tests.py",
        "pytest_args": "-v -k test_validation"
    }
)
```

## Automatic Statistics Updates

After each run, statistics are automatically updated:

- Total runs per test
- Pass/fail counts
- Failure rates
- Average duration
- Last run timestamp
- Last failure timestamp

## Comparing Local vs CI

### After Running Local Tests

1. **Run local tests**:
   ```bash
   python scripts/run_local_tests.py anvil/tests/
   ```

2. **Generate combined report**:
   ```bash
   cd lens
   python -m lens report test-execution --db ../.anvil/history.db --format html --output combined-report.html
   ```

3. **View space-specific data** (future feature):
   ```bash
   # CI only
   python -m lens report test-execution --space ci --format html

   # Local only
   python -m lens report test-execution --space local --format html

   # Comparison
   python -m lens report comparison --local-vs-ci --format html
   ```

## Integration with pytest.ini

For automatic tracking on every test run, add to `pytest.ini`:

```ini
[pytest]
# ... existing config ...

# Automatic JSON reporting
addopts = --json-report --json-report-file=.pytest_cache/report.json
```

Then create a pytest plugin to auto-record history:

```python
# conftest.py (at project root)
import pytest
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory
from datetime import datetime

def pytest_sessionfinish(session, exitstatus):
    """Record execution history after test session."""
    # Read .pytest_cache/report.json
    # Store in database with space="local"
    # Update statistics
    pass
```

## Best Practices

### 1. Run Tests Regularly

Run local tests before committing:

```bash
# Before commit
python scripts/run_local_tests.py

# Or integrate with pre-commit hook
```

### 2. Track Different Test Suites

Track each module separately for better granularity:

```bash
python scripts/run_local_tests.py forge/tests/
python scripts/run_local_tests.py anvil/tests/
python scripts/run_local_tests.py scout/tests/
```

### 3. Review Trends

Periodically check local test trends:

```bash
cd anvil
python -m anvil.cli.main stats show --type test
python -m anvil.cli.main stats flaky --threshold 10
```

## Troubleshooting

### "pytest-json-report not found"

**Solution**:
```bash
pip install pytest-json-report
```

### "Database locked"

**Cause**: Another process is using the database.

**Solution**: Wait for other operations to complete, or use a different database file:
```bash
python scripts/run_local_tests.py --db .anvil/local-history.db
```

### "Statistics not updating"

**Cause**: StatisticsCalculator may have an issue.

**Solution**: Manually update statistics:
```bash
cd anvil
python -c "from anvil.storage.execution_schema import ExecutionDatabase; from anvil.core.statistics_calculator import StatisticsCalculator; db = ExecutionDatabase('.anvil/history.db'); calc = StatisticsCalculator(db); stats = calc.calculate_all_stats(); [db.update_entity_statistics(s) for s in stats]; db.close()"
```

## Example Workflow

### Daily Development Workflow

```bash
# 1. Morning: Check CI status
python scripts/sync_ci_to_anvil.py $(scout ci show --latest)

# 2. Development: Run relevant tests locally
python scripts/run_local_tests.py forge/tests/test_models.py -v

# 3. Before commit: Run full suite
python scripts/run_local_tests.py

# 4. After commit: Compare local vs CI
cd lens
python -m lens report test-execution --format html
```

### Weekly Review

```bash
# 1. Sync all CI runs from past week
for run_id in $(scout ci list --since 7days --format ids); do
    python scripts/sync_ci_to_anvil.py $run_id
done

# 2. Generate comprehensive report
cd lens
python -m lens report test-execution --window 7 --format html --output weekly-report.html

# 3. Identify issues
python -m anvil.cli.main stats flaky --threshold 5 --window 50
```

## Database Schema

Local and CI executions share the same schema, differentiated by `space`:

| Column | Local Example | CI Example |
|--------|---------------|------------|
| execution_id | `local-20260202-143052` | `ci-21589120797-62204520085` |
| entity_id | `forge/tests/test_models.py::test_validation` | Same |
| space | `local` | `ci` |
| metadata | `{"source": "run_local_tests.py"}` | `{"platform": "ubuntu-latest", "python_version": "3.11"}` |

This allows Lens to:
- Aggregate across both spaces for overall statistics
- Filter by space for targeted analysis
- Compare same tests across environments

## Future Enhancements

### Automatic IDE Integration

VSCode extension to track test runs automatically:

```json
// .vscode/settings.json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "--json-report",
    "--json-report-file=.pytest_cache/report.json"
  ],
  "argos.autoTrackTests": true
}
```

### Git Hook Integration

Automatically track tests on pre-commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash
python scripts/run_local_tests.py --quiet
```

### CI/CD Integration

Automatically sync CI results after each run:

```yaml
# .github/workflows/tests.yml
- name: Sync results to Anvil
  if: always()
  run: |
    python scripts/sync_ci_to_anvil.py ${{ github.run_id }}
```

---

**Last Updated**: February 2, 2026
**Status**: Production Ready
