# Verdict - Generic Test Validation Tool - Specification & Implementation Plan

**Version**: 1.0
**Date**: February 3, 2026
**Purpose**: Standalone test validation framework for component validation

---

## 1. Overview

**Verdict** is a generic, configuration-driven test framework for validating components through input/output comparison testing. It is a standalone tool at the root of the Argos project, installable as a Python package and usable by any component (Anvil, Forge, Scout, etc.) as a third-party dependency.

Initial use case: validating Anvil parsers (black, flake8, isort), but designed to be generic for any testable component.

### Key Characteristics
- **Manual execution only** (not in pre-commit or automatic CI)
- **Flexible test case formats** (single file or folder structure)
- **Configuration-driven** test discovery and execution
- **Detailed logging** of test results
- **Parallel execution** support for performance (configured via max_workers)

---

## 2. File Format Decisions

### 2.1 Test Case Format: **YAML**

**Rationale**:
- More readable than JSON (supports comments, no quotes on keys)
- Simpler than TOML for nested structures
- Native support for multi-line strings (perfect for tool output)
- Wide Python ecosystem support (`pyyaml`)

### 2.2 Configuration Format: **YAML**

**Rationale**: Consistency with test case format

---

## 3. Test Case Structure

### 3.1 Single-File Test Case (Small I/O)

**Format**: `{test_name}.yaml`

```yaml
# Case metadata
name: "Black parser - single file violation"
description: "Test black output with one file needing reformatting"

# Input to component under test
input:
  type: "text"   # text | file_path
  content: |
    would reformat /home/user/project/file.py
    Oh no! 💥 💔 💥
    1 file would be reformatted.

# Expected output (structure depends on component being tested)
expected:
  total_violations: 1
  files_scanned: 1
  errors: 0
  warnings: 1
  info: 0
  by_code:
    BLACK001: 1
  file_violations:
    - file_path: "file.py"
      violation_count: 1
      violations:
        - line_number: 1
          severity: "WARNING"
          code: "BLACK001"
          message: "File would be reformatted by black"
```

### 3.2 Folder-Based Test Case (Large I/O)

**Structure**:
```
test_case_name/
├── input.txt             # Raw input to component
└── expected_output.yaml  # Expected output structure
```

**input.txt**:
```
./src/main.py:10:1: E501 line too long (120 > 100 characters)
./src/main.py:15:5: W291 trailing whitespace
./src/utils.py:5:1: F401 'os' imported but unused
```

**expected_output.yaml**:
```yaml
name: "Flake8 parser - multiple violations"
description: "Test flake8 output with various error codes"

# Expected output structure
total_violations: 3
files_scanned: 2
errors: 2
warnings: 1
info: 0
by_code:
  E501: 1
  W291: 1
  F401: 1
file_violations:
  - file_path: "src/main.py"
    violation_count: 2
  - file_path: "src/utils.py"
    violation_count: 1
```

---

## 4. Configuration File Structure

**File**: `anvil/tests/parser_validation/test_config.yaml`

```yaml
# Component Validation Test Configuration

# Global settings
settings:
  max_workers: 4          # Parallel execution if > 1, sequential if 1
  stop_on_failure: false  # Continue testing after failures
  verbose: true           # Detailed console output
  log_file: ".anvil/validation.log"

# Test suites
test_suites:
  # Individual cases explicitly listed
  - name: "validate_black_parser"
    type: "individual_cases"
    target: "black"       # References targets section below
    cases:
      - "black_single_file.yaml"
      - "black_multiple_files.yaml"
      - "black_no_violations.yaml"
      - "black_with_emoji"  # folder (no extension = folder)

  # All cases in a folder
  - name: "validate_flake8_parser"
    type: "cases_in_folder"
    target: "flake8"
    folder: "flake8_cases"

  # Folder with exclusions
  - name: "validate_isort_parser"
    type: "cases_in_folder"
    target: "isort"
    folder: "isort_cases"
    exclude:
      - "isort_wip"           # folder
      - "isort_broken.yaml"   # file

# Target definitions
# Maps target names to callable implementations
# Each callable must implement the interface: (str) -> dict
targets:
  black:
    callable: "anvil.validators.adapters.validate_black_parser"

  flake8:
    callable: "anvil.validators.adapters.validate_flake8_parser"

  isort:
    callable: "anvil.validators.adapters.validate_isort_parser"

  coverage_check:
    callable: "anvil.validators.adapters.validate_coverage_analyzer"

  test_results:
    callable: "anvil.validators.adapters.validate_test_parser"

  log_analyzer:
    callable: "anvil.validators.adapters.validate_log_analyzer"
```

**Interface Contract**:

All target implementations must follow this signature:
```python
def target_callable(input_text: str) -> dict:
    """
    Process input text and return structured output as dictionary.

    Args:
        input_text: The raw input to process (from test case)

    Returns:
        Dictionary with validation results (structure varies by target)
    """
    pass
```

**How It Works**:

1. **Test suite specifies target**: `target: "black"`
2. **Framework imports callable**: `from anvil.validators.adapters import validate_black_parser`
3. **Framework calls interface**: `result = validate_black_parser(input_text)`
4. **Output validation**: Compares `result` dict against `expected` from test case

**Implementation Example** (`anvil/validators/adapters.py`):
```python
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

def validate_black_parser(input_text: str) -> dict:
    """
    Adapter for black parser validation.
    Converts LintParser output to dict format expected by test framework.
    """
    parser = LintParser()
    lint_data = parser.parse_black_output(input_text, Path("."))

    # Convert LintData to dict
    return {
        "total_violations": lint_data.total_violations,
        "files_scanned": len(lint_data.file_violations),
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violation_count": len(fv.violations),
                "violations": [
                    {
                        "line_number": v.line_number,
                        "severity": v.severity,
                        "code": v.code,
                        "message": v.message
                    }
                    for v in fv.violations
                ]
            }
            for fv in lint_data.file_violations
        ]
    }

def validate_flake8_parser(input_text: str) -> dict:
    """Adapter for flake8 parser validation."""
    parser = LintParser()
    lint_data = parser.parse_flake8_output(input_text, Path("."))
    # Same conversion as black...
    return {...}

def validate_coverage_analyzer(input_text: str) -> dict:
    """Adapter for coverage analyzer validation."""
    from anvil.coverage.analyzer import CoverageAnalyzer
    analyzer = CoverageAnalyzer(threshold=90)
    result = analyzer.analyze_coverage_report(input_text)
    # Convert to dict...
    return {...}
```

**Benefits**:
- **Explicit**: Clear interface contract, no magic
- **Decoupled**: Test framework knows nothing about LintParser, CoverageAnalyzer, etc.
- **Type-safe**: Simple signature: `str -> dict`
- **Testable**: Adapters can be unit tested independently
- **Flexible**: Any Python callable that matches signature works
- **No reflection**: No dynamic imports, class instantiation, or method discovery

---

## 4.1 Use Case Examples

### Use Case 1: Parser Validation (Current)
**Target**: Lint parser methods (black, flake8, isort)

**Adapter Implementation**:
```python
# File: anvil/validators/adapters.py
from anvil.parsers.lint_parser import LintParser
from pathlib import Path

def validate_black_parser(input_text: str) -> dict:
    """Validate black parser output."""
    parser = LintParser()
    lint_data = parser.parse_black_output(input_text, Path("."))
    return {
        "total_violations": lint_data.total_violations,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        # ... convert to dict
    }
```

**Configuration**:
```yaml
targets:
  black:
    callable: "anvil.validators.adapters.validate_black_parser"
```

### Use Case 2: Test Coverage Validation
**Target**: Coverage report analyzer

**Adapter Implementation**:
```python
# File: anvil/validators/adapters.py
def validate_coverage_analyzer(input_text: str) -> dict:
    """Validate coverage report analyzer."""
    from anvil.coverage.analyzer import CoverageAnalyzer

    analyzer = CoverageAnalyzer(
        threshold=90,
        exclude_patterns=["*/tests/*", "*/conftest.py"]
    )
    result = analyzer.analyze_coverage_report(input_text)

    return {
        "total_coverage": result.coverage_percentage,
        "threshold_met": result.meets_threshold,
        "uncovered_lines": result.uncovered_line_count,
        "modules_below_threshold": result.failing_modules
    }
```

**Configuration**:
```yaml
targets:
  coverage_check:
    callable: "anvil.validators.adapters.validate_coverage_analyzer"
```

**Test Case Example**:
```yaml
name: "Coverage report - above threshold"
description: "Test coverage analyzer with 95% coverage"

input:
  type: "file_path"
  content: "coverage.xml"

expected:
  total_coverage: 95.2
  threshold_met: true
  uncovered_lines: 45
  modules_below_threshold: []
```

### Use Case 3: Test Execution Validation
**Target**: Test result parser

**Adapter Implementation**:
```python
# File: anvil/validators/adapters.py
def validate_test_parser(input_text: str) -> dict:
    """Validate pytest output parser."""
    from anvil.testing.result_parser import TestResultParser

    parser = TestResultParser(format="pytest")
    result = parser.parse_pytest_output(input_text)

    return {
        "total_tests": result.total,
        "passed": result.passed,
        "failed": result.failed,
        "skipped": result.skipped,
        "duration": result.duration_seconds,
        "status": "success" if result.all_passed else "failed"
    }
```

**Configuration**:
```yaml
targets:
  test_results:
    callable: "anvil.validators.adapters.validate_test_parser"
```

**Test Case Example**:
```yaml
name: "Pytest results - all passing"
description: "Test pytest output parser with successful run"

input:
  type: "text"
  content: |
    ============================= test session starts ==============================
    collected 42 items

    tests/test_parser.py::test_black_output PASSED                          [ 50%]
    tests/test_parser.py::test_flake8_output PASSED                         [100%]

    ============================== 42 passed in 2.15s ==============================

expected:
  total_tests: 42
  passed: 42
  failed: 0
  skipped: 0
  duration: 2.15
  status: "success"
```

### Use Case 4: Program Execution Log Validation
**Target**: Log analyzer

**Adapter Implementation**:
```python
# File: anvil/validators/adapters.py
def validate_log_analyzer(input_text: str) -> dict:
    """Validate application log analyzer."""
    from anvil.logging.analyzer import LogAnalyzer

    analyzer = LogAnalyzer(log_level_threshold="INFO")
    result = analyzer.analyze_application_log(input_text)

    return {
        "total_lines": result.line_count,
        "log_levels": result.level_counts,
        "contains_messages": result.found_messages,
        "startup_successful": result.startup_ok,
        "errors_found": result.has_errors
    }
```

**Configuration**:
```yaml
targets:
  log_analyzer:
    callable: "anvil.validators.adapters.validate_log_analyzer"
```

**Test Case Example**:
```yaml
name: "Application log - startup sequence"
description: "Validate expected startup log messages"

input:
  type: "text"
  content: |
    2026-02-03 10:15:22 INFO Starting application v1.2.3
    2026-02-03 10:15:22 INFO Loading configuration from config.yaml
    2026-02-03 10:15:23 INFO Database connection established
    2026-02-03 10:15:23 INFO Server listening on port 8080
    2026-02-03 10:15:23 INFO Application ready

expected:
  total_lines: 5
  log_levels:
    INFO: 5
    WARNING: 0
    ERROR: 0
  contains_messages:
    - "Starting application v1.2.3"
    - "Database connection established"
    - "Application ready"
  startup_successful: true
  errors_found: false
```

### Use Case 5: Program Execution with Exit Code
**Target**: Process executor and validator

**Adapter Implementation**:
```python
# File: anvil/validators/adapters.py
def validate_program_execution(input_text: str) -> dict:
    """Validate program execution (input_text is command to run)."""
    from anvil.execution.runner import ProgramRunner
    import subprocess

    # For this use case, input_text is the command
    result = subprocess.run(
        input_text,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30
    )

    return {
        "exit_code": result.returncode,
        "stdout_contains": result.stdout.split('\n'),
        "stderr_empty": len(result.stderr) == 0,
        "execution_time_under": True  # Would need timing
    }
```

**Configuration**:
```yaml
targets:
  program_execution:
    callable: "anvil.validators.adapters.validate_program_execution"
```

**Test Case Example**:
```yaml
name: "CLI tool - successful execution"
description: "Test CLI tool produces expected output and exit code"

input:
  type: "text"  # Command to execute
  content: "python -m myapp.cli --version"

expected:
  exit_code: 0
  stdout_contains:
    - "myapp version 1.2.3"
  stderr_empty: true
  execution_time_under: 5.0
```

---

## 4.2 Verdict Package Configuration

### setup.py
```python
from setuptools import setup, find_packages

setup(
    name="verdict",
    version="1.0.0",
    description="Generic test validation framework",
    author="Argos Team",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "isort>=5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "verdict=verdict.cli:main",
        ],
    },
    python_requires=">=3.8",
)
```

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "verdict"
version = "1.0.0"
description = "Generic test validation framework"
requires-python = ">=3.8"

dependencies = [
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "isort>=5.0",
]

[project.scripts]
verdict = "verdict.cli:main"
```

---

## 4.3 Creating New Adapters (in Consumer Projects)

**Step 1: Install Verdict** in your project (e.g., Anvil):
```bash
cd anvil
pip install -e ../verdict
```

**Step 2: Implement the interface** in `anvil/validators/adapters.py`:
```python
def validate_my_component(input_text: str) -> dict:
    """
    Adapter for my custom component.

    Args:
        input_text: Raw input from test case

    Returns:
        Dictionary with validation results
    """
    # Import your component
    from my_module import MyComponent

    # Execute component logic
    component = MyComponent()
    result = component.process(input_text)

    # Convert to dict (required fields depend on your test cases)
    return {
        "status": result.status,
        "output": result.output,
        "errors": result.errors,
        # ... any fields your test cases will check
    }
```

**Step 2: Register in config**:
```yaml
targets:
  my_component:
    callable: "anvil.validators.adapters.validate_my_component"
```

**Step 3: Create test cases**:
```yaml
name: "My component test"
input:
  type: "text"
  content: "test input"
expected:
  status: "success"
  output: "expected output"
```

**Guidelines**:
- Keep adapters simple: just convert between formats
- Adapter owns all configuration (thresholds, paths, etc.)
- Return plain dicts, not custom objects
- Handle errors and return them in dict format if needed
- One adapter per target, even if reusing same component

---

## 5. Project Structure

### 5.1 Verdict Package (Root Level)

```
argos/
├── verdict/                       # Standalone test validation tool
│   ├── __init__.py
│   ├── setup.py                   # Package installation
│   ├── pyproject.toml             # Modern Python packaging
│   ├── requirements.txt
│   ├── README.md
│   │
│   ├── verdict/                   # Main package
│   │   ├── __init__.py
│   │   ├── runner.py              # Test execution engine
│   │   ├── loader.py              # Config and test case loader
│   │   ├── executor.py            # Target callable executor
│   │   ├── validator.py           # Output comparison logic
│   │   └── logger.py              # Test logging
│   │
│   ├── tests/                     # Verdict's own tests
│   │   └── test_verdict.py
│   │
│   └── examples/                  # Example configurations
│       └── basic_example/
│           ├── config.yaml
│           └── cases/
│
├── anvil/                         # Uses Verdict
│   ├── requirements.txt           # Includes verdict as dependency
│   ├── validators/
│   │   ├── __init__.py
│   │   └── adapters.py            # Anvil-specific adapters
│   │
│   └── tests/
│       └── validation/            # Anvil validation tests
│           ├── config.yaml        # Anvil's Verdict configuration
│           └── cases/             # Anvil's test cases
│           ├── black_cases/
│           │   ├── single_file.yaml
│           │   ├── multiple_files.yaml
│           │   └── with_emoji/
│           │       ├── input.txt
│           │       └── expected_output.yaml
│           │
│           ├── flake8_cases/
│           ├── isort_cases/
│           ├── coverage_cases/
│           └── test_execution_cases/
│
├── forge/                         # Can also use Verdict
│   └── validators/
│       └── adapters.py            # Forge-specific adapters
│
├── scout/                         # Can also use Verdict
│   └── validators/
│       └── adapters.py            # Scout-specific adapters
│
└── scripts/
    └── run_validations.py         # Convenience script
```

**Key Benefits of Root-Level Structure**:
- ✅ **Reusable**: Anvil, Forge, Scout can all use Verdict
- ✅ **Decoupled**: Verdict has no knowledge of Anvil/Forge/Scout
- ✅ **Installable**: Standard Python package with setup.py
- ✅ **Versioned**: Can version Verdict independently
- ✅ **Testable**: Verdict has its own test suite
- ✅ **Portable**: Could be extracted to separate repo if needed

---

## 5.2 Installation & Usage

### Installing Verdict

**Option 1: Install from source (development)**
```bash
# From argos root
cd verdict
pip install -e .
```

**Option 2: Add as dependency in Anvil**
```toml
# anvil/pyproject.toml
[project]
dependencies = [
    "verdict @ file:///../verdict",  # Local development
    # OR for production:
    # "verdict>=1.0.0"
]
```

```txt
# anvil/requirements.txt
-e ../verdict  # Development mode
```

### Using Verdict in Anvil

**Step 1: Create adapters** (`anvil/validators/adapters.py`):
```python
from verdict import ValidationAdapter

def validate_black_parser(input_text: str) -> dict:
    """Anvil-specific adapter for black parser."""
    from anvil.parsers.lint_parser import LintParser
    # ... implementation
    return {...}
```

**Step 2: Configure tests** (`anvil/tests/validation/config.yaml`):
```yaml
targets:
  black:
    callable: "anvil.validators.adapters.validate_black_parser"

test_suites:
  - name: "validate_black_parser"
    target: "black"
    type: "cases_in_folder"
    folder: "black_cases"
```

**Step 3: Run validation**:
```bash
# Using Verdict CLI
verdict run --config anvil/tests/validation/config.yaml

# Or programmatically
from verdict import TestRunner
runner = TestRunner("anvil/tests/validation/config.yaml")
results = runner.run_all()
```

---

## 6. Test Definition & Implementation

### 6.1 Test Runner Architecture

**Components**:

   - Supports different input types: text, file_path, command
1. **ConfigLoader** (`runner.py`)
   - Loads `test_config.yaml`
   - Discovers test cases based on configuration
   - Validates configuration structure
   - Loads target definitions

2. **TestCaseLoader** (`runner.py`)
   - Loads individual test cases (YAML or folder)
   - Parses input/expected sections
   - Validates test case structure
   - Determines case type (single-file vs folder)

3. **TargetExecutor** (`runner.py`)
   - Dynamically imports target module/class/method
   - Executes target with test input and configured parameters
   - Returns actual output (structure depends on target)
   - Handles execution errors gracefully

4. **OutputValidator** (`validator.py`)
   - Compares actual vs expected output
   - Supports partial matching (only check specified fields)
   - Returns detailed diff on mismatch
   - Handles nested structures (dicts, lists, objects)

5. **TestLogger** (`logger.py`)
   - Logs test execution (start, progress, results)
   - Saves to JSON file with timestamp
   - Supports multiple output formats (console, file, JSON)
   - Thread-safe for parallel execution

### 6.2 Test Execution Flow

```
1. Load test_config.yaml
2. For each test_suite:
   a. Discover test cases
   b. Load test case definitions
   c. Execute tests (parallel or sequential)
   d. Validate outputs
   e. Log results
3. Generate summary report
4. Exit with appropriate code (0 = all pass, 1 = any fail)
```

### 6.3 Test Case Validation Logic

**Comparison Strategy**:

- **Exact Match Fields**: `total_violations`, `files_scanned`, `errors`, `warnings`, `info`
- **Dictionary Match**: `by_code` (all expected keys must match)
- **List Match**: `file_violations` (check count and key fields)
- **Optional Deep Match**: Full `LintData` structure if provided

**Validation Modes**:

1. **Strict Mode**: Every field must match exactly
2. **Partial Mode** (default): Only check fields specified in `expected`
3. **Regex Mode**: Support regex patterns in expected values (for messages)

---

## 7. Parallel Execution

### 7.1 Strategy

**Using Python's `concurrent.futures.ThreadPoolExecutor`**

**Rationale**:
- Component execution is typically fast (CPU or I/O)
- Thread pool simpler than process pool for this use case
- GIL impact minimal (I/O for file loading, computation is brief)
- Easy shared state for logging

**Configuration**:
```yaml
settings:
  max_workers: 4  # > 1 = parallel, 1 = sequential, null/0 = cpu_count()
```

**Execution Mode**:
- `max_workers: 1` → Sequential execution
- `max_workers: 4` → Parallel with 4 threads
- `max_workers: null` → Parallel with `os.cpu_count()` threads

### 7.2 Thread Safety

**Safe Operations**:
- Each test case runs independently
- No shared mutable state between tests
- Logger uses thread-safe queue or locks

**Execution Order**:
- Tests may complete out of order
- Results are collected and sorted for reporting

---

## 8. Logging & Execution Tracking

### 8.1 Log Levels

- **DEBUG**: Parser method calls, input/output details
- **INFO**: Test start/completion, progress
- **WARNING**: Partial matches, unexpected fields
- **ERROR**: Test failures, validation errors
- **CRITICAL**: Configuration errors, system failures

### 8.2 Log Output Formats

**Console Output** (human-readable):
```
[INFO] Running test suite: validate_black_parser (target: black)
  [INFO] Test 1/3: black_single_file.yaml
    ✓ PASS (0.05s)
  [INFO] Test 2/3: black_multiple_files.yaml
    ✓ PASS (0.03s)
  [INFO] Test 3/3: black_with_emoji
    ✗ FAIL (0.04s)
      Field mismatch: total_violations
        Expected: 2
        Actual: 3

[INFO] Summary:
  Total: 3 tests
  Passed: 2 (66.7%)
  Failed: 1 (33.3%)
  Duration: 0.12s
```

**JSON Log File** (`.anvil/validation_{timestamp}.json`):
```json
{
  "timestamp": "2026-02-03T15:30:00",
  "config_file": "test_config.yaml",
  "settings": {
    "max_workers": 4,
    "stop_on_failure": false,
    "verbose": true
  },
  "test_suites": [
    {
      "name": "validate_black_parser",
      "target": "black",
      "total_tests": 3,
      "passed": 2,
      "failed": 1,
      "duration": 0.12,
      "tests": [
        {
          "name": "black_single_file.yaml",
          "status": "PASS",
          "duration": 0.05
        },
        {
          "name": "black_with_emoji",
          "status": "FAIL",
          "duration": 0.04,
          "error": "Field mismatch: total_violations",
          "diff": {
            "field": "total_violations",
            "expected": 2,
            "actual": 3
          }
        }
      ]
    }
  ],
  "summary": {
    "total_tests": 3,
    "passed": 2,
    "failed": 1,
    "duration": 0.12
  }
}
```

### 8.3 Execution Tracking

**Current Solution**: File-based JSON logs

**Future with Gaze**:
- Integrate with Gaze execution tracking
- Store results in Gaze database
- Enable historical trend analysis
- Support for CI/CD integration

**Transition Plan**:
- Phase 1: JSON file logging (immediate)
- Phase 2: Add Gaze adapter layer (when Gaze ready)
- Phase 3: Full Gaze integration with reporting

---

## 9. CLI Interface

### 9.1 Verdict CLI

**After installing Verdict**, use the `verdict` command:

```bash
# Run all tests from config
verdict run --config anvil/tests/validation/config.yaml

# Run specific test suite
verdict run --config config.yaml --suite validate_black_parser

# Run specific test case
verdict run --config config.yaml --case black_single_file.yaml

# Run with options
verdict run --config config.yaml --workers 8 --verbose

# Stop on first failure
verdict run --config config.yaml --fail-fast

# Output format
verdict run --config config.yaml --format json
verdict run --config config.yaml --format console
verdict run --config config.yaml --format html  # future

# Show version and info
verdict --version
verdict --help
```

### 9.2 Convenience Script (Optional)

**File**: `scripts/run_validations.py`

```python
#!/usr/bin/env python
"""Convenience script to run Anvil validations."""
import sys
from verdict import TestRunner

if __name__ == "__main__":
    runner = TestRunner("anvil/tests/validation/config.yaml")
    results = runner.run_all()
    sys.exit(0 if results.all_passed else 1)
```

### 9.3 GitHub Actions Workflow

**File**: `.github/workflows/validate-anvil.yml`

```yaml
name: Validate Anvil Components

on:
  workflow_dispatch:  # Manual trigger only
    inputs:
      suite:
        description: 'Test suite to run (or "all")'
        required: false
        default: 'all'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Verdict
        run: |
          cd verdict
          pip install -e .

      - name: Install Anvil dependencies
        run: |
          cd anvil
          pip install -r requirements.txt

      - name: Run validation tests
        run: |
          verdict run \
            --config anvil/tests/validation/config.yaml \
            --suite ${{ github.event.inputs.suite || 'all' }} \
            --format json \
            --output validation_results.json

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-results
          path: validation_results.json
          retention-days: 30
```

---

## 10. Implementation Phases

### Phase 1: Core Verdict Package (Week 1)
- [ ] Create `verdict/` directory at argos root
- [ ] Create `verdict/setup.py` and `verdict/pyproject.toml`
- [ ] Implement `verdict/verdict/loader.py` (ConfigLoader, TestCaseLoader)
- [ ] Implement `verdict/verdict/executor.py` (TargetExecutor)
- [ ] Implement `verdict/verdict/validator.py` (OutputValidator)
- [ ] Implement `verdict/verdict/runner.py` (TestRunner)
- [ ] Implement `verdict/verdict/logger.py` (TestLogger)
- [ ] Implement `verdict/verdict/cli.py` (CLI entry point)
- [ ] Create Verdict's own test suite
- [ ] Create example configurations in `verdict/examples/`
- [ ] Test installation: `pip install -e verdict`

### Phase 2: Anvil Integration (Week 2)
- [ ] Add Verdict to `anvil/requirements.txt`
- [ ] Create `anvil/validators/adapters.py`
- [ ] Implement 3 adapters (black, flake8, isort)
- [ ] Create `anvil/tests/validation/config.yaml`
- [ ] Create comprehensive test cases (10+ per adapter)
- [ ] Test Verdict CLI from Anvil
- [ ] Create convenience scripts if needed

### Phase 2: Enhanced Features (Week 2)
- [ ] Add parallel execution support
- [ ] Implement JSON logging
- [ ] Add CLI with argparse
- [ ] Create comprehensive test cases (10+ per parser)
- [ ] Add validation modes (strict/partial/regex)
- [ ] Error handling and edge cases

### Phase 3: Integration (Week 3)
- [ ] GitHub Actions workflow
- [ ] Documentation (README, examples)
- [ ] CI artifact upload/download
- [ ] HTML report generation (optional)
- [ ] Performance benchmarking

### Phase 4: Gaze Integration (Future)
- [ ] Design Gaze adapter interface
- [ ] Implement execution tracking with Gaze
- [ ] Migrate JSON logs to Gaze database
- [ ] Historical trend analysis

---

## 11. Success Criteria

**Must Have**:
- ✅ Run all parser validation tests successfully
- ✅ Clear pass/fail reporting for each test
- ✅ Detailed error messages on failures
- ✅ Support for both single-file and folder test cases
- ✅ Configuration-driven test discovery
- ✅ Local script execution
- ✅ Manual GitHub Actions workflow

**Should Have**:
- ✅ Parallel execution for performance
- ✅ JSON logging for analysis
- ✅ Partial matching for flexible validation
- ✅ Comprehensive test coverage (20+ cases)

**Nice to Have**:
- ⭕ HTML report generation
- ⭕ Regex pattern matching in expectations
- ⭕ Performance benchmarks per parser
- ⭕ Test case generation from real CI logs

---

## 12. Open Questions & Decisions

### Q1: Should we support test case inheritance?
**Example**: Base test case with common setup, variants override specific fields

**Decision**: Not in Phase 1. Add if needed.

### Q2: How to handle parser errors (exceptions)?
**Options**:
1. Catch and fail test gracefully
2. Allow expected exceptions in test case
3. Both

**Recommendation**: Option 3 - support both error cases and expected exceptions

### Q3: Should we validate performance (execution time)?
**Recommendation**: Track but don't assert in Phase 1. Add thresholds in Phase 2.

### Q4: How to handle test data updates (target component changes)?
**Recommendation**:
- Document when component changes require test updates
- Consider regeneration tool for bulk updates
- Use descriptive test names to clarify what is being tested

### Q5: Should tests modify filesystem?

### Q6: How to handle different input types (text, file, command)?
**Recommendation**:
- Support `input.type` field: `text`, `file_path`, `command`
- TargetExecutor adapts based on input type
- For `command`: execute and capture output before passing to target
- For `file_path`: load file content before passing to target

### Q7: How to validate complex nested structures?
**Recommendation**:
- Use partial matching by default
- Support dot notation for nested field access: `expected.data.result.status`
- Allow regex patterns in string fields
- Consider JSONPath or similar for complex queries (Phase 2)
**Recommendation**: No. Keep tests pure (input → output). Use temp directories if needed.

---

## 13. Dependencies

**Required**:
- `pyyaml` - YAML parsing
- `pytest` (optional) - Could wrap in pytest for IDE integration

**Optional**:
- `deepdiff` - Advanced output comparison
- `jinja2` - HTML report generation
- `colorama` - Colored console output

---

## 14. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Test cases become outdated | Medium | High | Version test cases, document update process |
| Parallel execution bugs | Low | Medium | Thorough testing, fallback to sequential |
| Configuration complexity | Medium | Medium | Clear docs, validation, examples |
| Performance degradation | Low | Low | Track execution time, benchmark |
| Gaze integration delay | Low | Medium | File-based logs work independently |

---

## 15. Next Steps

### Immediate Actions
1. **Review & Approve** this specification
2. **Create Verdict project structure** at argos root
3. **Implement Verdict core** (Phase 1)
4. **Test Verdict standalone** with examples
5. **Integrate into Anvil** (Phase 2)
6. **Create Anvil adapters** and test cases
7. **Validate with real parser outputs** from CI logs
8. **Document usage** in Verdict README

### Future Enhancements
- **Extract to separate repo**: If Verdict proves useful beyond Argos
- **Publish to PyPI**: For external projects to use
- **Add Forge/Scout adapters**: Extend to other Argos components
- **Create adapter generator**: Tool to scaffold new adapters

---

**End of Specification Document**
