# How Anvil Handles Parsed Data & How Verdict Retrieves It

## Overview

Anvil is a **data parsing and storage system** that:
1. **Parses** tool outputs (black, flake8, isort, pytest, etc.)
2. **Stores** the parsed data in SQLite databases
3. **Provides** database APIs for querying the parsed data

Verdict is a **validation tool** that:
1. **Calls** Anvil parsers through adapters
2. **Compares** actual output with expected output
3. **Reports** validation results

---

## Part 1: How Anvil Handles Parsed Data

### 1.1 Data Flow: Input → Parse → Store

```
Raw Tool Output (string)
    ↓
Anvil Parser (e.g., LintParser)
    ↓
Parsed Data Object (e.g., LintData)
    ↓
Database Storage (ExecutionDatabase/StatisticsDatabase)
    ↓
SQLite Tables
    ↓
Query APIs (get_*, retrieve_*)
```

### 1.2 Parsing Layer

**Location**: `anvil/parsers/`

Anvil has specialized parsers for each tool:

```
parsers/
  lint_parser.py       # Parses black, flake8, isort output
  pytest_parser.py     # Parses pytest output
  coverage_parser.py   # Parses coverage data
  git_parser.py        # Parses git information
```

**Example: Black Parser**

```python
from anvil.parsers.lint_parser import LintParser

parser = LintParser()
input_text = """
error: cannot format module: Black does not support Python 3.7
"""

# Parse the output
lint_data = parser.parse_black_output(input_text, Path("."))

# Result is a LintData object with:
# - validator: "black"
# - total_violations: 1
# - errors: 1
# - file_violations: [...]
# - by_code: {"E901": 1}
```

### 1.3 Storage Layer - Two Database Types

Anvil uses **two separate databases** with different purposes:

#### A. ExecutionDatabase (Execution History)
**File**: `anvil/storage/execution_schema.py`
**Database**: `.anvil/history.db`
**Purpose**: Track test/validator execution history for selective execution

**Tables**:
```sql
execution_history
├── id, execution_id, entity_id, entity_type
├── timestamp, status, duration, space, metadata

execution_rules
├── id, name, criteria, enabled
├── threshold, window, groups, executor_config

entity_statistics
├── id, entity_id, entity_type
├── total_runs, passed, failed, skipped
├── failure_rate, avg_duration, last_run

execution_history (detailed)
├── execution_id, entity_id, entity_type
├── timestamp, status, duration
```

**Used by**: Pytest executor for selective test execution

#### B. StatisticsDatabase (Parsed Results)
**File**: `anvil/storage/statistics_database.py`
**Database**: `.anvil/statistics.db` or `.anvil/execution.db`
**Purpose**: Store parsed validation results

**Tables**:
```sql
validation_runs
├── id, timestamp, git_commit, git_branch
├── incremental, passed, duration_seconds

test_case_records
├── id, run_id, test_name, test_suite
├── passed, skipped, duration_seconds, failure_message

validator_run_records
├── id, run_id, validator_name
├── passed, error_count, warning_count, files_checked

file_validation_records
├── id, run_id, validator_name
├── file_path, error_count, warning_count

coverage_summary
├── id, execution_id, timestamp
├── total_coverage, files_analyzed, total_statements, covered_statements

coverage_history
├── id, execution_id, file_path, timestamp
├── total_statements, covered_statements, coverage_percentage

lint_summary
├── id, execution_id, timestamp, validator
├── files_scanned, total_violations, errors, warnings, info, by_code

lint_violations
├── id, execution_id, file_path, line_number, column_number
├── severity, code, message, validator, timestamp
```

### 1.4 Data Persistence - StatisticsPersistence

**Location**: `anvil/storage/statistics_persistence.py`

This class handles saving parsed data to the StatisticsDatabase:

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_persistence import StatisticsPersistence

# Create database
db = StatisticsDatabase(".anvil/statistics.db")
persistence = StatisticsPersistence(db)

# Parse data from tool output
parser = LintParser()
lint_data = parser.parse_flake8_output(output_text, Path("."))

# Save to database
persistence.save_lint_summary(lint_data)
persistence.save_lint_violations(lint_data)
```

---

## Part 2: How Verdict Calls Anvil & Retrieves Data

### 2.1 The Verdict → Anvil Integration Flow

```
Verdict CLI
    ↓
Load Config (config.yaml)
    ↓
Find Test Cases
    ↓
For each test case:
    ├─ Read input file (e.g., black_output.txt)
    ├─ Call Anvil adapter function
    │  └─ Adapter calls Anvil parser
    │     └─ Parser returns parsed dict
    ├─ Read expected output file (e.g., expected_output.yaml)
    ├─ Compare actual vs expected
    └─ Report pass/fail
```

### 2.2 Verdict Configuration

**File**: `anvil/tests/validation/config.yaml`

```yaml
validators:
  black:
    callable: anvil.validators.adapters.validate_black_parser
    root: cases/black_cases
  flake8:
    callable: anvil.validators.adapters.validate_flake8_parser
    root: cases/flake8_cases
  isort:
    callable: anvil.validators.adapters.validate_isort_parser
    root: cases/isort_cases
```

### 2.3 Verdict Calls Anvil Through Adapters

**Location**: `anvil/validators/adapters.py`

Adapters implement the interface: `str → dict`

```python
def validate_black_parser(input_text: str) -> dict:
    """
    Verdict adapter for black parser.

    Takes raw black output and returns parsed dict.
    """
    # 1. Create parser
    parser = LintParser()

    # 2. Parse the input
    lint_data = parser.parse_black_output(input_text, Path("."))

    # 3. Convert to dictionary
    return {
        "validator": lint_data.validator,
        "total_violations": lint_data.total_violations,
        "files_scanned": lint_data.files_scanned,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violations": fv.violations,
                "validator": fv.validator,
            }
            for fv in lint_data.file_violations
        ],
    }
```

### 2.4 Verdict Executor Calls the Adapter

**Location**: `verdict/executor.py`

```python
class TargetExecutor:
    def execute(self, callable_path: str, input_text: str) -> dict:
        """
        Execute adapter function and return parsed dict.

        Flow:
        1. Import the adapter: "anvil.validators.adapters.validate_black_parser"
        2. Call it with input_text
        3. Get back parsed dictionary
        """
        # Dynamically import the callable
        callable_func = self._import_callable(callable_path)

        # Execute: input_text → dict
        result = callable_func(input_text)

        return result
```

### 2.5 Verdict Validator Compares Results

**Location**: `verdict/validator.py`

```python
class OutputValidator:
    def validate(self, actual: dict, expected: dict) -> Tuple[bool, List[str]]:
        """
        Compare actual parsed output with expected output.

        Args:
            actual: Dict from Anvil adapter
            expected: Dict from expected_output.yaml

        Returns:
            (is_valid, differences)
        """
        # Deep comparison of dictionaries
        differences = []
        self._compare_dicts(actual, expected, "", differences)

        is_valid = len(differences) == 0
        return is_valid, differences
```

### 2.6 Test Case Structure

```
cases/black_cases/
├── black_single_file.yaml          # Test case definition
├── inputs/
│   └── black_single_file.txt       # Raw black output (input to adapter)
├── outputs/
│   └── expected_output.yaml        # Expected parsed output
```

**Test Case File** (`black_single_file.yaml`):
```yaml
name: black_single_file
description: Parse single file black output
input: inputs/black_single_file.txt
output: outputs/expected_output.yaml
```

**Input** (`inputs/black_single_file.txt`):
```
error: cannot format module: Black does not support Python 3.7
```

**Expected Output** (`outputs/expected_output.yaml`):
```yaml
validator: black
total_violations: 1
errors: 1
warnings: 0
info: 0
files_scanned: 0
by_code:
  E901: 1
file_violations: []
```

### 2.7 Verdict Execution Flow

```python
# verdict/runner.py
def run_suite(self, suite_name: str) -> List[TestResult]:
    """
    1. Load test cases for suite
    2. For each test case:
       a. Read input file
       b. Execute adapter (calls Anvil parser)
       c. Read expected output
       d. Compare actual vs expected
       e. Return result
    """
    test_cases = self.test_case_loader.load_cases(suite_name)

    for test_case in test_cases:
        # 1. Get input text
        input_text = test_case.load_input()

        # 2. Call Anvil adapter → get parsed dict
        actual_output = self.executor.execute(
            callable_path="anvil.validators.adapters.validate_black_parser",
            input_text=input_text
        )

        # 3. Get expected output
        expected_output = test_case.load_expected_output()

        # 4. Validate
        is_valid, differences = self.validator.validate(
            actual_output,
            expected_output
        )

        # 5. Record result
        result = TestResult(
            test_name=test_case.name,
            suite_name=suite_name,
            passed=is_valid,
            differences=differences
        )
        results.append(result)
```

---

## Part 3: Visualizing Parsed Data

### 3.1 Query Methods Available

**StatisticsDatabase** provides query methods:

```python
from anvil.storage.statistics_database import StatisticsDatabase, StatisticsQueryEngine

db = StatisticsDatabase(".anvil/statistics.db")
query_engine = StatisticsQueryEngine(db)

# Query by run
runs = query_engine.get_validation_runs(limit=10)

# Query test results
tests = query_engine.get_test_case_records(run_id=1)

# Query lint results
lint_summary = query_engine.get_lint_summary(run_id=1)
violations = query_engine.get_lint_violations(run_id=1, code="E501")

# Query coverage
coverage = query_engine.get_coverage_summary(run_id=1)

# Query validators
validators = query_engine.get_validator_run_records(run_id=1)
file_results = query_engine.get_file_validation_records(run_id=1)
```

### 3.2 Programmatic Access Example

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine

# Connect to database
db = StatisticsDatabase(".anvil/execution.db")
query_engine = StatisticsQueryEngine(db)

# Get recent validation run
runs = query_engine.get_validation_runs(limit=1)
run = runs[0]

print(f"Run: {run.id}")
print(f"Branch: {run.git_branch}")
print(f"Status: {'PASS' if run.passed else 'FAIL'}")

# Get test results for this run
tests = query_engine.get_test_case_records(run_id=run.id)
for test in tests:
    status = "PASS" if test.passed else "FAIL"
    print(f"  [{status}] {test.test_suite}::{test.test_name}")

# Get lint violations
violations = query_engine.get_lint_violations(run_id=run.id)
for violation in violations:
    print(f"  {violation.file_path}:{violation.line_number}")
    print(f"    [{violation.severity}] {violation.code}: {violation.message}")
```

### 3.3 REST API Access (via Lens Backend)

**File**: `lens/backend/server.py`

The Lens backend exposes Anvil data via REST endpoints:

```python
from fastapi import FastAPI
from anvil.storage.statistics_database import StatisticsDatabase

app = FastAPI()
db = StatisticsDatabase(".anvil/execution.db")

@app.get("/api/validation/runs")
async def get_validation_runs(limit: int = 10):
    """Get recent validation runs"""
    query_engine = StatisticsQueryEngine(db)
    runs = query_engine.get_validation_runs(limit=limit)
    return [run.to_dict() for run in runs]

@app.get("/api/validation/runs/{run_id}/tests")
async def get_run_tests(run_id: int):
    """Get test results for a run"""
    query_engine = StatisticsQueryEngine(db)
    tests = query_engine.get_test_case_records(run_id=run_id)
    return [test.to_dict() for test in tests]

@app.get("/api/validation/runs/{run_id}/lint")
async def get_run_lint(run_id: int):
    """Get lint results for a run"""
    query_engine = StatisticsQueryEngine(db)
    summary = query_engine.get_lint_summary(run_id=run_id)
    violations = query_engine.get_lint_violations(run_id=run_id)
    return {
        "summary": [s.to_dict() for s in summary],
        "violations": [v.to_dict() for v in violations]
    }
```

### 3.4 Frontend Visualization (React)

**File**: `lens/frontend/src/pages/ValidationResults.tsx`

```typescript
import { useEffect, useState } from 'react';

export function ValidationResults() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [tests, setTests] = useState([]);

  // Fetch validation runs from Anvil via REST API
  useEffect(() => {
    fetch('/api/validation/runs?limit=10')
      .then(res => res.json())
      .then(data => setRuns(data));
  }, []);

  // Fetch tests for selected run
  const selectRun = (run) => {
    setSelectedRun(run);
    fetch(`/api/validation/runs/${run.id}/tests`)
      .then(res => res.json())
      .then(data => setTests(data));
  };

  return (
    <div>
      <h2>Validation Runs</h2>
      <table>
        <tbody>
          {runs.map(run => (
            <tr key={run.id} onClick={() => selectRun(run)}>
              <td>{run.id}</td>
              <td>{run.timestamp}</td>
              <td>{run.git_branch}</td>
              <td>{run.passed ? 'PASS' : 'FAIL'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedRun && (
        <div>
          <h3>Test Results for Run {selectedRun.id}</h3>
          <table>
            <tbody>
              {tests.map(test => (
                <tr key={test.id}>
                  <td>{test.test_suite}</td>
                  <td>{test.test_name}</td>
                  <td>{test.passed ? 'PASS' : 'FAIL'}</td>
                  <td>{test.duration_seconds.toFixed(2)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

---

## Part 4: Complete Example - Black Parser

### Step 1: Raw Input
```
error: cannot format module: Black does not support Python 3.7
Oh no! 💥 💔 💥
error: 2 files failed to reformat.
```

### Step 2: Anvil Parser Processes It
```python
parser = LintParser()
lint_data = parser.parse_black_output(raw_input, Path("."))
```

### Step 3: LintData Object Created
```
LintData(
  validator="black",
  total_violations=2,
  errors=2,
  warnings=0,
  info=0,
  files_scanned=0,
  by_code={"E901": 2},
  file_violations=[]
)
```

### Step 4: Verdict Adapter Converts to Dict
```python
def validate_black_parser(input_text: str) -> dict:
    parser = LintParser()
    lint_data = parser.parse_black_output(input_text, Path("."))
    return {
        "validator": "black",
        "total_violations": 2,
        "errors": 2,
        "warnings": 0,
        "info": 0,
        "files_scanned": 0,
        "by_code": {"E901": 2},
        "file_violations": []
    }
```

### Step 5: Verdict Validator Compares
```python
actual = {
    "validator": "black",
    "total_violations": 2,
    "errors": 2,
    ...
}

expected = {
    "validator": "black",
    "total_violations": 2,
    "errors": 2,
    ...
}

# Result: PASS (actual matches expected)
```

### Step 6: Data Stored in Database (Optional)
```python
persistence = StatisticsPersistence(db)
persistence.save_lint_summary(lint_data)
persistence.save_lint_violations(lint_data)

# Now queryable via:
violations = query_engine.get_lint_violations(run_id=1)
```

### Step 7: Visualized in Frontend
```
ValidationRuns Table:
┌────┬─────────────────┬────────┬────────┐
│ ID │ Timestamp       │ Branch │ Status │
├────┼─────────────────┼────────┼────────┤
│ 1  │ 2026-02-04...   │ main   │ FAIL   │
└────┴─────────────────┴────────┴────────┘

TestResults for Run 1:
┌──────────────────┬──────────────┬────────┐
│ Suite            │ Test         │ Status │
├──────────────────┼──────────────┼────────┤
│ black_cases      │ black_single │ PASS   │
└──────────────────┴──────────────┴────────┘

LintViolations for Run 1:
┌──────────────┬──────┬──────┐
│ File         │ Line │ Code │
├──────────────┼──────┼──────┤
│ module.py    │ 1    │ E901 │
│ module.py    │ 2    │ E901 │
└──────────────┴──────┴──────┘
```

---

## Summary

| Component | Role | Location |
|-----------|------|----------|
| **Anvil Parsers** | Parse tool outputs (black, flake8, etc.) | `anvil/parsers/` |
| **Anvil Adapters** | Convert parsed data to dicts for Verdict | `anvil/validators/adapters.py` |
| **Verdict Runner** | Execute test cases and compare outputs | `verdict/runner.py` |
| **Verdict Executor** | Dynamically call Anvil adapters | `verdict/executor.py` |
| **Verdict Validator** | Compare actual vs expected dicts | `verdict/validator.py` |
| **StatisticsDatabase** | Store parsed results in SQLite | `anvil/storage/statistics_database.py` |
| **StatisticsQueryEngine** | Query parsed data from database | `anvil/storage/statistics_queries.py` |
| **Lens Backend** | Expose Anvil data via REST API | `lens/backend/server.py` |
| **Lens Frontend** | Visualize Anvil data in UI | `lens/frontend/src/` |

**Key Insight**: Anvil's parsed data flows through multiple layers - from parsing, to validation (with Verdict), to storage (in database), to querying, to visualization (in Lens).
