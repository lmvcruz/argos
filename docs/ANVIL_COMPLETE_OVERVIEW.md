# Anvil Data Handling - Complete Overview

## Quick Summary

**Anvil** parses tool outputs and stores the results. **Verdict** validates the parsing by comparing actual output against expected output. Together, they form a validation pipeline.

```
Tool Output → Anvil Parser → Parsed Data → Verdict Validator → Pass/Fail
                                  ↓
                           SQLite Database
                                  ↓
                              REST API
                                  ↓
                           React Frontend
```

---

## The Three Core Questions Answered

### 1. How does Anvil save the data to the database?

**Flow**: Parse → Convert to StorageModel → Insert into SQLite

```python
# Parsing
parser = LintParser()
lint_data = parser.parse_flake8_output(raw_output, Path("."))
# Result: LintData object with parsed information

# Storage
persistence = StatisticsPersistence(db)
persistence.save_lint_summary(lint_data)
persistence.save_lint_violations(lint_data)
# Result: Data inserted into SQLite tables
```

**Database Tables Created**:
- `validation_runs` - Overall run metadata
- `test_case_records` - Individual test results
- `lint_summary` - Aggregated lint results
- `lint_violations` - Detailed violation records
- `coverage_summary` - Coverage statistics
- `validator_run_records` - Validator execution results
- `file_validation_records` - Per-file results

### 2. How can we visualize the parsed data?

**Three methods**:

1. **Direct Query** (Python)
   ```python
   db = StatisticsDatabase(".anvil/execution.db")
   query = StatisticsQueryEngine(db)
   violations = query.get_lint_violations(run_id=1)
   ```

2. **REST API** (from Lens backend)
   ```
   GET /api/validation/runs
   GET /api/validation/runs/{id}/lint
   GET /api/validation/runs/{id}/coverage
   ```

3. **Frontend** (React component)
   ```typescript
   const [data, setData] = useState([]);
   useEffect(() => {
     fetch('/api/validation/runs/{id}/lint')
       .then(res => res.json())
       .then(setData);
   }, []);
   ```

### 3. How does Verdict call Anvil to get parsed data?

**Flow**: Test → Adapter → Parser → Dict → Comparison

```
Test Case (e.g., black_single_file.yaml)
    ↓
Read input file (e.g., black_output.txt)
    ↓
Call Verdict adapter:
    validate_black_parser(input_text)
    ↓ [Inside adapter]
    Create parser: LintParser()
    Parse: lint_data = parser.parse_black_output(input_text, Path("."))
    Convert: return dict(lint_data)
    ↓ [Back to Verdict]
Get actual output (dict)
    ↓
Read expected output file (expected_output.yaml)
    ↓
Compare: OutputValidator.validate(actual, expected)
    ↓
Result: PASS or FAIL
```

---

## Architecture Components

### Anvil Components

```
anvil/
├── parsers/                    # Parse tool outputs
│   ├── lint_parser.py         # Black, flake8, isort
│   ├── pytest_parser.py       # Pytest results
│   └── coverage_parser.py     # Coverage data
│
├── storage/                    # Store parsed data
│   ├── statistics_database.py    # SQLite schema
│   ├── statistics_persistence.py # Save to DB
│   └── statistics_queries.py     # Query from DB
│
├── validators/
│   └── adapters.py             # Convert parsed data to dicts
│
└── executors/                  # Run tests with history
    └── pytest_executor.py      # Pytest with database recording
```

### Verdict Components

```
verdict/
├── runner.py              # Orchestrate test execution
├── executor.py            # Call adapter functions
├── validator.py           # Compare actual vs expected
├── loader.py              # Load test cases
└── cli.py                 # Command-line interface
```

### Lens Components

```
lens/
├── backend/
│   └── server.py          # FastAPI REST endpoints
│
└── frontend/
    └── src/
        └── pages/
            └── ValidationResults.tsx  # React component
```

---

## Data Models

### LintData (from Anvil Parser)

```python
@dataclass
class LintData:
    validator: str                    # "black", "flake8", "isort"
    total_violations: int             # Total count
    errors: int                       # ERROR severity count
    warnings: int                     # WARNING severity count
    info: int                         # INFO severity count
    files_scanned: int                # Number of files
    by_code: Dict[str, int]          # Count by violation code
    file_violations: List[FileViolation]  # Per-file details
```

### ValidationRun (in Database)

```python
@dataclass
class ValidationRun:
    id: int
    timestamp: str                    # ISO format
    git_commit: str
    git_branch: str
    incremental: bool
    passed: bool                      # Overall status
    duration_seconds: float
```

### TestCaseRecord (in Database)

```python
@dataclass
class TestCaseRecord:
    id: int
    run_id: int                       # Foreign key to validation_run
    test_name: str
    test_suite: str
    passed: bool
    skipped: bool
    duration_seconds: float
    failure_message: Optional[str]
```

### LintSummary (in Database)

```python
@dataclass
class LintSummary:
    id: int
    run_id: int                       # Foreign key to validation_run
    validator: str                    # "black", "flake8", etc.
    files_scanned: int
    total_violations: int
    errors: int
    warnings: int
    info: int
    by_code: Dict[str, int]          # JSON stored in DB
```

---

## Complete Example: Black Parser Flow

### Input
```
Raw black output:
error: cannot format module: Black does not support Python 3.7
Oh no! 💥 💔 💥
error: 2 files failed to reformat.
```

### Step 1: Parse (Anvil)
```python
parser = LintParser()
parsed = parser.parse_black_output(input_text, Path("."))
# Result: LintData(validator="black", total_violations=2, errors=2, ...)
```

### Step 2: Store (Anvil)
```python
persistence = StatisticsPersistence(db)
persistence.save_lint_summary(parsed)
persistence.save_lint_violations(parsed)
# Tables updated: lint_summary, lint_violations
```

### Step 3: Adapt (Anvil)
```python
def validate_black_parser(input_text: str) -> dict:
    parser = LintParser()
    parsed = parser.parse_black_output(input_text, Path("."))
    return {
        "validator": "black",
        "total_violations": 2,
        "errors": 2,
        "warnings": 0,
        "info": 0,
        "by_code": {"E901": 2},
        ...
    }
```

### Step 4: Execute (Verdict)
```python
actual = validate_black_parser(input_text)
# Returns: {"validator": "black", "total_violations": 2, ...}
```

### Step 5: Validate (Verdict)
```python
expected = {"validator": "black", "total_violations": 2, ...}
is_valid, diffs = validator.validate(actual, expected)
# Result: is_valid = True, diffs = []
```

### Step 6: Query (Lens Backend)
```python
query = StatisticsQueryEngine(db)
violations = query.get_lint_violations(run_id=1)
# Returns: [LintViolation(...), LintViolation(...)]
```

### Step 7: Visualize (Lens Frontend)
```
Validation Run #1
├─ Branch: main
├─ Status: FAIL
└─ Lint Results
   └─ black: 2 violations (2 errors, 0 warnings)
```

---

## Database Schema (Simplified)

```sql
-- Run metadata
validation_runs
├─ id INTEGER PRIMARY KEY
├─ timestamp TEXT
├─ git_commit TEXT
├─ git_branch TEXT
├─ passed INTEGER (0/1)
└─ duration_seconds REAL

-- Test results
test_case_records
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ test_name TEXT
├─ test_suite TEXT
├─ passed INTEGER (0/1)
└─ duration_seconds REAL

-- Lint aggregates
lint_summary
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ validator TEXT
├─ total_violations INTEGER
├─ errors INTEGER
├─ warnings INTEGER
└─ by_code TEXT (JSON)

-- Lint details
lint_violations
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ file_path TEXT
├─ line_number INTEGER
├─ severity TEXT
├─ code TEXT
└─ message TEXT

-- Coverage
coverage_summary
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ total_coverage REAL
├─ files_analyzed INTEGER
└─ covered_statements INTEGER

-- Validators
validator_run_records
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ validator_name TEXT
├─ passed INTEGER (0/1)
├─ error_count INTEGER
└─ warning_count INTEGER

-- Per-file validation
file_validation_records
├─ id INTEGER PRIMARY KEY
├─ run_id INTEGER (FK to validation_runs)
├─ file_path TEXT
├─ validator_name TEXT
├─ error_count INTEGER
└─ warning_count INTEGER
```

---

## API Endpoints (Lens Backend)

```
GET /api/validation/runs
  └─ Returns: List[ValidationRun]

GET /api/validation/runs/{run_id}
  └─ Returns: ValidationRun

GET /api/validation/runs/{run_id}/tests
  └─ Returns: List[TestCaseRecord]

GET /api/validation/runs/{run_id}/lint
  └─ Returns: {summary: List[LintSummary], violations: List[LintViolation]}

GET /api/validation/runs/{run_id}/coverage
  └─ Returns: List[CoverageSummary]

GET /api/validation/runs/{run_id}/validators
  └─ Returns: List[ValidatorRunRecord]

GET /api/validation/runs/{run_id}/files
  └─ Returns: List[FileValidationRecord]
```

---

## Usage Patterns

### Pattern 1: Real-time Parsing
Use when you need immediate results without storage.

```python
from anvil.parsers.lint_parser import LintParser

parser = LintParser()
result = parser.parse_flake8_output(tool_output, Path("."))
# Use result directly, don't store
```

### Pattern 2: Parse and Store
Use when you want to keep historical records.

```python
from anvil.parsers.lint_parser import LintParser
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_persistence import StatisticsPersistence

parser = LintParser()
result = parser.parse_flake8_output(tool_output, Path("."))

db = StatisticsDatabase(".anvil/execution.db")
persistence = StatisticsPersistence(db)
persistence.save_lint_summary(result)
```

### Pattern 3: Validate with Verdict
Use when you want to validate against expected output.

```python
from anvil.validators.adapters import validate_flake8_parser
from verdict.validator import OutputValidator

actual = validate_flake8_parser(tool_output)
expected = load_expected_output()

validator = OutputValidator()
is_valid, diffs = validator.validate(actual, expected)
```

### Pattern 4: Query Historical Data
Use when you want to analyze past results.

```python
from anvil.storage.statistics_database import StatisticsDatabase
from anvil.storage.statistics_queries import StatisticsQueryEngine

db = StatisticsDatabase(".anvil/execution.db")
query = StatisticsQueryEngine(db)

runs = query.get_validation_runs(limit=10)
for run in runs:
    violations = query.get_lint_violations(run_id=run.id)
    print(f"Run {run.id}: {len(violations)} violations")
```

### Pattern 5: REST API Access
Use when you want to access from web/frontend.

```javascript
// Frontend code
const response = await fetch('/api/validation/runs/1/lint');
const data = await response.json();
console.log(`Found ${data.violations.length} violations`);
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `anvil/parsers/lint_parser.py` | Parse black, flake8, isort output |
| `anvil/parsers/pytest_parser.py` | Parse pytest output |
| `anvil/storage/statistics_database.py` | Database schema & CRUD |
| `anvil/storage/statistics_persistence.py` | Save parsed data to DB |
| `anvil/storage/statistics_queries.py` | Query parsed data from DB |
| `anvil/validators/adapters.py` | Convert parsed data to dicts |
| `verdict/executor.py` | Execute adapter functions |
| `verdict/validator.py` | Compare actual vs expected |
| `verdict/runner.py` | Orchestrate test execution |
| `lens/backend/server.py` | REST API endpoints |
| `lens/frontend/src/pages/` | React components |

---

## Decision Tree: Which Method to Use?

```
Do you have raw tool output?
├─ YES, need parsed data NOW
│  └─ Use: LintParser.parse_*() directly
│
├─ YES, need to store for later
│  └─ Use: LintParser.parse_*() + StatisticsPersistence.save_*()
│
└─ YES, need to validate correctness
   └─ Use: Verdict adapters + OutputValidator

Do you have stored parsed data?
├─ YES, need to retrieve it
│  └─ Use: StatisticsQueryEngine.get_*()
│
└─ YES, need to display it
   └─ Use: REST API or direct query

Do you have a running Lens backend?
├─ YES
│  └─ Use: Fetch from /api/validation/* endpoints
│
└─ NO
   └─ Use: Direct Python StatisticsQueryEngine
```

---

## Summary Table

| Layer | Component | Input | Processing | Output |
|-------|-----------|-------|-----------|--------|
| **Parse** | LintParser | Raw string (tool output) | Parse & extract | LintData object |
| **Adapt** | Adapters | Raw string | Call parser + convert | Python dict |
| **Validate** | OutputValidator | Actual dict, Expected dict | Compare | bool + differences |
| **Store** | Persistence | LintData object | Insert SQL | Rows in database |
| **Query** | QueryEngine | Query parameters | SQL SELECT | List of models |
| **Expose** | REST API | HTTP request | Query + format | JSON response |
| **Display** | React | Fetch response | Process & render | Web UI |

---

## Conclusion

Anvil provides a complete pipeline for:
1. **Parsing** tool outputs into structured data
2. **Storing** parsed data in a queryable database
3. **Validating** parsing correctness with Verdict
4. **Exposing** data via REST API
5. **Visualizing** results in a web interface

Choose the layer that fits your use case, or combine multiple layers for a complete solution!
