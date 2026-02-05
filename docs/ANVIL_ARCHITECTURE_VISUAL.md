# Anvil Data Flow - Visual Architecture

## Complete Data Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ANVIL DATA PROCESSING PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────┘

TIER 1: INPUT
════════════════════════════════════════════════════════════════════════════════
  Raw Tool Output (String)
  ├─ "error: cannot format module"  (from black)
  ├─ "module.py:10:1: E501 line too long"  (from flake8)
  ├─ "isort would reformat ..."  (from isort)
  └─ "===== 10 passed in 2.3s ====="  (from pytest)


TIER 2: PARSING (Anvil Parsers)
════════════════════════════════════════════════════════════════════════════════
  ┌────────────────────────────────────────────────────────────────┐
  │ LintParser                   │ PytestParser │ CoverageParser   │
  ├────────────────────────────────────────────────────────────────┤
  │ parse_black_output()         │ parse()      │ parse()          │
  │ parse_flake8_output()        │              │                  │
  │ parse_isort_output()         │              │                  │
  └────────────────────────────────────────────────────────────────┘
                              ↓
  Parsed Data Objects (LintData, TestData, CoverageData)
  ├─ validator: "black"
  ├─ total_violations: 5
  ├─ errors: 2
  ├─ by_code: {"E501": 3, "W292": 2}
  ├─ file_violations: [...]
  └─ ...


TIER 3A: STORAGE (Optional - Anvil Database)
════════════════════════════════════════════════════════════════════════════════
  StatisticsPersistence
         ↓
  ┌─────────────────────────────────────────────────────────┐
  │        SQLite Database (.anvil/execution.db)            │
  ├─────────────────────────────────────────────────────────┤
  │ Table: validation_runs                                  │
  │ ├─ id, timestamp, git_branch, git_commit, passed       │
  │                                                         │
  │ Table: test_case_records                                │
  │ ├─ run_id, test_name, test_suite, passed, duration    │
  │                                                         │
  │ Table: lint_summary                                     │
  │ ├─ run_id, validator, total_violations, errors, ...   │
  │                                                         │
  │ Table: lint_violations                                  │
  │ ├─ run_id, file_path, line_number, code, message      │
  │                                                         │
  │ Table: coverage_summary                                 │
  │ ├─ run_id, total_coverage, covered_statements         │
  └─────────────────────────────────────────────────────────┘
         ↓
  StatisticsQueryEngine (Retrieve via get_*, query methods)


TIER 3B: VALIDATION (Verdict)
════════════════════════════════════════════════════════════════════════════════
  ┌────────────────────────────────────────────────────────┐
  │         Verdict Adapters (Convert to Dict)             │
  │  validate_black_parser()                               │
  │  validate_flake8_parser()                              │
  │  validate_isort_parser()                               │
  └────────────────────────────────────────────────────────┘
         ↓
  LintData → dict conversion
  ├─ validator: "black"
  ├─ total_violations: 5
  ├─ errors: 2
  ├─ by_code: {"E501": 3, "W292": 2}
  └─ file_violations: [...]

         ↓ [Actual Output]
  ┌────────────────────────────────────────────────────────┐
  │        Verdict OutputValidator                         │
  │                                                        │
  │  actual ←→ expected                                    │
  │  (deep dict comparison)                               │
  └────────────────────────────────────────────────────────┘
         ↓
  Validation Result: PASS/FAIL
  ├─ differences: []  (if pass)
  └─ differences: ["Missing field 'errors'"]  (if fail)


TIER 4: QUERYING & VISUALIZATION
════════════════════════════════════════════════════════════════════════════════
  ┌─────────────────────────────────────┐
  │  StatisticsQueryEngine              │
  │  (Query stored parsed data)         │
  ├─────────────────────────────────────┤
  │ get_validation_runs()               │
  │ get_test_case_records()             │
  │ get_lint_violations()               │
  │ get_coverage_summary()              │
  │ get_validator_run_records()         │
  └─────────────────────────────────────┘
         ↓
  ┌────────────────────────────────────────────┐
  │  Lens Backend (REST API)                   │
  ├────────────────────────────────────────────┤
  │ GET /api/validation/runs                   │
  │ GET /api/validation/runs/{id}/tests        │
  │ GET /api/validation/runs/{id}/lint         │
  │ GET /api/validation/runs/{id}/coverage     │
  └────────────────────────────────────────────┘
         ↓
  ┌────────────────────────────────────────────┐
  │  Lens Frontend (React)                     │
  ├────────────────────────────────────────────┤
  │ ValidationRunsTable                        │
  │ TestResultsViewer                          │
  │ LintViolationsPanel                        │
  │ CoverageSummary                            │
  └────────────────────────────────────────────┘
         ↓
  📊 User-Facing Visualization
```

---

## Verdict Execution Flow (Detailed)

```
VERDICT RUNNER
══════════════════════════════════════════════════════════════════════════════

1. LOAD CONFIGURATION
   ↓
   config.yaml
   ├─ validators:
   │  ├─ black:
   │  │  ├─ callable: anvil.validators.adapters.validate_black_parser
   │  │  └─ root: cases/black_cases
   │  ├─ flake8:
   │  │  ├─ callable: anvil.validators.adapters.validate_flake8_parser
   │  │  └─ root: cases/flake8_cases
   │  └─ ...

2. DISCOVER TEST CASES
   ↓
   cases/black_cases/
   ├─ black_single_file.yaml
   ├─ black_multiline_errors.yaml
   └─ ...

   For each: Load case definition, input file, expected output file

3. FOR EACH TEST CASE → EXECUTE
   ↓
   ┌─────────────────────────────────────────────────────┐
   │ Test: black_single_file                             │
   ├─────────────────────────────────────────────────────┤
   │                                                     │
   │ STEP 1: Read Input File                            │
   │ ═══════════════════════════════════════════════════ │
   │ cases/black_cases/inputs/black_single_file.txt:    │
   │                                                    │
   │   error: cannot format module: Black does not     │
   │   support Python 3.7                              │
   │                                                    │
   │ input_text = "error: cannot format..."            │
   │                                                     │
   │ STEP 2: Call Anvil Adapter                         │
   │ ═══════════════════════════════════════════════════ │
   │                                                    │
   │ TargetExecutor.execute(                           │
   │   callable_path="anvil.validators.adapters.      │
   │                   validate_black_parser",        │
   │   input_text="error: cannot format..."           │
   │ )                                                  │
   │                                                    │
   │ → Imports: validate_black_parser function        │
   │ → Calls: validate_black_parser(input_text)       │
   │                                                    │
   │ Inside adapter:                                   │
   │   parser = LintParser()                          │
   │   lint_data = parser.parse_black_output(...)     │
   │   return dict(lint_data)                         │
   │                                                    │
   │ → Returns: {                                       │
   │     "validator": "black",                        │
   │     "total_violations": 1,                       │
   │     "errors": 1,                                 │
   │     "warnings": 0,                               │
   │     "by_code": {"E901": 1},                      │
   │     "file_violations": []                        │
   │   }                                               │
   │                                                    │
   │ actual_output = {...}                             │
   │                                                     │
   │ STEP 3: Read Expected Output File                 │
   │ ═══════════════════════════════════════════════════ │
   │                                                    │
   │ cases/black_cases/outputs/expected_output.yaml:  │
   │                                                    │
   │   validator: black                               │
   │   total_violations: 1                            │
   │   errors: 1                                      │
   │   warnings: 0                                    │
   │   by_code:                                       │
   │     E901: 1                                      │
   │   file_violations: []                            │
   │                                                    │
   │ expected_output = {...}                           │
   │                                                     │
   │ STEP 4: Validate (Compare)                        │
   │ ═══════════════════════════════════════════════════ │
   │                                                    │
   │ OutputValidator.validate(                        │
   │   actual=actual_output,                          │
   │   expected=expected_output                       │
   │ )                                                  │
   │                                                    │
   │ → Deep dict comparison                           │
   │ → Check all keys from expected exist in actual  │
   │ → Check all values match                        │
   │ → Allow extra keys in actual (partial match)    │
   │                                                    │
   │ Comparison:                                      │
   │   actual.validator == expected.validator        │
   │   ✓ "black" == "black"                           │
   │                                                    │
   │   actual.total_violations == expected.total...  │
   │   ✓ 1 == 1                                        │
   │                                                    │
   │   actual.errors == expected.errors               │
   │   ✓ 1 == 1                                        │
   │                                                    │
   │ differences = []                                  │
   │ is_valid = True                                   │
   │                                                     │
   │ STEP 5: Record Result                            │
   │ ═══════════════════════════════════════════════════ │
   │                                                    │
   │ result = TestResult(                             │
   │   test_name="black_single_file",                │
   │   suite_name="black",                           │
   │   passed=True,                                  │
   │   differences=[]                                │
   │ )                                                │
   │                                                    │
   └─────────────────────────────────────────────────────┘

4. AGGREGATE & REPORT
   ↓
   Summary:
   ├─ Suite: black (5 tests)
   │  ├─ black_single_file.yaml ✓ PASS
   │  ├─ black_multiline_errors.yaml ✓ PASS
   │  ├─ black_json_output.yaml ✓ PASS
   │  ├─ black_unicode.yaml ✓ PASS
   │  └─ black_no_errors.yaml ✓ PASS
   │
   ├─ Suite: flake8 (5 tests)
   │  ├─ flake8_single_error.yaml ✓ PASS
   │  ├─ flake8_multiline.yaml ✗ FAIL (missing field 'warnings')
   │  └─ ...
   │
   └─ Overall: 14 passed, 1 failed
```

---

## How Verdict Gets Parsed Data from Anvil

### Method 1: Direct Parser Call (for Validation)

```
Verdict Adapter
    ↓
Calls LintParser.parse_black_output()
    ↓
Returns LintData object
    ↓
Converts to dict
    ↓
Returns to Verdict Validator
```

### Method 2: Database Query (for Analysis)

```
After Verdict Runs:
    ↓
StatisticsPersistence saves to .anvil/execution.db
    ↓
StatisticsQueryEngine queries database
    ↓
Returns ValidationRun, TestCaseRecord, LintSummary, etc.
    ↓
Exposed via Lens REST API
    ↓
Displayed in Lens Frontend
```

---

## Data Structure Example

### Input
```
Raw Black Output
════════════════════════════════════════
error: cannot format module: Black does not support Python 3.7
Oh no! 💥 💔 💥
error: 2 files failed to reformat.
```

### Parsing Result
```
LintData Object
════════════════════════════════════════
validator:        "black"
total_violations: 2
errors:           2
warnings:         0
info:             0
files_scanned:    0
by_code:          {"E901": 2}
file_violations:  []
```

### Adapted to Dict
```
Python Dict (returned by adapter)
════════════════════════════════════════
{
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

### Expected Output
```
YAML File (expected_output.yaml)
════════════════════════════════════════
validator: black
total_violations: 2
errors: 2
warnings: 0
info: 0
files_scanned: 0
by_code:
  E901: 2
file_violations: []
```

### Validation
```
Comparison Result
════════════════════════════════════════
✓ validator match
✓ total_violations match
✓ errors match
✓ warnings match
✓ info match
✓ files_scanned match
✓ by_code match
✓ file_violations match

Result: PASS
```

### Stored in Database
```
SQLite Tables
════════════════════════════════════════
validation_runs table:
  id=1, timestamp=2026-02-04T18:16:52, git_branch=main, passed=1

lint_summary table:
  run_id=1, validator=black, total_violations=2, errors=2, warnings=0

lint_violations table:
  (none, no specific file violations)
```

### Queried via API
```
REST API Call
════════════════════════════════════════
GET /api/validation/runs/1/lint

Response:
{
  "summary": [{
    "run_id": 1,
    "validator": "black",
    "total_violations": 2,
    "errors": 2,
    "warnings": 0
  }],
  "violations": []
}
```

### Displayed in Frontend
```
React Component
════════════════════════════════════════
┌─────────────────────────────────────┐
│  Run #1 - 2026-02-04 18:16:52      │
├─────────────────────────────────────┤
│  Branch: main                       │
│  Status: FAILED                     │
│                                     │
│  Lint Results:                      │
│  ├─ black:                          │
│  │  ├─ Total Violations: 2          │
│  │  ├─ Errors: 2                    │
│  │  ├─ Warnings: 0                  │
│  │  └─ Files Scanned: 0             │
│  │                                  │
│  └─ Violations: (none)              │
└─────────────────────────────────────┘
```

---

## Summary: Three Ways to Access Parsed Data

| Method | Purpose | Code Example |
|--------|---------|--------------|
| **Direct Parser** | Parse tool output in real-time | `parser.parse_black_output(text)` |
| **Database Query** | Retrieve historical parsed data | `db.get_lint_violations(run_id=1)` |
| **REST API** | Access parsed data from frontend | `GET /api/validation/runs/1/lint` |
| **Verdict Adapter** | Convert parsed data to dict for validation | `validate_black_parser(input_text)` |

Each method serves a different use case in the data pipeline!
