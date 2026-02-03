# Scout → Anvil → Lens Integration Plan

## Overview

Extend the current Anvil → Lens integration to include **CI test data from GitHub Actions**, enabling:
- Local vs CI test comparison
- Platform-specific failure detection
- CI health monitoring
- Complete test execution visibility

---

## Architecture

```
GitHub Actions (CI)
  ↓ Scout retrieves logs
Scout CI Log Parser
  ↓ Parses pytest output
Anvil Database (.anvil/history.db)
  ↓ Stores with space="ci"
Lens Analytics
  ↓ Generates reports
Integrated Local + CI Reports
```

---

## Implementation Steps

### Phase 1: Scout Enhancement (CI Test Parsing)

**File**: `scout/parsers/test_result_parser.py`

```python
class CITestResultParser:
    """Parse test results from CI logs."""

    def parse_pytest_output(self, log_content: str) -> List[TestResult]:
        """
        Parse pytest output from CI logs.

        Extracts:
        - Test node IDs
        - Pass/fail/skip status
        - Duration
        - Error messages
        """

    def parse_junit_xml(self, xml_content: str) -> List[TestResult]:
        """Parse JUnit XML artifacts from CI."""
```

**File**: `scout/integration/anvil_bridge.py`

```python
class AnvilBridge:
    """Bridge between Scout (CI data) and Anvil (storage)."""

    def sync_ci_run_to_anvil(
        self,
        run_id: int,
        job_id: int,
        anvil_db_path: str = ".anvil/history.db"
    ):
        """
        Sync CI run test results to Anvil database.

        Process:
        1. Retrieve CI logs via Scout
        2. Parse test results
        3. Store in Anvil DB with space="ci"
        4. Update statistics
        """
```

### Phase 2: Anvil Database Schema (Already Supports This!)

The current schema already supports this via the `space` field:

```python
class ExecutionHistory:
    execution_id: str  # "ci-21589120797"
    entity_id: str     # "forge/tests/test_*.py::test_func"
    entity_type: str   # "test"
    status: str        # "PASSED"/"FAILED"
    duration: float
    space: str         # "ci" instead of "local"  ← KEY DIFFERENCE
    metadata: dict     # {"platform": "ubuntu-latest", "python": "3.11"}
```

### Phase 3: Lens Enhancements (CI Reports)

**New Report Type**: `ci-health`

```python
# lens/analytics/ci_health.py

class CIHealthAnalyzer:
    """Analyze CI test execution health."""

    def get_ci_summary(self, window_days=30):
        """Get CI execution summary."""
        # Query executions WHERE space='ci'

    def get_platform_breakdown(self):
        """Break down by platform (ubuntu, windows, macos)."""

    def compare_local_vs_ci(self):
        """Compare local and CI test results."""
        # WHERE space='local' vs space='ci'
```

**CLI Commands**:
```bash
# Generate CI health report
lens report ci-health --window 30 --format html

# Compare local vs CI
lens report comparison --local-vs-ci --format html
```

---

## Proof of Concept

Let me create a working demo that:
1. Retrieves a real CI run from GitHub Actions
2. Parses the test results
3. Stores in Anvil database
4. Generates Lens report

### Step 1: Retrieve CI Run

```bash
# Using Scout (already works!)
cd scout
python -m scout.cli ci show --run-id 21589120797
```

### Step 2: Parse Test Results

We need to extract test results from the logs. GitHub Actions pytest typically outputs:
- Individual test results
- Summary statistics
- JUnit XML artifacts (if configured)

### Step 3: Store in Anvil

```python
# Same database, different space
execution_history = ExecutionHistory(
    execution_id="ci-21589120797-1",
    entity_id="forge/tests/test_argument_parser.py::test_basic",
    entity_type="test",
    status="PASSED",
    duration=1.23,
    space="ci",  # ← Marks this as CI execution
    metadata={
        "run_id": 21589120797,
        "platform": "ubuntu-latest",
        "python_version": "3.11",
        "job_name": "test"
    }
)
```

### Step 4: Generate Reports

Lens can now query both:
```sql
-- Local tests
SELECT * FROM execution_history WHERE space='local'

-- CI tests
SELECT * FROM execution_history WHERE space='ci'

-- Comparison
SELECT
    entity_id,
    SUM(CASE WHEN space='local' AND status='PASSED' THEN 1 ELSE 0 END) as local_passed,
    SUM(CASE WHEN space='ci' AND status='PASSED' THEN 1 ELSE 0 END) as ci_passed
FROM execution_history
GROUP BY entity_id
```

---

## Implementation Priority

### Quick Win (1-2 hours)

Create a simple script that:
1. Takes a CI run ID
2. Downloads logs via Scout
3. Parses pytest output (regex-based)
4. Stores in Anvil database
5. Shows comparison report

### Full Implementation (Phase 0.3 + 0.4)

Follow the implementation plan:
- Scout enhancement for test parsing
- AnvilBridge for automated sync
- Lens CI health dashboard
- Platform comparison reports

---

## Example Workflow

```bash
# 1. Sync recent CI runs
scout ci sync --limit 10

# 2. View CI statistics
cd ../anvil
anvil stats show --type test --space ci

# 3. Compare local vs CI
anvil stats compare --local-vs-ci

# 4. Generate integrated report
cd ../lens
lens report comparison --local-vs-ci --format html --output ci-comparison.html

# 5. View report
start ci-comparison.html
```

---

## Expected Output

### Console Report
```
CI vs Local Test Comparison
==========================================================================================

Total Tests: 739
Local Executions: 1,875
CI Executions: 245 (last 10 runs)

Platform-Specific Failures:
  Windows-only failures: 3 tests
  - test_symlink_collection (expected - Windows symlink limitation)
  - test_file_permissions
  - test_path_handling

  Linux-only failures: 0 tests

Local-only failures: 2 tests
  - test_database_lock (likely timing issue)
  - test_concurrent_access

CI-only failures: 5 tests
  - test_network_dependency (CI network isolation)
  - test_timeout_threshold (CI resource constraints)
```

### HTML Report Features
- Side-by-side success rate comparison
- Platform breakdown heatmap
- Failure pattern identification
- Reproduction commands for CI-specific failures

---

## Benefits

1. **Platform-Specific Issue Detection**: See which tests fail only on CI (or only locally)
2. **Complete Visibility**: Track all test executions (local + CI) in one place
3. **Root Cause Analysis**: Identify environmental differences
4. **Reproducibility**: CI failures can be reproduced locally with environment info
5. **Trend Analysis**: CI health over time

---

## Next Steps

Would you like me to:

**Option A: Quick Demo**
- Create script to parse one CI run
- Store in Anvil database
- Show basic comparison

**Option B: Full Implementation**
- Implement Scout test result parser
- Create AnvilBridge for automated sync
- Extend Lens with CI reports
- Add platform comparison features

**Option C: Minimal Viable Product**
- Parse pytest output from CI logs
- Store as `space="ci"`
- Extend existing Lens report to filter by space
- Add simple local/CI comparison table

Let me know which approach you'd like, and I'll implement it!
