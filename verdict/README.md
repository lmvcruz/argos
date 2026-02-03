# Verdict

**Generic test validation framework for comparing actual vs expected outputs**

## Overview

Verdict is a standalone, reusable testing framework that validates software components by comparing their actual outputs against expected results. It uses a simple interface contract (`str -> dict`) to decouple test execution from component implementation.

## Key Features

- **Interface-based decoupling**: Components implement `(str) -> dict` callable interface
- **Flexible test case formats**: Single-file YAML or folder-based test structures
- **Parallel execution**: Configurable multi-threading support
- **Multiple use cases**: Parser validation, test coverage, log analysis, program execution
- **Standalone package**: Install via pip and use across multiple projects

## Installation

### From source (development):

```bash
cd verdict
pip install -e .
```

### With development dependencies:

```bash
pip install -e ".[dev]"
```

## Quick Start

### 1. Create a test case (YAML):

```yaml
# tests/black_parser/case_01.yaml
input: |
  would reformat /path/to/file.py

  3 files would be reformatted, 2 files would be left unchanged.

expected:
  files_to_reformat: 3
  files_unchanged: 2
```

### 2. Create configuration:

```yaml
# config.yaml
settings:
  max_workers: 4

test_suites:
  - name: "black_parser_validation"
    target: "black"
    type: "cases_in_folder"
    folder: "tests/black_parser"

targets:
  black:
    callable: "myproject.validators.adapters.validate_black_parser"
```

### 3. Create adapter (in your project):

```python
# myproject/validators/adapters.py

def validate_black_parser(input_text: str) -> dict:
    """Adapter for black parser validation."""
    parser = BlackParser()
    result = parser.parse_output(input_text)
    return {
        "files_to_reformat": result.files_to_reformat,
        "files_unchanged": result.files_unchanged,
    }
```

### 4. Run tests:

```bash
verdict run --config config.yaml
```

## Usage

### Command-line Interface

```bash
# Run all test suites
verdict run --config path/to/config.yaml

# Run specific test suite
verdict run --config config.yaml --suite parser_validation

# Parallel execution
verdict run --config config.yaml --workers 8

# JSON output
verdict run --config config.yaml --format json
```

## Test Case Formats

### Single-file YAML:

```yaml
input: |
  <input text here>

expected:
  field1: value1
  field2: value2
```

### Folder-based:

```
tests/
  case_01/
    input.txt         # Input text
    expected_output.yaml  # Expected dict
  case_02/
    input.txt
    expected_output.yaml
```

## Configuration Structure

```yaml
settings:
  max_workers: 4  # Parallel execution (null = auto)

test_suites:
  - name: "suite_name"
    target: "target_id"
    type: "cases_in_folder"  # or "single_file"
    folder: "path/to/cases"  # or file: "path/to/file.yaml"

targets:
  target_id:
    callable: "module.path.function_name"
```

## Use Cases

1. **Parser Validation**: Test log/output parsers (black, flake8, isort, etc.)
2. **Coverage Validation**: Verify test coverage reports
3. **Test Execution**: Validate test runner outputs
4. **Log Analysis**: Parse and validate application logs
5. **Program Execution**: Test command-line tools and scripts

## Interface Contract

All target callables must implement:

```python
def callable(input_text: str) -> dict:
    """
    Process input text and return structured dict.

    Args:
        input_text: Raw input string to process

    Returns:
        Dictionary with structured output
    """
    pass
```

## Development

### Run tests:

```bash
pytest tests/
```

### Run with coverage:

```bash
pytest --cov=verdict tests/
```

### Format code:

```bash
black verdict/ tests/
isort verdict/ tests/
```

## Architecture

- **loader.py**: Loads configuration and test cases from YAML files
- **executor.py**: Imports and executes target callables
- **validator.py**: Compares actual vs expected dictionaries
- **runner.py**: Orchestrates test execution and parallelism
- **logger.py**: Formats and outputs test results
- **cli.py**: Command-line interface

## License

MIT

## Contributing

Contributions welcome! Please ensure:
- All tests pass
- Code is formatted (black, isort)
- Coverage ≥ 90%
- Documentation is updated
