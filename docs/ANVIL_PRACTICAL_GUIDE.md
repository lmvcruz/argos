# Practical Guide: Working with Anvil Parsed Data

## Table of Contents
0. Using Anvil CLI Parse Command
1. Using Anvil Parsers Directly
2. Querying Anvil Database
3. Accessing via Verdict Adapters
4. Accessing via REST API
5. Common Scenarios

---

## 0. Using Anvil CLI Parse Command

### What is the Parse Command?

The `anvil parse` command parses tool output **without running any validators**. This is useful for:
- Testing parsers in isolation
- Debugging tool output format
- Integrating with external tools
- Converting tool output to Verdict-compatible format

### Basic Usage

```bash
# Parse from a file
anvil parse --tool flake8 --file output.txt

# Parse from stdin
cat output.txt | anvil parse --tool flake8 --input -

# Parse from command line argument
anvil parse --tool black --input "error: cannot format..."
```

### Supported Tools

- `black` - Black formatter output
- `flake8` - Flake8 linter output
- `isort` - isort import sorter output
- `pylint` - Pylint linter output
- `pytest` - Pytest test runner output
- `coverage` - Coverage measurement output

### Examples

```bash
# Parse flake8 output from file
anvil parse --tool flake8 --file flake8_results.txt

# Parse black output from stdin
flake8 myfile.py | anvil parse --tool flake8 --input -

# Parse isort output
isort --check-only --diff myfile.py | anvil parse --tool isort --input -

# Parse pytest output
pytest --tb=short | anvil parse --tool pytest --input -
```

### Output Format

The parse command outputs JSON in Verdict-compatible format:

```json
{
  "validator": "flake8",
  "passed": false,
  "total_violations": 3,
  "errors": 2,
  "warnings": 1,
  "files_checked": 1,
  "execution_time": 0.0,
  "by_code": {
    "E501": 1,
    "F841": 1,
    "W292": 1
  },
  "file_violations": {
    "test.py": [
      {
        "line": 10,
        "column": 1,
        "code": "E501",
        "message": "line too long (100 > 79 characters)",
        "severity": "error"
      }
    ]
  }
}
```

### Use Cases

**1. Testing Parser Implementation**

```bash
# If you modify a parser, test it in isolation
echo "test.py:10:1: E501 line too long" | anvil parse --tool flake8 --input -
```

**2. Integrating with CI/CD**

```bash
# Capture tool output and parse it
flake8 src/ > flake8_output.txt
anvil parse --tool flake8 --file flake8_output.txt > parsed_results.json
```

**3. Building a Custom Tool**

```python
# Subprocess to parse external tool output
import subprocess
import json

result = subprocess.run(
    ["anvil", "parse", "--tool", "flake8", "--file", "output.txt"],
    capture_output=True,
    text=True,
)
parsed = json.loads(result.stdout)
print(f"Found {parsed['total_violations']} violations")
```

---

## 1. Using Anvil Parsers Directly

### Parsing Black Output

```python
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

# Create parser
parser = LintParser()

# Raw black output
black_output = """
error: cannot format module: Black does not support Python 3.7
Oh no! 💥 💔 💥
error: 2 files failed to reformat.
"""

# Parse it
lint_data = parser.parse_black_output(black_output, Path("."))

# Access parsed data
print(f"Validator: {lint_data.validator}")  # "black"
print(f"Total Violations: {lint_data.total_violations}")  # 2
print(f"Errors: {lint_data.errors}")  # 2
print(f"By Code: {lint_data.by_code}")  # {"E901": 2}
print(f"File Violations: {lint_data.file_violations}")  # []
```

### Parsing Flake8 Output

```python
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

parser = LintParser()

flake8_output = """
module.py:10:1: E501 line too long (100 > 79 characters)
module.py:15:5: F841 local variable 'x' is assigned to but never used
module.py:20:1: W292 no newline at end of file
"""

lint_data = parser.parse_flake8_output(flake8_output, Path("."))

print(f"Validator: {lint_data.validator}")  # "flake8"
print(f"Files Scanned: {lint_data.files_scanned}")
print(f"Total Violations: {lint_data.total_violations}")  # 3
print(f"Errors: {lint_data.errors}")  # 1
print(f"Warnings: {lint_data.warnings}")  # 2

# Access file violations
for file_violation in lint_data.file_violations:
    print(f"\nFile: {file_violation.file_path}")
    for violation in file_violation.violations:
        print(f"  Line {violation['line']}: {violation['code']} - {violation['message']}")
```

### Parsing isort Output

```python
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

parser = LintParser()

isort_output = """
isort would reformat module.py
---

import os
+import sys
 import json
"""

lint_data = parser.parse_isort_output(isort_output, Path("."))

print(f"Validator: {lint_data.validator}")  # "isort"
print(f"Total Violations: {lint_data.total_violations}")
print(f"By Code: {lint_data.by_code}")  # {"I001": count}
```

---

## 2. Querying Anvil Database

### Basic Setup

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine

# Connect to database
db = StatisticsDatabase(".anvil/execution.db")
query_engine = StatisticsQueryEngine(db)
```

### Get All Validation Runs

```python
# Get last 10 runs
runs = query_engine.get_validation_runs(limit=10)

for run in runs:
    print(f"Run #{run.id}")
    print(f"  Timestamp: {run.timestamp}")
    print(f"  Branch: {run.git_branch}")
    print(f"  Commit: {run.git_commit}")
    print(f"  Status: {'PASS' if run.passed else 'FAIL'}")
    print(f"  Duration: {run.duration_seconds}s")
    print()
```

### Get Tests for a Run

```python
run_id = 1
tests = query_engine.get_test_case_records(run_id=run_id)

print(f"Tests in Run {run_id}:")
for test in tests:
    status = "✓" if test.passed else "✗"
    print(f"  {status} {test.test_suite}::{test.test_name}")
    print(f"      Duration: {test.duration_seconds}s")
    if test.failure_message:
        print(f"      Failure: {test.failure_message}")
```

### Get Lint Results

```python
# Get lint summary for a run
run_id = 1
lint_summaries = query_engine.get_lint_summary(run_id=run_id)

print(f"Lint Results for Run {run_id}:")
for lint in lint_summaries:
    print(f"\n  Validator: {lint.validator}")
    print(f"    Files Scanned: {lint.files_scanned}")
    print(f"    Total Violations: {lint.total_violations}")
    print(f"    Errors: {lint.errors}")
    print(f"    Warnings: {lint.warnings}")
    print(f"    By Code: {lint.by_code}")

# Get detailed violations
violations = query_engine.get_lint_violations(run_id=run_id)

print(f"\nDetailed Violations for Run {run_id}:")
for violation in violations:
    print(f"  {violation.file_path}:{violation.line_number}")
    print(f"    [{violation.severity}] {violation.code}: {violation.message}")
```

### Get Coverage Data

```python
# Coverage summary
coverage = query_engine.get_coverage_summary(run_id=1)

print("Coverage Summary:")
for cov in coverage:
    print(f"  Total Coverage: {cov.total_coverage}%")
    print(f"  Files Analyzed: {cov.files_analyzed}")
    print(f"  Covered: {cov.covered_statements}/{cov.total_statements}")

# Coverage history (per file)
coverage_history = query_engine.get_coverage_history(run_id=1)

print("\nCoverage by File:")
for item in coverage_history:
    coverage_pct = (item.covered_statements / item.total_statements * 100) if item.total_statements > 0 else 0
    print(f"  {item.file_path}: {coverage_pct:.1f}%")
```

### Get Validator Results

```python
# Validator summary for a run
validators = query_engine.get_validator_run_records(run_id=1)

print("Validator Results:")
for validator in validators:
    status = "PASS" if validator.passed else "FAIL"
    print(f"  {validator.validator_name}: {status}")
    print(f"    Files Checked: {validator.files_checked}")
    print(f"    Errors: {validator.error_count}")
    print(f"    Warnings: {validator.warning_count}")

# Per-file validation results
file_results = query_engine.get_file_validation_records(run_id=1)

print("\nFile-Level Results:")
for result in file_results:
    print(f"  {result.file_path} ({result.validator_name})")
    print(f"    Errors: {result.error_count}, Warnings: {result.warning_count}")
```

### Advanced Queries

```python
# Get runs from last 7 days
from datetime import datetime, timedelta

seven_days_ago = datetime.now() - timedelta(days=7)
recent_runs = query_engine.get_validation_runs(limit=100)
recent = [r for r in recent_runs if datetime.fromisoformat(r.timestamp) > seven_days_ago]

print(f"Runs from last 7 days: {len(recent)}")

# Get failed runs
failed_runs = [r for r in query_engine.get_validation_runs(limit=100) if not r.passed]
print(f"Failed runs: {len(failed_runs)}")

# Get specific validator violations
violations = query_engine.get_lint_violations(run_id=1)
flake8_violations = [v for v in violations if v.validator == "flake8"]
print(f"Flake8 violations: {len(flake8_violations)}")

# Get violations by code
e501_violations = [v for v in violations if v.code == "E501"]
print(f"E501 (line too long) violations: {len(e501_violations)}")
```

---

## 3. Accessing via Verdict Adapters

### Using Adapters Programmatically

```python
from anvil.validators.adapters import (
    validate_black_parser,
    validate_flake8_parser,
    validate_isort_parser,
)

# Raw tool outputs
black_output = "error: cannot format module..."
flake8_output = "module.py:10:1: E501 line too long..."
isort_output = "isort would reformat module.py..."

# Call adapters to get parsed dicts
black_result = validate_black_parser(black_output)
flake8_result = validate_flake8_parser(flake8_output)
isort_result = validate_isort_parser(isort_output)

# Now you have dicts ready for validation or storage
print(f"Black result: {black_result}")
# Output:
# {
#   'validator': 'black',
#   'total_violations': 1,
#   'errors': 1,
#   'warnings': 0,
#   'by_code': {'E901': 1},
#   ...
# }
```

### Using Adapters with Verdict

```python
# Verdict Runner uses adapters internally:
from verdict.runner import TestRunner
from pathlib import Path

config_path = Path("anvil/tests/validation/config.yaml")
runner = TestRunner(config_path)

# Run all tests
results = runner.run_all()

# Results contain pass/fail for each test
for result in results:
    print(f"{result.test_name}: {'PASS' if result.passed else 'FAIL'}")
    if not result.passed:
        for diff in result.differences:
            print(f"  - {diff}")
```

---

## 4. Accessing via REST API (Lens Backend)

### Setup Backend

```python
# lens/backend/server.py

from fastapi import FastAPI
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine

app = FastAPI()
db = StatisticsDatabase(".anvil/execution.db")
query_engine = StatisticsQueryEngine(db)

# The backend exposes these endpoints:
```

### Available Endpoints

```bash
# Get recent validation runs
GET /api/validation/runs?limit=10

# Get tests for a run
GET /api/validation/runs/{run_id}/tests

# Get lint results
GET /api/validation/runs/{run_id}/lint

# Get coverage results
GET /api/validation/runs/{run_id}/coverage

# Get validator results
GET /api/validation/runs/{run_id}/validators

# Get file-level results
GET /api/validation/runs/{run_id}/files
```

### Example JavaScript/Fetch Calls

```javascript
// Get recent runs
const runs = await fetch('/api/validation/runs?limit=10')
  .then(res => res.json());

console.log(`Found ${runs.length} runs`);
runs.forEach(run => {
  console.log(`Run #${run.id}: ${run.timestamp} - ${run.passed ? 'PASS' : 'FAIL'}`);
});

// Get tests for first run
const runId = runs[0].id;
const tests = await fetch(`/api/validation/runs/${runId}/tests`)
  .then(res => res.json());

console.log(`Found ${tests.length} tests`);
tests.forEach(test => {
  console.log(`  ${test.test_suite}::${test.test_name}: ${test.passed ? 'PASS' : 'FAIL'}`);
});

// Get lint results
const lint = await fetch(`/api/validation/runs/${runId}/lint`)
  .then(res => res.json());

console.log('Lint Summary:');
lint.summary.forEach(summary => {
  console.log(`  ${summary.validator}: ${summary.total_violations} violations`);
});

console.log('Lint Violations:');
lint.violations.forEach(violation => {
  console.log(`  ${violation.file_path}:${violation.line_number} - ${violation.code}`);
});
```

### Example React Component

```typescript
import { useEffect, useState } from 'react';

function ValidationDashboard() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [runDetails, setRunDetails] = useState(null);

  // Load runs on mount
  useEffect(() => {
    fetch('/api/validation/runs?limit=20')
      .then(res => res.json())
      .then(setRuns);
  }, []);

  // Load details for selected run
  const selectRun = (runId) => {
    setSelectedRun(runId);

    // Fetch all data for this run in parallel
    Promise.all([
      fetch(`/api/validation/runs/${runId}/tests`).then(r => r.json()),
      fetch(`/api/validation/runs/${runId}/lint`).then(r => r.json()),
      fetch(`/api/validation/runs/${runId}/coverage`).then(r => r.json()),
    ]).then(([tests, lint, coverage]) => {
      setRunDetails({ tests, lint, coverage });
    });
  };

  return (
    <div>
      <h1>Validation Dashboard</h1>

      <div className="runs-list">
        <h2>Recent Runs</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Time</th>
              <th>Branch</th>
              <th>Status</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {runs.map(run => (
              <tr
                key={run.id}
                onClick={() => selectRun(run.id)}
                className={selectedRun === run.id ? 'selected' : ''}
              >
                <td>{run.id}</td>
                <td>{new Date(run.timestamp).toLocaleString()}</td>
                <td>{run.git_branch}</td>
                <td className={run.passed ? 'pass' : 'fail'}>
                  {run.passed ? 'PASS' : 'FAIL'}
                </td>
                <td>{(run.duration_seconds / 60).toFixed(1)}m</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {runDetails && (
        <div className="run-details">
          <h2>Run #{selectedRun} Details</h2>

          <section className="tests">
            <h3>Tests ({runDetails.tests.length})</h3>
            <ul>
              {runDetails.tests.map(test => (
                <li key={test.id}>
                  <span className={test.passed ? 'pass' : 'fail'}>
                    {test.passed ? '✓' : '✗'}
                  </span>
                  {test.test_suite}::{test.test_name}
                </li>
              ))}
            </ul>
          </section>

          <section className="lint">
            <h3>Lint Results</h3>
            {runDetails.lint.summary.map(summary => (
              <div key={summary.validator}>
                <h4>{summary.validator}</h4>
                <p>{summary.total_violations} violations</p>
              </div>
            ))}
          </section>

          <section className="coverage">
            <h3>Coverage</h3>
            {runDetails.coverage.map(cov => (
              <p key={cov.execution_id}>
                {cov.total_coverage}% coverage
              </p>
            ))}
          </section>
        </div>
      )}
    </div>
  );
}

export default ValidationDashboard;
```

---

## 5. Common Scenarios

### Scenario 1: Process a Tool Output Immediately

```python
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

# You have fresh output from a linter
output = subprocess.run(["flake8", "module.py"], capture_output=True, text=True).stdout

# Parse it immediately
parser = LintParser()
parsed = parser.parse_flake8_output(output, Path("."))

# Use the parsed data
print(f"Found {parsed.total_violations} violations")
for fv in parsed.file_violations:
    print(f"\nFile: {fv.file_path}")
    for v in fv.violations:
        print(f"  {v['line']}:{v['code']} {v['message']}")
```

### Scenario 2: Store Parsed Data for Later Analysis

```python
from anvil.parsers.lint_parser import LintParser
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_persistence import StatisticsPersistence
from pathlib import Path

# Parse
parser = LintParser()
parsed = parser.parse_flake8_output(output, Path("."))

# Store
db = StatisticsDatabase(".anvil/execution.db")
persistence = StatisticsPersistence(db)
persistence.save_lint_summary(parsed)
persistence.save_lint_violations(parsed)

# Later: Query
from anvil.storage.statistics_queries import StatisticsQueryEngine
query = StatisticsQueryEngine(db)
violations = query.get_lint_violations(run_id=1)
print(f"Stored and retrieved {len(violations)} violations")
```

### Scenario 3: Validate Tool Output Against Expected

```python
from anvil.validators.adapters import validate_flake8_parser
from verdict.validator import OutputValidator
import yaml

# Get actual output
actual = validate_flake8_parser(tool_output)

# Load expected output
with open("expected_output.yaml") as f:
    expected = yaml.safe_load(f)

# Validate
validator = OutputValidator()
is_valid, differences = validator.validate(actual, expected)

if is_valid:
    print("✓ Output matches expected")
else:
    print("✗ Output differs:")
    for diff in differences:
        print(f"  - {diff}")
```

### Scenario 4: Build a Report from Database

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine
from datetime import datetime, timedelta

db = StatisticsDatabase(".anvil/execution.db")
query = StatisticsQueryEngine(db)

# Get runs from last week
week_ago = datetime.now() - timedelta(days=7)
runs = query.get_validation_runs(limit=100)
recent_runs = [r for r in runs if datetime.fromisoformat(r.timestamp) > week_ago]

# Generate report
passed = sum(1 for r in recent_runs if r.passed)
failed = sum(1 for r in recent_runs if not r.passed)
total = len(recent_runs)

print(f"Weekly Report ({total} runs)")
print(f"  Passed: {passed} ({100*passed/total:.1f}%)")
print(f"  Failed: {failed} ({100*failed/total:.1f}%)")

# Per-validator summary
all_validators = {}
for run in recent_runs:
    summaries = query.get_lint_summary(run_id=run.id)
    for summary in summaries:
        if summary.validator not in all_validators:
            all_validators[summary.validator] = {'total': 0, 'violations': 0}
        all_validators[summary.validator]['total'] += 1
        all_validators[summary.validator]['violations'] += summary.total_violations

print("\nLint Summary:")
for validator, stats in all_validators.items():
    avg_violations = stats['violations'] / stats['total'] if stats['total'] > 0 else 0
    print(f"  {validator}: {avg_violations:.1f} violations/run (avg)")
```

### Scenario 5: Monitor Trends Over Time

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine
from datetime import datetime, timedelta
import statistics

db = StatisticsDatabase(".anvil/execution.db")
query = StatisticsQueryEngine(db)

# Get all runs
all_runs = query.get_validation_runs(limit=1000)

# Group by week
from collections import defaultdict
by_week = defaultdict(list)

for run in all_runs:
    run_date = datetime.fromisoformat(run.timestamp)
    week_key = run_date.strftime("%Y-W%W")
    by_week[week_key].append(run)

# Calculate trends
print("Pass Rate by Week:")
for week, runs in sorted(by_week.items()):
    passed = sum(1 for r in runs if r.passed)
    total = len(runs)
    pass_rate = 100 * passed / total if total > 0 else 0
    print(f"  {week}: {pass_rate:.1f}% ({passed}/{total})")

# Duration trend
print("\nAverage Duration by Week:")
for week, runs in sorted(by_week.items()):
    durations = [r.duration_seconds for r in runs if r.duration_seconds]
    if durations:
        avg_duration = statistics.mean(durations)
        print(f"  {week}: {avg_duration:.1f}s")
```

---

## Summary

| Task | Method | Code |
|------|--------|------|
| Parse tool output | Direct parser | `LintParser().parse_flake8_output(text)` |
| Store parsed data | StatisticsPersistence | `persistence.save_lint_summary(data)` |
| Query database | StatisticsQueryEngine | `query.get_lint_violations(run_id=1)` |
| Validate output | Verdict adapter + validator | `validate_flake8_parser(text)` |
| Access via API | FastAPI endpoints | `GET /api/validation/runs/{id}/lint` |
| Frontend display | React components | `useEffect(() => fetch(...))` |

Choose the method that fits your use case!
