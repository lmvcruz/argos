# Anvil API Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Creating Custom Validators](#creating-custom-validators)
5. [Parser Development](#parser-development)
6. [Result Aggregation](#result-aggregation)
7. [Statistics Integration](#statistics-integration)
8. [Configuration Extension](#configuration-extension)
9. [Testing Custom Validators](#testing-custom-validators)
10. [API Reference](#api-reference)

## Introduction

Anvil provides a plugin architecture for extending validation capabilities. This guide explains how to:

- Create custom validators for new tools
- Implement parsers for tool output
- Integrate with Anvil's result aggregation
- Add custom configuration options
- Test custom validators

### Prerequisites

- Python 3.8+
- Understanding of Anvil's architecture
- Familiarity with the tool you're integrating

## Architecture Overview

### Component Hierarchy

```
ValidatorBase (Abstract)
    ↓
PythonValidator / CppValidator
    ↓
ToolSpecificValidator (e.g., Flake8Validator)
    ↓
ParserBase (Abstract)
    ↓
ToolSpecificParser (e.g., Flake8Parser)
```

### Validation Flow

1. **Discovery**: Detect language and collect files
2. **Execution**: Run validator tools on files
3. **Parsing**: Parse tool output into standard format
4. **Aggregation**: Combine results from all validators
5. **Reporting**: Display results to user
6. **Statistics**: Store results in database (optional)

## Core Components

### ValidatorBase

Abstract base class for all validators.

```python
from anvil.validators.base import ValidatorBase
from anvil.models.validation_result import ValidationResult
from typing import List, Optional

class ValidatorBase:
    """
    Base class for all validators.

    All validators must inherit from this class and implement
    the abstract methods.
    """

    def __init__(self, config: dict):
        """
        Initialize validator with configuration.

        Args:
            config: Validator-specific configuration from anvil.toml
        """
        self.config = config
        self.enabled = config.get("enabled", True)

    @property
    def name(self) -> str:
        """Get validator name."""
        raise NotImplementedError

    @property
    def language(self) -> str:
        """Get target language (python, cpp, or both)."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """
        Check if validator tool is available.

        Returns:
            True if tool is installed and can be executed
        """
        raise NotImplementedError

    def validate(self, files: List[str]) -> ValidationResult:
        """
        Run validation on files.

        Args:
            files: List of file paths to validate

        Returns:
            ValidationResult with errors, warnings, and metadata
        """
        raise NotImplementedError
```

### ParserBase

Abstract base class for output parsers.

```python
from anvil.parsers.base import ParserBase
from anvil.models.validation_result import ValidationResult, Issue
from typing import List

class ParserBase:
    """
    Base class for output parsers.

    Parsers convert tool-specific output into standard ValidationResult.
    """

    def parse(self, output: str, files: List[str]) -> ValidationResult:
        """
        Parse tool output into ValidationResult.

        Args:
            output: Raw tool output (stdout/stderr)
            files: Files that were validated

        Returns:
            ValidationResult with parsed issues
        """
        raise NotImplementedError

    def parse_issue(self, line: str) -> Optional[Issue]:
        """
        Parse single issue from output line.

        Args:
            line: Single line of tool output

        Returns:
            Issue object or None if line doesn't contain issue
        """
        raise NotImplementedError
```

### ValidationResult

Standard result format for all validators.

```python
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Issue:
    """Represents a single validation issue."""

    file: str                # File path
    line: int               # Line number (0 if not applicable)
    column: int             # Column number (0 if not applicable)
    severity: str           # error, warning, info
    message: str            # Issue description
    code: str              # Error code (e.g., E501, C0111)
    source: str            # Validator name
    suggestion: Optional[str] = None  # Fix suggestion

@dataclass
class ValidationResult:
    """Validation results from a single validator."""

    validator: str          # Validator name
    passed: bool           # Overall pass/fail
    issues: List[Issue]    # List of issues found
    errors_count: int      # Number of errors
    warnings_count: int    # Number of warnings
    files_checked: int     # Number of files validated
    duration: float        # Execution time in seconds
    metadata: Dict         # Additional validator-specific data
```

## Creating Custom Validators

### Step 1: Define Validator Class

```python
# anvil/validators/python/mypy_validator.py
"""Mypy type checking validator."""

from anvil.validators.base import ValidatorBase
from anvil.validators.python_validator import PythonValidator
from anvil.parsers.mypy_parser import MypyParser
from anvil.models.validation_result import ValidationResult
from typing import List
import subprocess
import shutil


class MypyValidator(PythonValidator):
    """
    Validator for mypy type checking.

    Runs mypy on Python files and reports type errors.
    """

    def __init__(self, config: dict):
        """
        Initialize mypy validator.

        Args:
            config: Configuration from [python.mypy] section
        """
        super().__init__(config)
        self.parser = MypyParser()
        self.strict = config.get("strict", False)
        self.ignore_missing_imports = config.get(
            "ignore_missing_imports", False
        )

    @property
    def name(self) -> str:
        """Get validator name."""
        return "mypy"

    @property
    def language(self) -> str:
        """Get target language."""
        return "python"

    def is_available(self) -> bool:
        """
        Check if mypy is installed.

        Returns:
            True if mypy command is available
        """
        return shutil.which("mypy") is not None

    def build_command(self, files: List[str]) -> List[str]:
        """
        Build mypy command.

        Args:
            files: Files to check

        Returns:
            Command as list of arguments
        """
        cmd = ["mypy"]

        if self.strict:
            cmd.append("--strict")

        if self.ignore_missing_imports:
            cmd.append("--ignore-missing-imports")

        # Output format for parsing
        cmd.extend(["--show-column-numbers", "--no-error-summary"])

        cmd.extend(files)

        return cmd

    def validate(self, files: List[str]) -> ValidationResult:
        """
        Run mypy on files.

        Args:
            files: List of Python files to check

        Returns:
            ValidationResult with type errors
        """
        if not self.enabled:
            return self._create_skipped_result()

        if not self.is_available():
            return self._create_unavailable_result()

        # Filter to Python files only
        python_files = [f for f in files if f.endswith(".py")]

        if not python_files:
            return self._create_empty_result()

        # Build and execute command
        cmd = self.build_command(python_files)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse output
            validation_result = self.parser.parse(
                result.stdout,
                python_files
            )

            return validation_result

        except subprocess.TimeoutExpired:
            return self._create_timeout_result()
        except Exception as e:
            return self._create_error_result(str(e))
```

### Step 2: Implement Parser

```python
# anvil/parsers/mypy_parser.py
"""Parser for mypy output."""

import re
from anvil.parsers.base import ParserBase
from anvil.models.validation_result import ValidationResult, Issue
from typing import List, Optional


class MypyParser(ParserBase):
    """
    Parser for mypy type checker output.

    Parses mypy output format:
    file.py:10:5: error: Description [error-code]
    """

    # Pattern: file.py:10:5: error: Description [error-code]
    ISSUE_PATTERN = re.compile(
        r'^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+): '
        r'(?P<severity>\w+): (?P<message>.+?)(\s+\[(?P<code>.+?)\])?$'
    )

    def parse(self, output: str, files: List[str]) -> ValidationResult:
        """
        Parse mypy output.

        Args:
            output: Raw mypy output
            files: Files that were checked

        Returns:
            ValidationResult with parsed issues
        """
        issues = []

        for line in output.splitlines():
            issue = self.parse_issue(line)
            if issue:
                issues.append(issue)

        errors_count = sum(1 for i in issues if i.severity == "error")
        warnings_count = sum(1 for i in issues if i.severity == "warning")

        return ValidationResult(
            validator="mypy",
            passed=(errors_count == 0),
            issues=issues,
            errors_count=errors_count,
            warnings_count=warnings_count,
            files_checked=len(files),
            duration=0.0,  # Set by validator
            metadata={}
        )

    def parse_issue(self, line: str) -> Optional[Issue]:
        """
        Parse single issue from output line.

        Args:
            line: Single line of mypy output

        Returns:
            Issue object or None
        """
        match = self.ISSUE_PATTERN.match(line)

        if not match:
            return None

        return Issue(
            file=match.group("file"),
            line=int(match.group("line")),
            column=int(match.group("column")),
            severity=match.group("severity"),
            message=match.group("message"),
            code=match.group("code") or "no-code",
            source="mypy"
        )
```

### Step 3: Register Validator

```python
# anvil/validators/registry.py

from anvil.validators.python.mypy_validator import MypyValidator

PYTHON_VALIDATORS = {
    "flake8": Flake8Validator,
    "black": BlackValidator,
    "mypy": MypyValidator,  # Add new validator
    # ...
}
```

### Step 4: Add Configuration Schema

```python
# anvil/config/schema.py

VALIDATOR_SCHEMAS = {
    "python": {
        "mypy": {
            "enabled": bool,
            "strict": bool,
            "ignore_missing_imports": bool,
        },
        # ...
    }
}
```

## Parser Development

### Output Format Strategies

#### Line-Based Parsing

For simple line-by-line output (flake8, pylint):

```python
def parse(self, output: str, files: List[str]) -> ValidationResult:
    issues = []
    for line in output.splitlines():
        issue = self.parse_issue(line)
        if issue:
            issues.append(issue)
    return self._build_result(issues, files)
```

#### JSON Parsing

For JSON output (pytest, pylint --output-format=json):

```python
import json

def parse(self, output: str, files: List[str]) -> ValidationResult:
    try:
        data = json.loads(output)
        issues = self._parse_json_issues(data)
        return self._build_result(issues, files)
    except json.JSONDecodeError as e:
        return self._create_parse_error_result(str(e))
```

#### XML Parsing

For XML output (cppcheck, gtest):

```python
import xml.etree.ElementTree as ET

def parse(self, output: str, files: List[str]) -> ValidationResult:
    try:
        root = ET.fromstring(output)
        issues = self._parse_xml_issues(root)
        return self._build_result(issues, files)
    except ET.ParseError as e:
        return self._create_parse_error_result(str(e))
```

### Regular Expression Patterns

Common patterns for parsing tool output:

```python
# Pattern for file:line:column format
FILE_LINE_COL = re.compile(
    r'^(?P<file>.+?):(?P<line>\d+):(?P<column>\d+):'
)

# Pattern for severity levels
SEVERITY = re.compile(r'\b(error|warning|info|note)\b', re.IGNORECASE)

# Pattern for error codes
ERROR_CODE = re.compile(r'\[([A-Z]\d+)\]')

# Pattern for suggestions
SUGGESTION = re.compile(r'(Try|Consider|Use|Replace): (.+?)$')
```

### Error Handling

Robust parsers handle edge cases:

```python
def parse_issue(self, line: str) -> Optional[Issue]:
    """Parse with comprehensive error handling."""
    try:
        match = self.PATTERN.match(line)
        if not match:
            return None

        # Validate parsed data
        file_path = match.group("file")
        if not file_path:
            return None

        line_num = int(match.group("line"))
        if line_num < 0:
            line_num = 0

        return Issue(
            file=file_path,
            line=line_num,
            column=int(match.group("column") or 0),
            severity=self._normalize_severity(match.group("severity")),
            message=match.group("message").strip(),
            code=match.group("code") or "unknown",
            source=self.validator_name
        )
    except (ValueError, AttributeError, IndexError) as e:
        # Log but don't fail entire parse
        self.logger.warning(f"Failed to parse line: {line}, error: {e}")
        return None

def _normalize_severity(self, severity: str) -> str:
    """Normalize severity to standard levels."""
    severity_lower = severity.lower()
    if severity_lower in ["error", "fatal", "critical"]:
        return "error"
    elif severity_lower in ["warning", "warn"]:
        return "warning"
    else:
        return "info"
```

## Result Aggregation

### Aggregator Interface

```python
from anvil.core.aggregator import ResultAggregator
from anvil.models.validation_result import ValidationResult
from typing import List

class ResultAggregator:
    """Aggregates results from multiple validators."""

    def aggregate(
        self,
        results: List[ValidationResult]
    ) -> AggregatedResult:
        """
        Combine results from all validators.

        Args:
            results: List of validator results

        Returns:
            AggregatedResult with combined metrics
        """
        total_errors = sum(r.errors_count for r in results)
        total_warnings = sum(r.warnings_count for r in results)
        all_passed = all(r.passed for r in results)

        return AggregatedResult(
            passed=all_passed,
            total_errors=total_errors,
            total_warnings=total_warnings,
            validator_results=results,
            summary=self._generate_summary(results)
        )
```

### Custom Aggregation Logic

```python
class CustomAggregator(ResultAggregator):
    """Custom aggregation with severity weighting."""

    def __init__(self, config: dict):
        self.error_weight = config.get("error_weight", 1.0)
        self.warning_weight = config.get("warning_weight", 0.5)
        self.quality_threshold = config.get("quality_threshold", 0.9)

    def calculate_quality_score(
        self,
        results: List[ValidationResult]
    ) -> float:
        """
        Calculate quality score (0.0 to 1.0).

        Formula: 1 - (weighted_issues / total_checks)
        """
        total_files = sum(r.files_checked for r in results)

        if total_files == 0:
            return 1.0

        weighted_issues = sum(
            r.errors_count * self.error_weight +
            r.warnings_count * self.warning_weight
            for r in results
        )

        score = max(0.0, 1.0 - (weighted_issues / total_files))
        return score

    def aggregate(
        self,
        results: List[ValidationResult]
    ) -> AggregatedResult:
        """Aggregate with quality score."""
        base_result = super().aggregate(results)

        quality_score = self.calculate_quality_score(results)
        base_result.quality_score = quality_score
        base_result.passed = (
            base_result.passed and
            quality_score >= self.quality_threshold
        )

        return base_result
```

## Statistics Integration

### Recording Validation Results

```python
from anvil.storage.statistics import StatisticsDatabase
from anvil.models.validation_result import ValidationResult

class ValidatorWithStats(ValidatorBase):
    """Validator with statistics tracking."""

    def __init__(self, config: dict, stats_db: StatisticsDatabase):
        super().__init__(config)
        self.stats_db = stats_db

    def validate(self, files: List[str]) -> ValidationResult:
        """Validate and record statistics."""
        result = self._run_validation(files)

        # Record in database
        if self.stats_db.enabled:
            self.stats_db.record_validator_result(
                validator_name=self.name,
                result=result,
                git_commit=self._get_git_commit()
            )

        return result
```

### Querying Historical Data

```python
from anvil.storage.statistics import StatisticsDatabase

# Get success rate for specific test
stats_db = StatisticsDatabase(".anvil/stats.db")
success_rate = stats_db.get_test_success_rate(
    "test_user_authentication",
    last_n_runs=100
)

# Get flaky tests (50-90% success rate)
flaky_tests = stats_db.get_flaky_tests(
    min_success_rate=0.5,
    max_success_rate=0.9,
    min_runs=10
)

# Get file error frequency
problematic_files = stats_db.get_problematic_files(
    min_error_count=5,
    last_n_days=30
)
```

## Configuration Extension

### Adding Configuration Options

```python
# anvil/config/schema.py

# Define schema for new validator
MYPY_CONFIG_SCHEMA = {
    "enabled": {
        "type": bool,
        "default": True,
        "description": "Enable mypy validation"
    },
    "strict": {
        "type": bool,
        "default": False,
        "description": "Enable strict mode"
    },
    "ignore_missing_imports": {
        "type": bool,
        "default": False,
        "description": "Ignore missing imports"
    },
    "python_version": {
        "type": str,
        "default": "3.8",
        "description": "Target Python version"
    }
}

# Register in schema
PYTHON_VALIDATORS_SCHEMA["mypy"] = MYPY_CONFIG_SCHEMA
```

### Configuration Validation

```python
from anvil.config.validator import ConfigValidator

class MypyConfigValidator(ConfigValidator):
    """Validate mypy configuration."""

    def validate(self, config: dict) -> List[str]:
        """
        Validate configuration.

        Args:
            config: Mypy configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate python_version format
        if "python_version" in config:
            version = config["python_version"]
            if not re.match(r'^\d+\.\d+$', version):
                errors.append(
                    f"Invalid python_version: {version}. "
                    f"Expected format: X.Y"
                )

        # Validate mutual exclusions
        if config.get("strict") and config.get("ignore_missing_imports"):
            errors.append(
                "Cannot use 'strict' and 'ignore_missing_imports' together"
            )

        return errors
```

## Testing Custom Validators

### Unit Tests

```python
# tests/test_mypy_validator.py
"""Tests for mypy validator."""

import pytest
from anvil.validators.python.mypy_validator import MypyValidator
from anvil.parsers.mypy_parser import MypyParser


class TestMypyParser:
    """Test mypy parser."""

    def test_parse_type_error(self):
        """Test parsing type error."""
        parser = MypyParser()
        output = 'test.py:10:5: error: Incompatible types [assignment]'

        result = parser.parse(output, ["test.py"])

        assert len(result.issues) == 1
        issue = result.issues[0]
        assert issue.file == "test.py"
        assert issue.line == 10
        assert issue.column == 5
        assert issue.severity == "error"
        assert "Incompatible types" in issue.message
        assert issue.code == "assignment"

    def test_parse_no_errors(self):
        """Test parsing output with no errors."""
        parser = MypyParser()
        output = "Success: no issues found in 5 source files"

        result = parser.parse(output, ["test.py"])

        assert len(result.issues) == 0
        assert result.passed is True


class TestMypyValidator:
    """Test mypy validator."""

    def test_is_available_when_installed(self, mocker):
        """Test tool availability check."""
        mocker.patch("shutil.which", return_value="/usr/bin/mypy")

        validator = MypyValidator({"enabled": True})

        assert validator.is_available() is True

    def test_build_command_basic(self):
        """Test command building."""
        validator = MypyValidator({"enabled": True})

        cmd = validator.build_command(["test.py"])

        assert cmd[0] == "mypy"
        assert "test.py" in cmd
        assert "--show-column-numbers" in cmd

    def test_build_command_with_strict(self):
        """Test command with strict mode."""
        validator = MypyValidator({
            "enabled": True,
            "strict": True
        })

        cmd = validator.build_command(["test.py"])

        assert "--strict" in cmd

    @pytest.mark.integration
    def test_validate_real_code(self, tmp_path):
        """Integration test with real mypy."""
        # Create test file with type error
        test_file = tmp_path / "test.py"
        test_file.write_text(
            "def add(a: int, b: int) -> int:\n"
            "    return str(a + b)  # Type error\n"
        )

        validator = MypyValidator({"enabled": True})

        if not validator.is_available():
            pytest.skip("mypy not installed")

        result = validator.validate([str(test_file)])

        assert result.passed is False
        assert result.errors_count > 0
```

### Integration Tests

```python
# tests/integration/test_mypy_integration.py
"""Integration tests for mypy validator."""

import pytest
from pathlib import Path


@pytest.mark.integration
class TestMypyIntegration:
    """Integration tests with real mypy."""

    def test_validate_clean_code(self, tmp_path):
        """Test validation of type-correct code."""
        test_file = tmp_path / "clean.py"
        test_file.write_text(
            "def greet(name: str) -> str:\n"
            "    return f'Hello, {name}!'\n"
        )

        validator = MypyValidator({"enabled": True})
        result = validator.validate([str(test_file)])

        assert result.passed is True
        assert result.errors_count == 0

    def test_validate_with_errors(self, tmp_path):
        """Test validation with type errors."""
        test_file = tmp_path / "errors.py"
        test_file.write_text(
            "def add(a: int, b: int) -> int:\n"
            "    return 'not an int'  # Type error\n"
        )

        validator = MypyValidator({"enabled": True})
        result = validator.validate([str(test_file)])

        assert result.passed is False
        assert result.errors_count > 0
        assert any(
            "Incompatible return" in issue.message
            for issue in result.issues
        )
```

## API Reference

### Core Classes

#### `ValidatorBase`

Abstract base for all validators.

**Methods:**
- `__init__(config: dict)`: Initialize validator
- `name() -> str`: Get validator name (property)
- `language() -> str`: Get target language (property)
- `is_available() -> bool`: Check tool availability
- `validate(files: List[str]) -> ValidationResult`: Run validation

#### `ParserBase`

Abstract base for output parsers.

**Methods:**
- `parse(output: str, files: List[str]) -> ValidationResult`: Parse tool output
- `parse_issue(line: str) -> Optional[Issue]`: Parse single issue

#### `ValidationResult`

Standard validation result format.

**Attributes:**
- `validator: str`: Validator name
- `passed: bool`: Pass/fail status
- `issues: List[Issue]`: Found issues
- `errors_count: int`: Error count
- `warnings_count: int`: Warning count
- `files_checked: int`: Files validated
- `duration: float`: Execution time
- `metadata: Dict`: Additional data

#### `Issue`

Single validation issue.

**Attributes:**
- `file: str`: File path
- `line: int`: Line number
- `column: int`: Column number
- `severity: str`: error/warning/info
- `message: str`: Description
- `code: str`: Error code
- `source: str`: Validator name
- `suggestion: Optional[str]`: Fix suggestion

### Utility Functions

```python
# File filtering
from anvil.utils.file_utils import filter_by_extension

python_files = filter_by_extension(files, [".py"])

# Git operations
from anvil.utils.git_utils import get_changed_files

changed_files = get_changed_files(since="HEAD~1")

# Output formatting
from anvil.utils.output import format_issue

formatted = format_issue(issue, colorize=True)
```

## Best Practices

### Validator Development

1. **Fail Gracefully**: Handle missing tools, timeouts, parse errors
2. **Validate Configuration**: Check config early, provide helpful errors
3. **Test Thoroughly**: Unit tests + integration tests with real tool
4. **Document Well**: Docstrings for all public methods
5. **Follow Conventions**: Match existing validator patterns

### Parser Development

1. **Robust Parsing**: Handle malformed output gracefully
2. **Normalize Data**: Convert severity levels, file paths to standard format
3. **Extract Suggestions**: Parse fix suggestions when available
4. **Test Edge Cases**: Empty output, very long lines, special characters

### Performance

1. **Parallel Execution**: Use `concurrent.futures` for multiple files
2. **Caching**: Cache availability checks, file lists
3. **Incremental**: Support incremental validation
4. **Timeouts**: Set reasonable timeouts to prevent hangs

### Compatibility

1. **Tool Versions**: Handle output format differences across versions
2. **Platforms**: Test on Windows, Linux, macOS
3. **Python Versions**: Support Python 3.8+

## Examples

See the `examples/` directory for complete examples:

- `examples/custom_validator/` - Complete custom validator example
- `examples/custom_parser/` - Parser examples for different formats
- `examples/plugin_system/` - Loading validators from plugins

## Further Reading

- [User Guide](USER_GUIDE.md) - Using Anvil
- [Configuration Reference](CONFIGURATION.md) - Configuration options
- [Source Code](../anvil/) - Browse existing validators for examples
