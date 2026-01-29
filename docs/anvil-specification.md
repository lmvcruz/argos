# Anvil - Code Quality Gate Tool Specification

**Version:** 1.0
**Status:** Draft
**Created:** 2026-01-29
**Part of:** Argos Tooling Ecosystem

---

## Overview

**Anvil** is a flexible, language-agnostic code quality validation tool that enforces configurable quality standards across software projects. It provides a unified interface for running multiple quality checks (linting, formatting, complexity analysis, testing) and can be deployed in various contexts: interactive development, git hooks, CI/CD pipelines, or manual audits.

### Design Philosophy

- **Flexibility**: Can be used anywhere in the development workflow
- **Extensibility**: Plugin architecture allows adding new validators and languages
- **Simplicity**: Simple configuration for common use cases
- **Speed**: Incremental checking (only modified files) for fast feedback
- **Clarity**: Actionable error messages with suggested fixes

### Metalworking Metaphor

An anvil is where metal is tested for quality by striking it—flaws become evident, and the metal is shaped into its final form. Similarly, Anvil tests code quality by running validators, revealing issues that must be addressed before code is "forged" into production.

---

## Scope

### Iteration 2 Goals

Anvil will support **two programming languages** in Iteration 2:

1. **Python** - Complete support for Python ecosystem tools
2. **C++** - Complete support for C++ ecosystem tools

The architecture will be designed to easily add more languages in future iterations (JavaScript, Java, Rust, Go, etc.).

### Non-Goals (Iteration 2)

- Language-specific code generation or refactoring
- IDE integration (may be added in future)
- Real-time validation while typing (may be added in future)
- Automatic code fixing (reporting only; fixes are manual or via underlying tools)

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                         Anvil CLI                            │
│  (argparse-based command interface)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Configuration Manager                      │
│  (Loads anvil.toml, validates, provides config to runners)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Validation Orchestrator                   │
│  (Coordinates validators, aggregates results)                │
└──────┬──────────────────────────────────────────────┬───────┘
       │                                               │
┌──────▼──────────────┐                    ┌──────────▼────────┐
│  Language Detectors  │                    │  File Collectors  │
│  (Identify languages │                    │  (Find files to   │
│   in project)        │                    │   validate)       │
└──────┬──────────────┘                    └──────────┬────────┘
       │                                               │
┌──────▼───────────────────────────────────────────────▼───────┐
│                      Validator Registry                       │
│  (Plugin system for language-specific validators)             │
└──────┬────────────────────────────────────────────────┬──────┘
       │                                                 │
┌──────▼────────────────┐                    ┌──────────▼───────┐
│  Python Validators    │                    │  C++ Validators  │
│  - flake8             │                    │  - clang-tidy    │
│  - black              │                    │  - clang-format  │
│  - isort              │                    │  - cppcheck      │
│  - pylint             │                    │  - cpplint       │
│  - radon              │                    │  - include-what- │
│  - vulture            │                    │    you-use       │
│  - autoflake          │                    │  - Google Test   │
│  - pytest + coverage  │                    │                  │
└───────────┬───────────┘                    └──────────┬───────┘
            │                                           │
            └───────────────────┬───────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Result Parsers        │
                    │  (Extract structured   │
                    │   data from output)    │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  Statistics Database   │
                    │  (Track history,       │
                    │   success rates)       │
                    └────────────────────────┘
```

### Core Components

#### 1. Validator Interface (Abstract Base)

All validators implement a common interface:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ValidationResult:
    """Result from a single validator."""
    validator_name: str
    passed: bool
    errors: List[Dict[str, Any]]  # Each error has: file, line, message, severity
    warnings: List[Dict[str, Any]]
    execution_time: float
    files_checked: int

class Validator(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def name(self) -> str:
        """Return validator name (e.g., 'flake8', 'clang-tidy')."""
        pass

    @abstractmethod
    def language(self) -> str:
        """Return supported language (e.g., 'python', 'cpp')."""
        pass

    @abstractmethod
    def validate(self, files: List[str], config: Dict[str, Any]) -> ValidationResult:
        """Run validation on specified files with given configuration."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if validator tool is installed and available."""
        pass
```

#### 2. Language Detector

Automatically detects languages in the project:

```python
class LanguageDetector:
    """Detects programming languages in a project."""

    def detect_languages(self, project_path: str) -> List[str]:
        """Returns list of detected languages (e.g., ['python', 'cpp'])."""
        pass

    def get_files_for_language(self, project_path: str, language: str) -> List[str]:
        """Returns list of files for a specific language."""
        pass
```

Patterns:
- **Python**: `**/*.py`
- **C++**: `**/*.{cpp,cc,cxx,c++,hpp,h,hh,hxx,h++}`

#### 3. Configuration Manager

Handles configuration loading and validation:

```python
class ConfigurationManager:
    """Manages Anvil configuration."""

    def load_config(self, config_path: str = "anvil.toml") -> Dict[str, Any]:
        """Load and validate configuration from TOML file."""
        pass

    def get_validator_config(self, validator_name: str) -> Dict[str, Any]:
        """Get configuration for a specific validator."""
        pass

    def get_language_config(self, language: str) -> Dict[str, Any]:
        """Get configuration for a specific language."""
        pass
```

#### 4. Validation Orchestrator

Coordinates all validators:

```python
class ValidationOrchestrator:
    """Orchestrates validation across all configured validators."""

    def run_all_validators(self, incremental: bool = False) -> Dict[str, ValidationResult]:
        """Run all configured validators."""
        pass

    def run_language_validators(self, language: str, incremental: bool = False) -> Dict[str, ValidationResult]:
        """Run validators for a specific language."""
        pass

    def aggregate_results(self, results: Dict[str, ValidationResult]) -> bool:
        """Aggregate results and determine overall pass/fail."""
        pass
```

---

## Configuration Format

### File: `anvil.toml`

```toml
[anvil]
# General settings
languages = ["python", "cpp"]  # Auto-detect if not specified
incremental = true              # Only check modified files
fail_fast = false               # Stop on first failure
parallel = true                 # Run validators in parallel

# Quality gates (overall)
max_errors = 0                  # Maximum allowed errors (0 = none)
max_warnings = 10               # Maximum allowed warnings

# Python configuration
[anvil.python]
enabled = true
file_patterns = ["**/*.py"]

# Python validators
[anvil.python.flake8]
enabled = true
max_line_length = 100
ignore = ["E203", "W503"]

[anvil.python.black]
enabled = true
line_length = 100

[anvil.python.isort]
enabled = true
profile = "black"
line_length = 100

[anvil.python.pylint]
enabled = true
max_complexity = 10
disable = ["C0111"]  # Missing docstring

[anvil.python.radon]
enabled = true
max_complexity = 10  # Cyclomatic complexity threshold

[anvil.python.vulture]
enabled = true
min_confidence = 80  # Minimum confidence for dead code detection

[anvil.python.autoflake]
enabled = true
check_only = true  # Don't modify files, just report

[anvil.python.pytest]
enabled = true
coverage_threshold = 90.0  # Minimum coverage percentage
coverage_per_module = 85.0 # Minimum per-module coverage

# C++ configuration
[anvil.cpp]
enabled = true
file_patterns = ["**/*.{cpp,hpp,cc,h,cxx,hxx}"]
standard = "c++17"  # C++ standard (c++11, c++14, c++17, c++20, c++23)

# C++ validators
[anvil.cpp.clang-tidy]
enabled = true
checks = [
    "bugprone-*",
    "cert-*",
    "cppcoreguidelines-*",
    "modernize-*",
    "performance-*",
    "readability-*",
]
header_filter = ".*"  # Regex for headers to check

[anvil.cpp.clang-format]
enabled = true
style = "Google"  # Google, LLVM, Chromium, Mozilla, WebKit, or file:.clang-format

[anvil.cpp.cppcheck]
enabled = true
enable = ["warning", "style", "performance", "portability"]
suppress = []  # Suppression patterns

[anvil.cpp.cpplint]
enabled = true
filter = ["-whitespace/indent"]  # Filters to disable

[anvil.cpp.iwyu]  # include-what-you-use
enabled = false  # Optional, can be slow
mapping_file = ""  # Custom mapping file

[anvil.cpp.gtest]  # Google Test
enabled = true
test_filter = "*"  # Run all tests
timeout = 300      # Timeout in seconds

# Git hook configuration
[anvil.git-hooks]
pre_commit = true  # Install pre-commit hook
pre_push = false   # Install pre-push hook
bypass_keyword = "ANVIL_SKIP"  # Commit message keyword to bypass
```

### Minimal Configuration

For simple projects, minimal config:

```toml
[anvil]
# That's it! Anvil will:
# - Auto-detect languages (Python, C++)
# - Enable default validators
# - Use sensible defaults
```

---

## CLI Interface

### Commands

#### `anvil check`

Run all configured validators:

```bash
# Run all validators
anvil check

# Run incrementally (only changed files)
anvil check --incremental

# Run only Python validators
anvil check --language python

# Run specific validator
anvil check --validator flake8

# Verbose output
anvil check --verbose

# Quiet mode (errors only)
anvil check --quiet
```

#### `anvil install-hooks`

Install git hooks:

```bash
# Install pre-commit hook
anvil install-hooks

# Install pre-push hook
anvil install-hooks --pre-push

# Uninstall hooks
anvil install-hooks --uninstall
```

#### `anvil config`

Configuration management:

```bash
# Show current configuration
anvil config show

# Validate configuration file
anvil config validate

# Generate default configuration
anvil config init

# Check which validators are available
anvil config check-tools
```

#### `anvil list`

List available validators:

```bash
# List all validators
anvil list

# List Python validators
anvil list --language python

# List C++ validators
anvil list --language cpp

# Show validator details
anvil list --detailed
```

### Exit Codes

- `0`: All validations passed
- `1`: Validation failures (errors found)
- `2`: Configuration error
- `3`: Missing tools (validators not installed)
- `4`: Runtime error

---

## Validator Details

This section documents all configuration options and parseable output data for each validator. Configuration options control how the validator runs, while output data describes what information can be extracted from validation results.

### Python Validators

#### 1. flake8 - Syntax & Style Checker

**Purpose**: Detects Python syntax errors, PEP 8 style violations, programming errors, and code complexity issues through a combination of PyFlakes, pycodestyle, and McCabe complexity checker.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **max_line_length**: Maximum allowed line length in characters (integer, default: 79, recommended: 100)
- **max_doc_length**: Maximum allowed documentation line length (integer, default: none)
- **ignore**: List of error codes to ignore (list of strings, e.g., ["E203", "W503"])
- **extend_ignore**: Additional error codes to ignore beyond defaults (list of strings)
- **select**: Explicitly select specific error codes (list of strings)
- **extend_select**: Additional error codes to enable (list of strings)
- **exclude**: File patterns to exclude from checking (list of globs, e.g., [".git", "__pycache__", "*.egg-info"])
- **extend_exclude**: Additional exclusion patterns (list of globs)
- **max_complexity**: Maximum McCabe cyclomatic complexity (integer, default: 10)
- **per_file_ignores**: Ignore specific errors for specific files (dictionary mapping file patterns to error codes)
- **count**: Show count of violations (boolean, default: true)
- **statistics**: Show statistics about violations (boolean, default: false)
- **show_source**: Show source code for each violation (boolean, default: false)
- **format**: Output format - text, json, or pylint-style (string, default: "json")
- **jobs**: Number of parallel jobs for checking (integer, default: auto)
- **inline_quotes**: Preferred quote style - single or double (string)
- **docstring_convention**: Docstring convention to enforce - pep257, numpy, google (string)

**Parseable Output Data**:

- **file_path**: Path to file containing the issue (string, relative to project root)
- **line_number**: Line number where issue occurs (integer)
- **column_number**: Column number where issue starts (integer)
- **error_code**: Flake8 error code (string, e.g., "E501", "W503", "F401")
- **error_category**: Category of error - E (errors), W (warnings), F (PyFlakes), C (complexity), N (naming)
- **message**: Human-readable description of the issue (string)
- **physical_line**: The actual source code line with the issue (string)
- **severity**: Categorized severity - error, warning, or info (string)
- **rule_name**: Name of the violated rule (string)
- **total_violations**: Count of all violations across all files (integer)
- **violations_per_file**: Dictionary mapping file paths to violation counts (dict)
- **violations_by_type**: Count of violations grouped by error code (dict)

#### 2. black - Code Formatter Checker

**Purpose**: Enforces consistent Python code formatting by checking compliance with the opinionated Black code style. Black reformats code to a deterministic style, eliminating formatting debates.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **line_length**: Maximum line length (integer, default: 88, recommended for consistency with team standards)
- **target_version**: Python versions to target (list of strings: ["py38", "py39", "py310", "py311", "py312"])
- **skip_string_normalization**: Don't normalize string quotes (boolean, default: false)
- **skip_magic_trailing_comma**: Don't use trailing commas as split hint (boolean, default: false)
- **preview**: Enable preview features (boolean, default: false)
- **exclude**: File patterns to exclude (string regex pattern)
- **extend_exclude**: Additional exclusion patterns (string regex)
- **force_exclude**: Patterns to force-exclude even if in arguments (string regex)
- **include**: Include only files matching pattern (string regex, default: "\\.pyi?$")
- **quiet**: Suppress output (boolean, default: false)
- **verbose**: Verbose output (boolean, default: false)
- **check_only**: Only check, don't modify files (boolean, default: true for validation)
- **diff**: Show diffs of what would change (boolean, default: false)
- **color**: Use color in output (boolean, default: auto-detect)
- **fast**: Skip AST safety checks (boolean, default: false)
- **workers**: Number of parallel workers (integer, default: auto)

**Parseable Output Data**:

- **file_path**: Path to file that needs formatting (string)
- **needs_formatting**: Whether file requires reformatting (boolean)
- **diff**: Text diff showing what would change (string, multi-line)
- **total_files_checked**: Number of files analyzed (integer)
- **files_need_formatting**: Count of files needing changes (integer)
- **files_already_formatted**: Count of files already compliant (integer)
- **files_failed**: Files that couldn't be parsed (integer)
- **error_message**: Parser error if file has syntax issues (string)
- **suggested_command**: Command to fix the issue (string, e.g., "black src/file.py")
- **would_reformat**: List of file paths that would be reformatted (list of strings)
- **left_unchanged**: List of file paths already properly formatted (list of strings)

#### 3. isort - Import Sorter Checker

**Purpose**: Checks and enforces consistent import statement ordering and grouping according to configurable styles (black, google, pep8, etc.). Helps maintain clean, organized import sections.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **profile**: Preset configuration profile (string: "black", "django", "pycharm", "google", "open_stack", "plone", "attrs", "hug", "wemake", "appnexus")
- **line_length**: Maximum line length for imports (integer, default: 79)
- **multi_line_output**: Multi-line import style (integer 0-10, default: 3 for vertical hanging indent)
- **force_single_line**: Force each import on its own line (boolean, default: false)
- **force_alphabetical_sort**: Sort imports alphabetically within sections (boolean, default: false)
- **force_sort_within_sections**: Sort imports within their section (boolean, default: false)
- **skip**: Files to skip (list of globs, e.g., ["__init__.py", "migrations/"])
- **skip_glob**: Additional glob patterns to skip (list of globs)
- **extend_skip**: Additional files to skip (list of strings)
- **skip_gitignore**: Skip files in .gitignore (boolean, default: false)
- **sections**: Custom import sections (list: ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"])
- **known_first_party**: Modules to treat as first-party (list of strings)
- **known_third_party**: Modules to treat as third-party (list of strings)
- **known_local_folder**: Modules in local folder (list of strings)
- **extra_standard_library**: Additional stdlib modules (list of strings)
- **src_paths**: Source paths for resolving first-party imports (list of paths)
- **forced_separate**: Modules to separate into own section (list of strings)
- **indent**: Indent string (string, default: "    ")
- **length_sort**: Sort imports by length (boolean, default: false)
- **length_sort_straight**: Sort all imports by length (boolean, default: false)
- **combine_as_imports**: Combine "as" imports on same line (boolean, default: false)
- **include_trailing_comma**: Add trailing comma to multi-line imports (boolean, default: false)
- **use_parentheses**: Use parentheses for line continuation (boolean, default: true)
- **ensure_newline_before_comments**: Ensure newline before comments (boolean, default: true)
- **case_sensitive**: Sort case-sensitively (boolean, default: false)
- **check_only**: Only check, don't modify (boolean, default: true)
- **diff**: Show diff of changes (boolean, default: false)
- **color**: Use colored output (boolean, default: auto)

**Parseable Output Data**:

- **file_path**: Path to file with incorrect import order (string)
- **needs_sorting**: Whether imports need reordering (boolean)
- **diff**: Diff showing how imports should be reorganized (string)
- **current_imports**: Current import section as text (string)
- **corrected_imports**: How imports should look (string)
- **total_files_checked**: Number of files examined (integer)
- **files_need_sorting**: Count of files with incorrect ordering (integer)
- **files_already_sorted**: Count of files with correct ordering (integer)
- **error_message**: Error if file couldn't be parsed (string)
- **suggested_command**: Command to fix (string, e.g., "isort src/file.py")
- **incorrectly_sorted**: List of files needing sorting (list of strings)

#### 4. pylint - Static Analysis

**Purpose**: Comprehensive static code analyzer that checks for errors, enforces coding standards, detects code smells, and provides refactoring suggestions. Most thorough Python linter with extensive checks.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **rcfile**: Path to pylint configuration file (string, default: ".pylintrc" if exists)
- **max_line_length**: Maximum line length (integer, default: 100)
- **max_module_lines**: Maximum lines per module (integer, default: 1000)
- **max_complexity**: Maximum cyclomatic complexity per function (integer, default: 10)
- **max_args**: Maximum function arguments (integer, default: 5)
- **max_locals**: Maximum local variables per function (integer, default: 15)
- **max_returns**: Maximum return statements per function (integer, default: 6)
- **max_branches**: Maximum branches per function (integer, default: 12)
- **max_statements**: Maximum statements per function (integer, default: 50)
- **max_attributes**: Maximum attributes per class (integer, default: 7)
- **max_public_methods**: Maximum public methods per class (integer, default: 20)
- **max_bool_expr**: Maximum boolean expressions per condition (integer, default: 5)
- **min_similarity_lines**: Minimum lines for similarity check (integer, default: 4)
- **disable**: Message IDs or categories to disable (list of strings, e.g., ["C0111", "missing-docstring"])
- **enable**: Message IDs to explicitly enable (list of strings)
- **ignore**: Files/directories to ignore (list of strings)
- **ignore_patterns**: Regex patterns to ignore (list of regex strings)
- **ignore_paths**: Path patterns to ignore (list of strings)
- **extension_pkg_allow_list**: Packages to allow C extension loading (list of strings)
- **jobs**: Number of parallel processes (integer, default: 1)
- **score**: Display score (boolean, default: true)
- **fail_under**: Minimum score to pass (float, default: 10.0)
- **confidence**: Confidence levels to show (list: ["HIGH", "INFERENCE", "INFERENCE_FAILURE", "UNDEFINED"])
- **output_format**: Output format (string: "text", "json", "parseable", "colorized", "msvs")
- **good_names**: Accepted short variable names (list of strings, default: ["i", "j", "k", "ex", "Run", "_"])
- **bad_names**: Forbidden variable names (list of strings)
- **include_naming_hint**: Include naming hint in message (boolean, default: false)
- **const_rgx**: Regular expression for constant names (string)
- **class_rgx**: Regular expression for class names (string)
- **function_rgx**: Regular expression for function names (string)
- **method_rgx**: Regular expression for method names (string)
- **attr_rgx**: Regular expression for attribute names (string)
- **argument_rgx**: Regular expression for argument names (string)
- **variable_rgx**: Regular expression for variable names (string)
- **docstring_min_length**: Minimum function length requiring docstring (integer, default: -1)
- **notes**: Tags to look for in comments (list of strings: ["FIXME", "XXX", "TODO"])

**Parseable Output Data**:

- **file_path**: File containing the issue (string)
- **module_name**: Python module name (string)
- **object_name**: Function/class/method name where issue occurs (string)
- **line_number**: Line number (integer)
- **column_number**: Column number (integer)
- **end_line**: Ending line for multi-line issues (integer)
- **end_column**: Ending column (integer)
- **message_id**: Pylint message code (string, e.g., "W0613", "C0103")
- **symbol**: Symbolic name of the message (string, e.g., "unused-argument", "invalid-name")
- **message**: Human-readable message (string)
- **message_type**: Type category (string: "convention", "refactor", "warning", "error", "fatal")
- **severity**: Categorized as error, warning, or info (string)
- **confidence**: Confidence level (string: "HIGH", "INFERENCE", etc.)
- **overall_score**: Code quality score out of 10 (float)
- **previous_score**: Score from previous run if available (float)
- **score_change**: Difference from previous score (float)
- **statements_analyzed**: Total statements in codebase (integer)
- **violations_by_type**: Count of violations per message type (dict)
- **violations_by_category**: Count by category (convention, refactor, warning, error) (dict)
- **most_common_violations**: Top violation types by frequency (list of tuples)
- **files_with_violations**: Files that have any violations (list of strings)
- **clean_files**: Files with no violations (list of strings)

#### 5. radon - Complexity Analyzer

**Purpose**: Measures code complexity metrics including cyclomatic complexity, maintainability index, and raw metrics (LOC, LLOC, comments). Helps identify overly complex code that needs refactoring.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **max_complexity**: Maximum allowed cyclomatic complexity (integer, default: 10, corresponds to grade B)
- **min_complexity_grade**: Minimum acceptable complexity grade (string: "A", "B", "C", "D", "E", "F"; default: "B")
- **show_complexity**: Report complexity for all functions (boolean, default: true)
- **show_closures**: Include closures and lambdas (boolean, default: false)
- **order**: Sorting order (string: "SCORE" for complexity score, "ALPHA" for alphabetical)
- **json_output**: Output as JSON (boolean, default: true)
- **include_ipynb**: Include Jupyter notebooks (boolean, default: false)
- **exclude**: Comma-separated patterns to exclude (string)
- **ignore**: Comma-separated patterns to ignore (string)
- **no_assert**: Don't count assert statements (boolean, default: false)
- **show_mi**: Calculate maintainability index (boolean, default: true)
- **mi_threshold**: Minimum maintainability index (integer, default: 20, scale 0-100)
- **multi**: Run all metrics (CC, raw, MI) (boolean, default: false)
- **total_average**: Show average complexity (boolean, default: true)
- **raw_metrics**: Include raw metrics (LOC, LLOC, etc.) (boolean, default: false)

**Parseable Output Data**:

- **file_path**: File being analyzed (string)
- **function_name**: Name of function/method (string)
- **line_number**: Starting line of function (integer)
- **column_offset**: Column offset (integer)
- **end_line**: Ending line of function (integer)
- **complexity**: Cyclomatic complexity score (integer)
- **complexity_rank**: Letter grade (string: "A" for 1-5, "B" for 6-10, "C" for 11-20, "D" for 21-30, "E" for 31-40, "F" for 41+)
- **is_method**: Whether it's a class method (boolean)
- **is_classmethod**: Whether it's a @classmethod (boolean)
- **is_staticmethod**: Whether it's a @staticmethod (boolean)
- **function_type**: Type of callable (string: "function", "method", "closure", "lambda")
- **average_complexity**: Average complexity across all functions (float)
- **total_complexity**: Sum of all complexity scores (integer)
- **functions_analyzed**: Number of functions checked (integer)
- **maintainability_index**: MI score 0-100 (float, higher is better)
- **mi_rank**: Maintainability grade (string: "A", "B", "C")
- **lines_of_code**: Total lines including comments/blanks (integer)
- **logical_lines**: Logical lines of code (integer)
- **source_lines**: Lines with actual code (integer)
- **comment_lines**: Lines with comments (integer)
- **blank_lines**: Empty lines (integer)
- **single_comment_lines**: Single-line comments (integer)
- **multi_comment_lines**: Multi-line comments count (integer)
- **complexity_by_grade**: Count of functions per grade (dict)
- **high_complexity_functions**: List of functions exceeding threshold (list)

#### 6. vulture - Dead Code Detector

**Purpose**: Identifies unused code including functions, methods, classes, variables, imports, and properties. Helps maintain clean codebases by finding code that can be safely removed.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **min_confidence**: Minimum confidence level to report (integer 0-100, default: 80)
- **exclude**: Patterns to exclude (list of globs)
- **ignore_decorators**: Decorators that mark code as used (list of strings, e.g., ["@app.route", "@celery.task"])
- **ignore_names**: Names to never report as unused (list of strings or regex patterns)
- **make_whitelist**: Generate whitelist from false positives (boolean, default: false)
- **sort_by_size**: Sort results by lines of code (boolean, default: false)
- **paths**: Specific paths to check (list of strings)
- **verbose**: Include more details (boolean, default: false)

**Parseable Output Data**:

- **file_path**: File containing unused code (string)
- **line_number**: Line where unused item is defined (integer)
- **item_type**: Type of unused item (string: "function", "method", "class", "variable", "property", "import", "attribute")
- **item_name**: Name of the unused item (string)
- **confidence**: Confidence percentage (integer 0-100)
- **message**: Description (string, e.g., "unused function 'old_helper'")
- **size**: Number of lines the unused item occupies (integer)
- **first_line**: First line of the unused code block (integer)
- **last_line**: Last line of the unused code block (integer)
- **total_unused_items**: Count of all unused items found (integer)
- **unused_by_type**: Count grouped by item type (dict)
- **high_confidence_items**: Items with confidence >= 90 (list)
- **medium_confidence_items**: Items with confidence 70-89 (list)
- **low_confidence_items**: Items with confidence < 70 (list)
- **total_unused_lines**: Sum of lines for all unused code (integer)
- **potential_savings**: Estimated percentage of code that could be removed (float)

#### 7. autoflake - Unused Code Remover (Check Mode)

**Purpose**: Detects unused imports and unused variables in Python code. More focused than vulture, specifically targeting common cases of leftover imports and variables after refactoring.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **check_only**: Only report issues, don't modify files (boolean, default: true for validation)
- **remove_unused_variables**: Check for unused variables (boolean, default: true)
- **remove_all_unused_imports**: Remove all unused imports (boolean, default: true)
- **ignore_init_module_imports**: Keep imports in __init__.py (boolean, default: false)
- **remove_duplicate_keys**: Check for duplicate dict keys (boolean, default: true)
- **expand_star_imports**: Expand star imports (boolean, default: false)
- **exclude**: Files to exclude (list of globs)
- **imports**: Specific imports to remove (list of strings)
- **ignore_pass_statements**: Leave pass statements (boolean, default: false)
- **ignore_pass_after_docstring**: Keep pass after docstring (boolean, default: false)
- **in_place**: Modify files in place (boolean, default: false)
- **recursive**: Check directories recursively (boolean, default: true)
- **jobs**: Number of parallel jobs (integer, default: 1)

**Parseable Output Data**:

- **file_path**: File with unused code (string)
- **line_number**: Line number of unused item (integer)
- **item_type**: Type of item (string: "import", "variable")
- **item_name**: Name of unused item (string)
- **message**: Description (string)
- **is_unused_import**: Whether it's an unused import (boolean)
- **is_unused_variable**: Whether it's an unused variable (boolean)
- **import_module**: Module name for unused imports (string)
- **total_files_checked**: Files analyzed (integer)
- **files_with_issues**: Files containing unused code (integer)
- **total_unused_imports**: Count of unused imports (integer)
- **total_unused_variables**: Count of unused variables (integer)
- **suggested_removals**: Lines that could be removed (list of tuples: (file, line))

#### 8. pytest - Test Runner with Coverage

**Purpose**: Executes Python unit tests and measures code coverage. Verifies that tests pass and that sufficient code is covered by tests. Supports various test frameworks and plugins.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **coverage_threshold**: Minimum overall coverage percentage (float, default: 90.0)
- **coverage_per_module**: Minimum per-file coverage percentage (float, default: 85.0)
- **test_pattern**: Pattern for test files (string, default: "test_*.py")
- **test_paths**: Directories containing tests (list of strings, default: ["tests/"])
- **source_paths**: Source directories to measure coverage (list of strings, default: ["src/"])
- **markers**: Pytest markers to run/skip (list of strings, e.g., ["not slow", "unit"])
- **keywords**: Test name patterns to run (string, e.g., "-k 'test_user and not test_admin'")
- **verbose**: Verbosity level (integer 0-2, default: 1)
- **capture**: Output capture method (string: "no", "sys", "fd"; default: "fd")
- **maxfail**: Stop after N failures (integer, default: 0 for no limit)
- **strict_markers**: Raise error on unknown markers (boolean, default: false)
- **junit_xml**: Generate JUnit XML report (string, path to output file)
- **html_report**: Generate HTML coverage report (string, directory path)
- **json_report**: Generate JSON report (boolean, default: true)
- **cov_report_formats**: Coverage report formats (list: ["term", "html", "xml", "json"])
- **cov_fail_under**: Fail if coverage below threshold (float)
- **cov_branch**: Enable branch coverage (boolean, default: false)
- **cov_context**: Enable coverage contexts (string: "test", "module")
- **durations**: Show N slowest tests (integer, default: 0)
- **timeout**: Test timeout in seconds (integer, default: 300)
- **timeout_method**: Timeout method (string: "thread", "signal")
- **reruns**: Number of times to rerun failed tests (integer, default: 0)
- **reruns_delay**: Delay between reruns in seconds (float, default: 0)
- **parallel_workers**: Number of parallel test workers (integer, default: 1)
- **dist_mode**: Parallel distribution mode (string: "load", "loadscope", "loadfile", "no")
- **stepwise**: Exit on first failure, continue from last failure next run (boolean, default: false)
- **last_failed**: Run only tests that failed last time (boolean, default: false)
- **failed_first**: Run failed tests first, then others (boolean, default: false)
- **new_first**: Run new tests first (boolean, default: false)
- **cache_clear**: Clear cache before running (boolean, default: false)
- **collect_only**: Only collect tests, don't run (boolean, default: false)
- **disable_warnings**: Disable warning summary (boolean, default: false)

**Parseable Output Data**:

- **test_node_id**: Full test identifier (string, e.g., "tests/test_parser.py::TestParser::test_validate")
- **test_file**: File containing the test (string)
- **test_class**: Test class name if applicable (string)
- **test_function**: Test function/method name (string)
- **test_parameters**: Test parameters for parametrized tests (dict)
- **outcome**: Test result (string: "passed", "failed", "skipped", "xfailed", "xpassed", "error")
- **duration**: Test execution time in seconds (float)
- **setup_duration**: Setup phase duration (float)
- **call_duration**: Test call phase duration (float)
- **teardown_duration**: Teardown phase duration (float)
- **failure_message**: Error message if test failed (string, multi-line)
- **failure_traceback**: Full traceback for failures (string, multi-line)
- **failure_type**: Exception type (string)
- **failure_line**: Line number where failure occurred (integer)
- **skip_reason**: Reason for skipping test (string)
- **markers**: Test markers applied (list of strings)
- **keywords**: Test keywords (list of strings)
- **total_tests**: Total number of tests collected (integer)
- **tests_passed**: Count of passed tests (integer)
- **tests_failed**: Count of failed tests (integer)
- **tests_skipped**: Count of skipped tests (integer)
- **tests_xfailed**: Expected failures (integer)
- **tests_xpassed**: Unexpected passes (integer)
- **tests_error**: Tests with errors (integer)
- **total_duration**: Total test run time (float)
- **coverage_percentage**: Overall coverage (float, 0-100)
- **coverage_lines_covered**: Lines covered by tests (integer)
- **coverage_lines_total**: Total lines in source (integer)
- **coverage_lines_missing**: Lines not covered (integer)
- **coverage_branches_covered**: Branches covered (integer, if branch coverage enabled)
- **coverage_branches_total**: Total branches (integer)
- **coverage_per_file**: Coverage by file (dict: filename -> percentage)
- **files_below_threshold**: Files below coverage threshold (list)
- **missing_lines_by_file**: Missing line numbers per file (dict: filename -> list of line ranges)
- **slowest_tests**: N slowest tests with durations (list of tuples)
- **flaky_tests_detected**: Tests that passed after retry (list)

### C++ Validators

#### 9. clang-tidy - Static Analyzer

**Purpose**: Performs comprehensive static analysis of C++ code, detecting bugs, performance issues, modernization opportunities, and style violations. Part of the LLVM project, highly configurable.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **checks**: Check categories to enable (list of strings with wildcards, e.g., ["bugprone-*", "modernize-*", "-modernize-use-trailing-return-type"])
- **header_filter**: Regex for headers to analyze (string, default: ".*" for all)
- **warnings_as_errors**: Treat warnings as errors (boolean or string with check patterns, default: false)
- **system_headers**: Check system headers (boolean, default: false)
- **format_style**: Code format style for fixes (string: "llvm", "google", "chromium", "mozilla", "webkit", "file", "none")
- **use_color**: Colored output (boolean, default: auto)
- **config**: Inline configuration overrides (string, YAML format)
- **config_file**: Path to .clang-tidy config (string)
- **line_filter**: JSON array of line ranges to check (string, JSON format)
- **extra_args**: Additional compiler arguments (list of strings, e.g., ["-std=c++17", "-I/path/to/includes"])
- **extra_arg_before**: Args to prepend before -- separator (list of strings)
- **compile_commands_dir**: Path to compile_commands.json directory (string)
- **p**: Alias for compile_commands_dir (string)
- **export_fixes**: YAML file to export suggested fixes (string, path)
- **fix**: Apply suggested fixes (boolean, default: false for validation)
- **fix_errors**: Apply fixes even if compilation errors (boolean, default: false)
- **fix_notes**: Apply fixes from notes (boolean, default: false)
- **allow_enabling_analyzer_alpha_checkers**: Allow alpha checkers (boolean, default: false)
- **list_checks**: Only list available checks (boolean, default: false)
- **explain_config**: Print effective configuration (boolean, default: false)
- **quiet**: Suppress progress output (boolean, default: false)
- **vfsoverlay**: Virtual filesystem overlay (string, path to YAML)

**Parseable Output Data**:

- **file_path**: Source file with issue (string)
- **line_number**: Line number (integer)
- **column_number**: Column number (integer)
- **severity**: Issue severity (string: "error", "warning", "note")
- **check_name**: Name of the check (string, e.g., "modernize-use-nullptr", "bugprone-use-after-move")
- **message**: Diagnostic message (string)
- **diagnostic_level**: Level (string: "Error", "Warning", "Note")
- **replacement_available**: Whether automatic fix exists (boolean)
- **replacement_text**: Suggested replacement code (string)
- **replacement_offset**: File offset for replacement (integer)
- **replacement_length**: Length of code to replace (integer)
- **context_before**: Lines before the issue (string)
- **context_after**: Lines after the issue (string)
- **is_from_header**: Whether issue is in header file (boolean)
- **is_from_system_header**: Whether from system header (boolean)
- **total_diagnostics**: Total issues found (integer)
- **diagnostics_by_severity**: Count per severity (dict)
- **diagnostics_by_check**: Count per check name (dict)
- **files_analyzed**: Number of files checked (integer)
- **files_with_issues**: Files containing issues (integer)
- **fixable_diagnostics**: Count of issues with automatic fixes (integer)
- **fixes_exported**: Whether fixes were exported to YAML (boolean)
- **fixes_applied**: Whether fixes were applied (boolean for fix mode)

#### 10. clang-format - Code Formatter Checker

**Purpose**: Checks C++ code formatting compliance against specified style guides (Google, LLVM, Mozilla, Chromium, WebKit, or custom). Ensures consistent formatting across codebase.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **style**: Format style (string: "LLVM", "Google", "Chromium", "Mozilla", "WebKit", "Microsoft", "GNU", or "file" to use .clang-format file)
- **fallback_style**: Style to use if file style not found (string, one of above styles, default: "LLVM")
- **assume_filename**: Assume this filename for style selection (string)
- **cursor**: Cursor position for calculating new cursor after formatting (integer)
- **dry_run**: Check only, don't modify (boolean, default: true for validation)
- **ferror_limit**: Maximum formatting errors (integer, default: 0 for unlimited)
- **files**: Files to check (list of strings)
- **length**: Format only a range (integer, length in bytes)
- **offset**: Format starting at offset (integer, byte offset)
- **lines**: Line ranges to format (list of strings, e.g., ["10:20", "30:40"])
- **output_replacements_xml**: Output replacements in XML (boolean, default: false)
- **sort_includes**: Sort include directives (boolean, default: false)
- **verbose**: Verbose output (boolean, default: false)
- **Werror**: Treat warnings as errors (boolean, default: true)
- **dump_config**: Dump effective configuration (boolean, default: false)

**Parseable Output Data**:

- **file_path**: File that needs formatting (string)
- **needs_formatting**: Whether formatting required (boolean)
- **diff**: Unified diff of changes (string, multi-line)
- **replacements**: List of specific changes needed (list of dicts with offset, length, text)
- **total_files_checked**: Files examined (integer)
- **files_need_formatting**: Count needing changes (integer)
- **files_properly_formatted**: Count already compliant (integer)
- **format_errors**: Files with formatting errors (integer)
- **suggested_command**: Command to fix (string, e.g., "clang-format -i src/engine.cpp")
- **exit_code**: Tool exit code (integer: 0 = formatted, 1 = needs formatting)
- **xml_replacements**: XML-formatted replacements if enabled (string, XML)

#### 11. cppcheck - Static Analyzer

**Purpose**: Static analysis tool for C/C++ that detects bugs, undefined behavior, dangerous coding constructs, and suggests optimizations. Complements compiler warnings.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **enable**: Analysis types to enable (list: ["all", "warning", "style", "performance", "portability", "information", "unusedFunction", "missingInclude"])
- **inconclusive**: Show inconclusive results (boolean, default: false)
- **std**: C/C++ standard (string: "c89", "c99", "c11", "c17", "c++03", "c++11", "c++14", "c++17", "c++20", "c++23")
- **platform**: Target platform (string: "unix32", "unix64", "win32A", "win32W", "win64", "native", "unspecified")
- **suppress**: Suppression rules (list of strings, format: "errorId:file:line" or "errorId")
- **suppressions_list**: Path to suppressions file (string)
- **inline_suppr**: Enable inline suppressions via comments (boolean, default: true)
- **exitcode_suppressions**: Suppression file for exit codes (string, path)
- **template**: Output format template (string, custom or "gcc", "vs", "edit", "cppcheck1")
- **error_exitcode**: Exit code for errors (integer, default: 1)
- **force**: Force checking even if issues detected (boolean, default: false)
- **quiet**: Minimal output (boolean, default: false)
- **verbose**: Verbose output (boolean, default: false)
- **check_config**: Check configuration (boolean, default: false)
- **check_library**: Check library configurations (boolean, default: false)
- **dump**: Dump data for add-ons (boolean, default: false)
- **includes_file**: Include paths file (string, path)
- **include_paths**: Include directories (list of strings)
- **define**: Preprocessor definitions (list of strings, e.g., ["DEBUG=1", "USE_SSL"])
- **undefine**: Preprocessor undefinitions (list of strings)
- **max_ctu_depth**: Max depth for whole program analysis (integer, default: 2)
- **max_configs**: Max configurations to check (integer, default: 12)
- **jobs**: Number of parallel threads (integer, default: 1)
- **library**: Load library configuration (list of strings, e.g., ["posix", "windows", "qt"])
- **output_file**: Output file instead of stdout (string, path)
- **xml**: XML output (boolean, default: true)
- **xml_version**: XML format version (integer: 1 or 2, default: 2)
- **file_list**: File with list of files to check (string, path)

**Parseable Output Data**:

- **file_path**: File with issue (string)
- **line_number**: Line number (integer)
- **column_number**: Column number (integer, if available)
- **severity**: Issue severity (string: "error", "warning", "style", "performance", "portability", "information")
- **error_id**: Error identifier (string, e.g., "nullPointer", "uninitvar", "memleak")
- **message**: Human-readable message (string)
- **verbose_message**: Detailed explanation (string)
- **is_inconclusive**: Whether result is inconclusive (boolean)
- **cwe_id**: CWE (Common Weakness Enumeration) ID if applicable (integer)
- **hash**: Hash for error suppression (string)
- **symbol**: Symbol name related to error (string)
- **total_errors**: Total error-level issues (integer)
- **total_warnings**: Total warning-level issues (integer)
- **total_style**: Total style issues (integer)
- **total_performance**: Total performance issues (integer)
- **total_portability**: Total portability issues (integer)
- **total_information**: Total info messages (integer)
- **errors_by_id**: Count per error ID (dict)
- **errors_by_file**: Count per file (dict)
- **files_analyzed**: Files checked (integer)
- **files_with_errors**: Files containing issues (integer)
- **suppressed_errors**: Errors suppressed (integer)

#### 12. cpplint - Style Checker

**Purpose**: Checks C++ code against Google's C++ Style Guide. Enforces naming conventions, formatting rules, and best practices. Originally from Google, widely adopted.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **linelength**: Maximum line length (integer, default: 80)
- **filter**: Categories to enable/disable (list of strings, format: "+category" or "-category", e.g., ["-whitespace/indent", "+readability/casting"])
- **counting**: Counting level (string: "total", "toplevel", "detailed", default: "total")
- **root**: Source root directory for header guard checking (string)
- **repository**: Repository root for version control (string)
- **output**: Output format (string: "emacs", "vs7", "eclipse", "junit", "sed", "gsed", default: "emacs")
- **verbose**: Verbosity level (integer 0-5, default: 1)
- **recursive**: Check subdirectories recursively (boolean, default: true)
- **exclude**: Files to exclude (list of globs)
- **extensions**: File extensions to check (list of strings, default: ["cc", "cpp", "cxx", "h", "hpp", "hxx"])
- **headers**: Header file extensions (list of strings, default: ["h", "hpp", "hxx"])
- **quiet**: Suppress output (boolean, default: false)

**Parseable Output Data**:

- **file_path**: File with style violation (string)
- **line_number**: Line number (integer)
- **category**: Style category (string, e.g., "whitespace/indent", "readability/braces", "build/include")
- **confidence**: Confidence level 1-5 (integer, 5 = most confident)
- **message**: Violation description (string)
- **severity**: Computed from confidence (string: "error" for 5, "warning" for 3-4, "info" for 1-2)
- **rule_name**: Full category path (string)
- **total_errors**: Total style violations (integer)
- **errors_by_category**: Count per category (dict)
- **errors_by_confidence**: Count per confidence level (dict)
- **files_checked**: Files analyzed (integer)
- **files_with_errors**: Files with violations (integer)
- **most_common_violations**: Top violations by frequency (list)

#### 13. include-what-you-use (IWYU) - Include Optimizer

**Purpose**: Analyzes C++ code to ensure that files directly include all headers they use and don't include headers they don't use. Reduces compilation times and clarifies dependencies.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: false, as it's optional)
- **mapping_file**: Custom mapping file for include paths (string, path to .imp file)
- **cxx**: C++ compiler flags (list of strings, e.g., ["-std=c++17", "-I/usr/include"])
- **check_also**: Additional globs to check (list of globs)
- **keep**: Globs of includes to always keep (list of globs)
- **max_line_length**: Maximum line length for includes (integer, default: 80)
- **no_comments**: Don't add "why" comments (boolean, default: false)
- **no_fwd_decls**: Don't suggest forward declarations (boolean, default: false)
- **transitive_includes_only**: Only show transitive includes (boolean, default: false)
- **prefix_header_includes**: Suggest includes for prefix header (string, "add", "remove", "keep")
- **pch_in_code**: Treat first include as PCH (boolean, default: false)
- **quoted_includes_first**: Sort quoted includes before angles (boolean, default: true)
- **verbose**: Verbose output (integer 1-7, default: 1)

**Parseable Output Data**:

- **file_path**: File being analyzed (string)
- **unnecessary_includes**: Headers that should be removed (list of strings)
- **missing_includes**: Headers that should be added (list of strings)
- **suggested_forward_declarations**: Forward decls to add instead of includes (list of strings)
- **line_number**: Line of include directive (integer)
- **include_type**: Type of include (string: "necessary", "unnecessary", "transitive")
- **reason**: Why include is needed/not needed (string)
- **symbol_used**: Symbol requiring the include (string)
- **suggested_replacement**: Alternative include (string)
- **total_includes_checked**: Total include directives (integer)
- **unnecessary_includes_count**: Count to remove (integer)
- **missing_includes_count**: Count to add (integer)
- **forward_decl_opportunities**: Count of forward decl suggestions (integer)
- **files_analyzed**: Files checked (integer)
- **files_needing_changes**: Files with suggestions (integer)

#### 14. Google Test (gtest) - Unit Test Framework

**Purpose**: Executes C++ unit tests built with Google Test framework. Provides detailed test results, failure information, and execution metrics.

**Configuration Parameters**:

- **enabled**: Enable or disable this validator (boolean, default: true)
- **test_executable**: Path to test binary (string, required)
- **test_filter**: Filter tests to run (string, pattern like "*EngineTest*", default: "*" for all)
- **test_exclude_filter**: Filter tests to exclude (string, pattern)
- **repeat**: Number of times to repeat tests (integer, default: 1)
- **shuffle**: Randomize test order (boolean, default: false)
- **random_seed**: Random seed for shuffling (integer, default: 0 for random)
- **output**: Output format and location (string, format "format:path", e.g., "json:results.json", "xml:results.xml")
- **gtest_color**: Colored output (string: "yes", "no", "auto", default: "auto")
- **gtest_print_time**: Print test execution times (boolean, default: true)
- **gtest_print_utf8**: Print UTF-8 characters (boolean, default: true)
- **gtest_death_test_style**: Death test style (string: "threadsafe", "fast", default: "fast")
- **gtest_break_on_failure**: Break debugger on failure (boolean, default: false)
- **gtest_catch_exceptions**: Catch exceptions (boolean, default: true)
- **gtest_throw_on_failure**: Throw on failure (boolean, default: false)
- **gtest_brief**: Brief output (boolean, default: false)
- **timeout**: Test timeout in seconds (integer, default: 300)
- **list_tests**: Only list tests, don't run (boolean, default: false)
- **also_run_disabled_tests**: Run disabled tests (boolean, default: false)
- **jobs**: Run tests in parallel (integer, number of jobs, default: 1)

**Parseable Output Data**:

- **test_suite_name**: Name of test suite/fixture (string, e.g., "EngineTest")
- **test_name**: Name of individual test (string, e.g., "ProcessInput")
- **full_test_name**: Combined name (string, "EngineTest.ProcessInput")
- **file_path**: File containing the test (string)
- **line_number**: Line number of test definition (integer)
- **status**: Test result (string: "RUN", "OK", "FAILED", "SKIPPED", "TIMEOUT")
- **result**: Final result (string: "COMPLETED", "FAILED", "SKIPPED", "TIMEOUT")
- **duration**: Execution time in seconds (float)
- **duration_ms**: Execution time in milliseconds (integer)
- **failure_message**: Assertion failure message (string, multi-line)
- **failure_type**: Type of failure (string)
- **failure_file**: File where assertion failed (string)
- **failure_line**: Line where assertion failed (integer)
- **expected_value**: Expected value in assertion (string)
- **actual_value**: Actual value in assertion (string)
- **total_tests**: Total tests in suite (integer)
- **tests_run**: Tests executed (integer)
- **tests_passed**: Successful tests (integer)
- **tests_failed**: Failed tests (integer)
- **tests_skipped**: Skipped/disabled tests (integer)
- **tests_disabled**: Disabled tests count (integer)
- **total_assertions**: Total assertions checked (integer)
- **failed_assertions**: Failed assertions (integer)
- **total_duration**: Total execution time (float)
- **timestamp**: Test run timestamp (string, ISO format)
- **test_suites_run**: Number of test suites executed (integer)
- **slowest_tests**: N slowest tests (list of tuples: (name, duration))
- **flaky_tests**: Tests that passed after retry (list, if retries enabled)

---

## Statistics & Historical Tracking

### Overview

Anvil maintains a statistics database to track validation history over time. This enables:
- **Flaky test detection**: Identify tests that pass/fail inconsistently
- **Problem prioritization**: Focus on consistently failing tests/validators
- **Trend analysis**: Track quality metrics over time
- **Intelligent filtering**: Skip tests/files with high success rates

### Statistics Database Schema

```python
class ValidationRun:
    """Record of a single validation run."""
    id: str                    # Unique run ID
    timestamp: datetime        # When validation ran
    incremental: bool          # Full or incremental run
    duration_seconds: float    # Total duration
    overall_status: str        # passed, failed, error
    git_commit: str           # Git commit hash (if available)
    git_branch: str           # Git branch name (if available)

class ValidatorRunRecord:
    """Record of a single validator execution."""
    run_id: str               # Links to ValidationRun
    validator_name: str       # e.g., 'pytest', 'clang-tidy'
    language: str             # e.g., 'python', 'cpp'
    status: str               # passed, failed, error, skipped
    errors: int               # Number of errors
    warnings: int             # Number of warnings
    files_checked: int        # Number of files checked
    duration_seconds: float   # Execution time
    timestamp: datetime       # When this validator ran

class TestCaseRecord:
    """Record of individual test case results."""
    run_id: str               # Links to ValidationRun
    validator_name: str       # e.g., 'pytest', 'gtest'
    test_file: str            # Test file path
    test_name: str            # Full test name (e.g., 'TestClass::test_method')
    status: str               # passed, failed, skipped, error
    duration_seconds: float   # Test execution time
    error_message: str        # Failure message (if failed)
    timestamp: datetime       # When test ran

class FileValidationRecord:
    """Record of validation results per file."""
    run_id: str               # Links to ValidationRun
    validator_name: str       # e.g., 'flake8', 'cppcheck'
    file_path: str            # Source file path
    status: str               # passed, failed, skipped
    errors: int               # Number of errors in file
    warnings: int             # Number of warnings in file
    issues: List[Dict]        # Detailed issues (line, code, message)
    timestamp: datetime       # When file was checked
```

### Statistics Queries

Anvil provides query capabilities for historical data:

```python
class StatisticsEngine:
    """Query and analyze validation statistics."""

    def get_test_success_rate(self, test_name: str, last_n_runs: int = 10) -> float:
        """Get success rate for a specific test over last N runs."""
        pass

    def get_flaky_tests(self, threshold: float = 0.7, last_n_runs: int = 20) -> List[str]:
        """Find tests with success rate below threshold (indicating flakiness)."""
        pass

    def get_file_error_frequency(self, file_path: str, last_n_runs: int = 10) -> Dict[str, int]:
        """Get error frequency per validator for a specific file."""
        pass

    def get_validator_trends(self, validator_name: str, days: int = 30) -> List[Dict]:
        """Get trend data for a validator over time (errors, warnings, duration)."""
        pass

    def get_problematic_files(self, threshold: float = 0.5, last_n_runs: int = 10) -> List[str]:
        """Find files that fail validation more than threshold percent of the time."""
        pass
```

### Configuration

```toml
[anvil.statistics]
enabled = true                # Enable statistics tracking
database_path = ".anvil/stats.db"  # SQLite database path
retention_days = 90           # Keep statistics for 90 days

# Smart filtering based on statistics
[anvil.statistics.smart_filter]
enabled = true                # Enable smart filtering
skip_tests_with_success_rate_above = 0.95  # Skip tests with >95% success rate
run_flaky_tests_first = true  # Prioritize flaky tests
focus_on_recent_failures = true  # Prioritize recently failing tests
```

### Example: Smart Test Filtering

When enabled, Anvil uses statistics to optimize test execution:

```bash
# With statistics:
[ANVIL] Smart filtering enabled
[ANVIL] Analyzed last 20 runs
[ANVIL] Skipping 450 tests with >95% success rate
[ANVIL] Prioritizing 15 flaky tests (success rate 50-90%)
[ANVIL] Running 85 tests (15 flaky + 70 recent failures/new)

  [✓] pytest (85 tests, 83 passed, 2 failed) - 3.2s
       Flaky tests detected:
         - test_connection_retry (6/10 passes)
         - test_concurrent_access (7/10 passes)
```

### Reports

Statistics can be exported and visualized:

```bash
# Generate statistics report
anvil stats report --days 30

# Export to JSON/CSV
anvil stats export --format json --output stats.json

# Show flaky tests
anvil stats flaky --threshold 0.7

# Show problem files
anvil stats problem-files --threshold 0.5
```

---

## Validator Parsers

### Overview

Each validator requires a parser to extract structured data from its output. Parsers are responsible for:
- Executing the validator with appropriate arguments
- Capturing and parsing output (stdout, stderr, exit codes)
- Extracting file paths, line numbers, error codes, messages
- Normalizing data into `ValidationResult` format

### Parser Interface

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ValidatorInput:
    """Configuration and input for validator execution."""
    files: List[str]                    # Files to validate
    config: Dict[str, Any]              # Validator-specific config
    project_root: str                   # Project root directory
    incremental: bool                   # Incremental mode flag

@dataclass
class Issue:
    """A single validation issue."""
    file: str                           # File path (relative to project root)
    line: Optional[int]                 # Line number (None if file-level)
    column: Optional[int]               # Column number (None if not available)
    severity: str                       # error, warning, info
    code: str                           # Error/warning code (e.g., 'E501', 'bugprone-*')
    message: str                        # Human-readable message
    suggestion: Optional[str]           # Suggested fix (if available)

@dataclass
class ValidationResult:
    """Result from validator execution."""
    validator_name: str
    language: str
    passed: bool                        # Overall pass/fail
    errors: List[Issue]                 # Error-level issues
    warnings: List[Issue]               # Warning-level issues
    infos: List[Issue]                  # Informational issues
    execution_time: float               # Execution duration in seconds
    files_checked: int                  # Number of files checked
    metadata: Dict[str, Any]            # Validator-specific metadata

class ValidatorParser(ABC):
    """Abstract base for validator parsers."""

    @abstractmethod
    def execute_and_parse(self, input: ValidatorInput) -> ValidationResult:
        """Execute validator and parse output."""
        pass

    @abstractmethod
    def build_command(self, input: ValidatorInput) -> List[str]:
        """Build command-line arguments for validator."""
        pass

    @abstractmethod
    def parse_output(self, stdout: str, stderr: str, exit_code: int) -> ValidationResult:
        """Parse validator output into structured result."""
        pass
```

### Python Validator Parsers

#### 1. flake8 Parser

**Input Configuration:**
```python
config = {
    "max_line_length": 100,
    "ignore": ["E203", "W503"],
    "extend_ignore": [],
    "max_complexity": 10,
    "exclude": [".git", "__pycache__", "build"],
}
```

**Command Template:**
```bash
flake8 --max-line-length=100 --ignore=E203,W503 --format=json file1.py file2.py
```

**Output Format (JSON):**
```json
{
  "src/parser.py": [
    {
      "line_number": 45,
      "column_number": 10,
      "code": "E501",
      "text": "line too long (105 > 100 characters)",
      "physical_line": "    def very_long_function_name_with_many_parameters(self, param1, param2, param3):"
    }
  ]
}
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="flake8",
    language="python",
    passed=False,
    errors=[Issue(file="src/parser.py", line=45, column=10, severity="error",
                  code="E501", message="line too long (105 > 100 characters)")],
    warnings=[],
    execution_time=0.5,
    files_checked=8,
    metadata={"total_violations": 1}
)
```

#### 2. black Parser

**Input Configuration:**
```python
config = {
    "line_length": 100,
    "target_version": ["py38", "py39", "py310"],
    "skip_string_normalization": False,
}
```

**Command Template:**
```bash
black --check --line-length=100 --diff file1.py file2.py
```

**Output Format (text):**
```
would reformat src/utils.py
would reformat src/parser.py
Oh no! 💥 💔 💥
2 files would be reformatted, 6 files would be left unchanged.
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="black",
    language="python",
    passed=False,
    errors=[Issue(file="src/utils.py", line=None, severity="error",
                  code="FORMAT", message="File needs formatting",
                  suggestion="black src/utils.py")],
    execution_time=0.3,
    files_checked=8,
    metadata={"files_need_formatting": 2, "files_formatted": 6}
)
```

#### 3. isort Parser

**Input Configuration:**
```python
config = {
    "profile": "black",
    "line_length": 100,
    "multi_line_output": 3,
}
```

**Command Template:**
```bash
isort --check-only --diff --profile=black file1.py file2.py
```

**Output Format (text):**
```
ERROR: src/parser.py Imports are incorrectly sorted and/or formatted.
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="isort",
    language="python",
    passed=False,
    errors=[Issue(file="src/parser.py", line=None, severity="error",
                  code="IMPORT_ORDER", message="Imports are incorrectly sorted",
                  suggestion="isort src/parser.py")],
    execution_time=0.2,
    files_checked=8,
    metadata={"files_need_sorting": 1}
)
```

#### 4. pylint Parser

**Input Configuration:**
```python
config = {
    "max_complexity": 10,
    "disable": ["C0111"],  # Missing docstring
    "enable": ["all"],
    "max_line_length": 100,
}
```

**Command Template:**
```bash
pylint --output-format=json --disable=C0111 src/
```

**Output Format (JSON):**
```json
[
  {
    "type": "warning",
    "module": "parser",
    "obj": "parse_args",
    "line": 45,
    "column": 4,
    "endLine": 45,
    "endColumn": 15,
    "path": "src/parser.py",
    "symbol": "unused-argument",
    "message": "Unused argument 'context'",
    "message-id": "W0613"
  }
]
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="pylint",
    language="python",
    passed=False,
    errors=[],
    warnings=[Issue(file="src/parser.py", line=45, column=4, severity="warning",
                    code="W0613", message="Unused argument 'context'")],
    execution_time=1.2,
    files_checked=8,
    metadata={"score": 8.5}
)
```

#### 5. radon Parser

**Input Configuration:**
```python
config = {
    "max_complexity": 10,  # Cyclomatic complexity threshold
    "show_complexity": True,
}
```

**Command Template:**
```bash
radon cc --json --min B src/
```

**Output Format (JSON):**
```json
{
  "src/parser.py": [
    {
      "type": "method",
      "name": "parse_arguments",
      "lineno": 45,
      "col_offset": 4,
      "endline": 78,
      "complexity": 12,
      "rank": "B"
    }
  ]
}
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="radon",
    language="python",
    passed=False,
    errors=[Issue(file="src/parser.py", line=45, severity="warning",
                  code="COMPLEXITY", message="Function 'parse_arguments' has complexity 12 (threshold: 10)")],
    execution_time=0.4,
    files_checked=8,
    metadata={"average_complexity": "B", "max_complexity": 12}
)
```

#### 6. vulture Parser

**Input Configuration:**
```python
config = {
    "min_confidence": 80,  # Minimum confidence for dead code detection
}
```

**Command Template:**
```bash
vulture --min-confidence=80 src/
```

**Output Format (text):**
```
src/utils.py:45: unused function 'old_helper' (90% confidence)
src/parser.py:123: unused variable 'temp' (95% confidence)
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="vulture",
    language="python",
    passed=False,
    warnings=[Issue(file="src/utils.py", line=45, severity="warning",
                    code="UNUSED", message="unused function 'old_helper' (90% confidence)")],
    execution_time=0.6,
    files_checked=8,
    metadata={"unused_items": 2}
)
```

#### 7. pytest Parser

**Input Configuration:**
```python
config = {
    "coverage_threshold": 90.0,
    "coverage_per_module": 85.0,
    "test_pattern": "test_*.py",
    "markers": [],  # pytest markers to run
}
```

**Command Template:**
```bash
pytest --json-report --json-report-file=report.json --cov=src --cov-report=json tests/
```

**Output Format (JSON):**
```json
{
  "tests": [
    {
      "nodeid": "tests/test_parser.py::TestParser::test_parse_args",
      "outcome": "passed",
      "duration": 0.012,
      "setup": {"duration": 0.001},
      "call": {"duration": 0.010},
      "teardown": {"duration": 0.001}
    },
    {
      "nodeid": "tests/test_validator.py::test_validate_file",
      "outcome": "failed",
      "duration": 0.045,
      "call": {
        "longrepr": "AssertionError: Expected True, got False"
      }
    }
  ],
  "summary": {
    "passed": 734,
    "failed": 1,
    "skipped": 4,
    "total": 739,
    "duration": 8.5
  },
  "coverage": {
    "totals": {
      "percent_covered": 96.14
    },
    "files": {
      "src/parser.py": {
        "summary": {"percent_covered": 98.5}
      }
    }
  }
}
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="pytest",
    language="python",
    passed=False,
    errors=[Issue(file="tests/test_validator.py", line=None, severity="error",
                  code="TEST_FAILURE", message="test_validate_file failed: AssertionError: Expected True, got False")],
    execution_time=8.5,
    files_checked=8,
    metadata={
        "tests_passed": 734,
        "tests_failed": 1,
        "tests_skipped": 4,
        "coverage_percent": 96.14,
        "test_cases": [
            {"name": "test_parse_args", "status": "passed", "duration": 0.012},
            {"name": "test_validate_file", "status": "failed", "duration": 0.045,
             "error": "AssertionError: Expected True, got False"}
        ]
    }
)
```

### C++ Validator Parsers

#### 8. clang-tidy Parser

**Input Configuration:**
```python
config = {
    "checks": ["bugprone-*", "cert-*", "cppcoreguidelines-*", "modernize-*"],
    "header_filter": ".*",
    "warnings_as_errors": False,
    "format_style": "google",
}
```

**Command Template:**
```bash
clang-tidy --checks='bugprone-*,cert-*' --header-filter='.*' --export-fixes=fixes.yaml src/engine.cpp -- -std=c++17
```

**Output Format (YAML):**
```yaml
---
MainSourceFile: src/engine.cpp
Diagnostics:
  - DiagnosticName: 'modernize-use-nullptr'
    Message: 'use nullptr'
    FileOffset: 1234
    FilePath: src/engine.cpp
    Replacements:
      - FilePath: src/engine.cpp
        Offset: 1234
        Length: 1
        ReplacementText: 'nullptr'
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="clang-tidy",
    language="cpp",
    passed=False,
    warnings=[Issue(file="src/engine.cpp", line=None, severity="warning",
                    code="modernize-use-nullptr", message="use nullptr",
                    suggestion="Replace with nullptr")],
    execution_time=3.2,
    files_checked=7,
    metadata={"fixes_available": 1}
)
```

#### 9. clang-format Parser

**Input Configuration:**
```python
config = {
    "style": "Google",  # Google, LLVM, Chromium, Mozilla, WebKit, or file
    "fallback_style": "LLVM",
}
```

**Command Template:**
```bash
clang-format --dry-run --Werror --style=Google src/engine.cpp
```

**Output Format (text/exit code):**
- Exit code 0: Properly formatted
- Exit code 1: Needs formatting

**Parsed Output:**
```python
ValidationResult(
    validator_name="clang-format",
    language="cpp",
    passed=True if exit_code == 0 else False,
    errors=[Issue(file="src/engine.cpp", severity="error",
                  code="FORMAT", message="File needs formatting",
                  suggestion="clang-format -i src/engine.cpp")],
    execution_time=0.8,
    files_checked=7,
    metadata={"files_need_formatting": 0 if passed else 1}
)
```

#### 10. cppcheck Parser

**Input Configuration:**
```python
config = {
    "enable": ["warning", "style", "performance", "portability"],
    "suppress": [],
    "inconclusive": False,
    "std": "c++17",
}
```

**Command Template:**
```bash
cppcheck --enable=warning,style,performance --xml --xml-version=2 src/
```

**Output Format (XML):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
  <errors>
    <error id="memleak" severity="error" msg="Memory leak: ptr" verbose="Memory leak: ptr">
      <location file="src/engine.cpp" line="234" column="10"/>
    </error>
    <error id="unusedVariable" severity="warning" msg="Unused variable: result">
      <location file="src/utils.cpp" line="56" column="8"/>
    </error>
  </errors>
</results>
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="cppcheck",
    language="cpp",
    passed=False,
    errors=[Issue(file="src/engine.cpp", line=234, column=10, severity="error",
                  code="memleak", message="Memory leak: ptr")],
    warnings=[Issue(file="src/utils.cpp", line=56, column=8, severity="warning",
                    code="unusedVariable", message="Unused variable: result")],
    execution_time=2.1,
    files_checked=7,
    metadata={"total_issues": 2}
)
```

#### 11. cpplint Parser

**Input Configuration:**
```python
config = {
    "filter": ["-whitespace/indent", "-legal/copyright"],
    "linelength": 100,
    "root": "src",
}
```

**Command Template:**
```bash
cpplint --filter=-whitespace/indent --linelength=100 src/engine.cpp
```

**Output Format (text):**
```
src/engine.cpp:45:  Missing space before {  [whitespace/braces] [5]
src/utils.cpp:78:  Line ends in whitespace  [whitespace/end_of_line] [4]
Total errors found: 2
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="cpplint",
    language="cpp",
    passed=False,
    errors=[Issue(file="src/engine.cpp", line=45, severity="error",
                  code="whitespace/braces", message="Missing space before {")],
    execution_time=1.5,
    files_checked=7,
    metadata={"total_errors": 2}
)
```

#### 12. Google Test (gtest) Parser

**Input Configuration:**
```python
config = {
    "test_filter": "*",  # Run all tests
    "timeout": 300,      # Timeout in seconds
    "repeat": 1,         # Number of times to repeat tests
}
```

**Command Template:**
```bash
./build/tests/all_tests --gtest_output=json:results.json --gtest_filter=*
```

**Output Format (JSON):**
```json
{
  "tests": 125,
  "failures": 2,
  "disabled": 0,
  "errors": 0,
  "timestamp": "2026-01-29T14:30:00Z",
  "time": "2.3s",
  "testsuites": [
    {
      "name": "EngineTest",
      "tests": 45,
      "failures": 1,
      "disabled": 0,
      "errors": 0,
      "time": "0.8s",
      "testsuite": [
        {
          "name": "ProcessInput",
          "status": "RUN",
          "result": "COMPLETED",
          "time": "0.012s",
          "classname": "EngineTest"
        },
        {
          "name": "ValidateOutput",
          "status": "RUN",
          "result": "FAILED",
          "time": "0.045s",
          "classname": "EngineTest",
          "failures": [
            {
              "failure": "Expected: (output) == (expected), actual: 42 vs 43\nsrc/engine_test.cpp:234",
              "type": ""
            }
          ]
        }
      ]
    }
  ]
}
```

**Parsed Output:**
```python
ValidationResult(
    validator_name="gtest",
    language="cpp",
    passed=False,
    errors=[Issue(file="src/engine_test.cpp", line=234, severity="error",
                  code="TEST_FAILURE",
                  message="EngineTest.ValidateOutput failed: Expected: (output) == (expected), actual: 42 vs 43")],
    execution_time=2.3,
    files_checked=1,  # Test binary
    metadata={
        "tests_total": 125,
        "tests_passed": 123,
        "tests_failed": 2,
        "test_cases": [
            {"name": "EngineTest.ProcessInput", "status": "passed", "duration": 0.012},
            {"name": "EngineTest.ValidateOutput", "status": "failed", "duration": 0.045,
             "error": "Expected: (output) == (expected), actual: 42 vs 43"}
        ]
    }
)
```

### Parser Implementation Strategy

#### Architecture Approach

Each validator parser is implemented as a self-contained module with three main responsibilities:

1. **Command Construction** - Build the command-line invocation with appropriate flags and arguments based on configuration
2. **Execution & Capture** - Run the validator tool and capture stdout, stderr, and exit codes
3. **Output Parsing** - Extract structured data from the tool's output format (JSON, XML, text, etc.)

The parsers are designed to be **stateless** and **deterministic** - given the same input files and configuration, they should always produce the same structured output. This makes testing straightforward and behavior predictable.

#### Testing Strategy

Testing parsers requires a multi-layered approach:

**Layer 1: Unit Tests with Fixtures**

The primary testing approach uses **fixture-based unit tests**. For each validator:

1. **Collect Real Output Samples** - Run the actual validator tool on sample code (both clean and problematic) and capture the raw output
2. **Store as Test Fixtures** - Save these outputs as fixture files (e.g., `fixtures/flake8/output_with_errors.txt`)
3. **Test Parser Logic** - Unit tests feed fixtures to the parser and verify the structured output is correct
4. **Version-Specific Fixtures** - Store fixtures for different tool versions (e.g., `fixtures/pylint/8.x/`, `fixtures/pylint/9.x/`)

This approach provides:
- **Fast tests** - No need to install actual tools in test environment
- **Deterministic** - Same fixtures always produce same results
- **Comprehensive coverage** - Can test edge cases that are hard to reproduce
- **Version testing** - Can verify compatibility with multiple tool versions simultaneously

**Layer 2: Integration Tests with Real Tools**

Integration tests run the actual validator tools (when available):

1. **Tool Availability Check** - Skip tests if tool not installed (using pytest markers)
2. **Known Good/Bad Code** - Test on sample projects with known issues
3. **End-to-End Validation** - Verify command construction → execution → parsing pipeline
4. **Cross-Platform Testing** - Run in CI on Linux, Windows, macOS

These tests validate that:
- Command-line arguments are correctly formatted for each platform
- Tools are invoked correctly
- Real tool output matches our fixture expectations
- Parser handles live tool variations

**Layer 3: Regression Tests**

Maintain a regression test suite:
- **Historical Outputs** - Archive outputs from production use
- **Known Variations** - Document tool version differences
- **Platform Differences** - Track platform-specific output formats

#### Fixture Organization

```
anvil/tests/fixtures/
├── python/
│   ├── flake8/
│   │   ├── v6.0/
│   │   │   ├── no_errors.txt
│   │   │   ├── syntax_errors.json
│   │   │   └── multiple_files.json
│   │   └── v7.0/
│   │       └── syntax_errors.json
│   ├── pylint/
│   │   ├── v2.x/
│   │   │   ├── clean_code.json
│   │   │   └── violations.json
│   │   └── v3.x/
│   │       └── violations.json
│   └── pytest/
│       ├── all_passed.json
│       ├── some_failures.json
│       └── with_coverage.json
├── cpp/
│   ├── clang-tidy/
│   │   ├── v14/
│   │   │   └── warnings.yaml
│   │   └── v15/
│   │       └── warnings.yaml
│   ├── cppcheck/
│   │   └── v2.x/
│   │       ├── no_issues.xml
│   │       └── memory_leak.xml
│   └── gtest/
│       ├── all_passed.json
│       └── test_failures.json
└── sample_code/
    ├── python/
    │   ├── clean.py
    │   ├── style_issues.py
    │   └── complexity_issues.py
    └── cpp/
        ├── clean.cpp
        ├── memory_leak.cpp
        └── style_issues.cpp
```

#### Test Implementation Example

For each validator, tests follow this pattern:

**Test 1: Parse Clean Output**
- Input: Fixture with no errors
- Expected: ValidationResult with passed=True, empty error lists

**Test 2: Parse Output with Errors**
- Input: Fixture with known errors
- Expected: ValidationResult with correct number of errors, proper Issue objects

**Test 3: Parse Output with Warnings**
- Input: Fixture with warnings
- Expected: ValidationResult with warnings properly categorized

**Test 4: Handle Malformed Output**
- Input: Corrupted/incomplete fixture
- Expected: Parser handles gracefully, returns partial results or error

**Test 5: Version Compatibility**
- Input: Fixtures from different tool versions
- Expected: Parser handles both old and new formats

**Test 6: Platform-Specific Output**
- Input: Fixtures from Windows/Linux/macOS
- Expected: Parser normalizes platform differences

#### Parser Robustness

Parsers implement defensive parsing with fallbacks:

1. **Primary Format** - Try to parse expected format (JSON, XML, etc.)
2. **Fallback to Text Parsing** - If structured format fails, parse as text using regex
3. **Graceful Degradation** - Return partial results if some data can't be parsed
4. **Error Context** - Log parsing failures with context for debugging

---

### Platform & Version Compatibility Strategy

#### Challenge Overview

Validator tools vary across:
- **Versions**: Output formats change between major/minor versions
- **Platforms**: Path separators, line endings, tool availability
- **Configurations**: Different default behaviors on different systems

#### Version Handling

**Approach 1: Detect Version**

Each parser detects the tool version before parsing:

1. Run tool with `--version` flag
2. Parse version string (e.g., "pylint 3.0.1")
3. Select appropriate parsing strategy based on version

**Approach 2: Format Auto-Detection**

Parsers detect output format dynamically:

1. Try parsing as JSON → if successful, use JSON parser
2. Try parsing as XML → if successful, use XML parser
3. Fall back to text parsing with regex

**Approach 3: Multiple Format Parsers**

For tools with breaking changes, maintain separate parsers:

- **flake8**: Supports both legacy text and modern JSON output
- **pylint**: Different parsers for v2.x vs v3.x
- **cppcheck**: Handles both XML version 1 and version 2

#### Version Detection Implementation

Parsers implement version detection:

1. **Cache Version** - Detect once per session, cache result
2. **Version Registry** - Map version ranges to parser implementations
3. **Minimum Version Check** - Warn if tool version too old
4. **Maximum Version Warning** - Warn if untested version (may still work)

Example version handling:
- **pylint 2.x**: Parse JSON output with older schema
- **pylint 3.x**: Parse JSON with new schema (additional fields)
- **Auto-detect**: Check if JSON contains new fields to determine version

#### Platform Differences

**Path Normalization**

Parsers normalize paths to be cross-platform:

1. **Convert Separators** - Replace `\` with `/` on Windows
2. **Relative Paths** - Always use project-relative paths, not absolute
3. **Case Sensitivity** - Handle case-insensitive filesystems (Windows/macOS)

**Line Ending Handling**

Output may contain different line endings:

1. **Normalize** - Convert all line endings to `\n` during parsing
2. **Preserve** - Keep original in structured data if needed for diffing

**Tool Location**

Tools may be in different locations:

1. **PATH Search** - Use `shutil.which()` to locate tools
2. **Common Locations** - Check platform-specific install locations
3. **Custom Paths** - Allow users to specify tool paths in configuration

**Platform-Specific Flags**

Some tools have platform-specific behavior:

1. **Conditional Arguments** - Add/remove flags based on platform
2. **Environment Variables** - Set platform-specific environment
3. **Path Handling** - Quote paths appropriately for shell

#### Configuration for Compatibility

Users can override version/platform detection:

```toml
[anvil.compatibility]
# Explicit version overrides (rarely needed)
pylint_version = "3.0"
clang_tidy_version = "15"

# Custom tool paths
[anvil.tools]
pylint = "/opt/homebrew/bin/pylint"
clang_tidy = "C:\\Program Files\\LLVM\\bin\\clang-tidy.exe"

# Force specific output formats
[anvil.output_format]
flake8 = "json"  # Force JSON instead of text
cppcheck = "xml2"  # Force XML version 2
```

#### Testing Across Versions/Platforms

**CI Matrix Testing**

Anvil's CI tests across:
- **Platforms**: Linux (Ubuntu), Windows, macOS
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Tool Versions**: Minimum supported, latest stable

**Version Compatibility Matrix**

Documentation maintains compatibility matrix:

| Tool | Min Version | Tested Versions | Known Issues |
|------|-------------|-----------------|--------------|
| flake8 | 4.0 | 4.0, 5.0, 6.0, 7.0 | None |
| pylint | 2.12 | 2.x, 3.x | v3.x has new JSON schema |
| pytest | 7.0 | 7.x, 8.x | Coverage plugin required |
| clang-tidy | 12 | 12, 13, 14, 15, 16 | Check names changed in v15 |
| cppcheck | 2.0 | 2.x | XML format preferred |

#### Handling Breaking Changes

When tool updates break compatibility:

1. **Detect** - CI tests with latest tool versions catch breakage
2. **Fix** - Add support for new format while maintaining old format support
3. **Deprecate** - Warn users of old tool versions to upgrade
4. **Document** - Update compatibility matrix and migration guide
5. **Test** - Add fixtures for new version to regression suite

#### Graceful Degradation

If parser can't handle a specific version:

1. **Warn User** - "Warning: untested tool version (pylint 4.0), may produce incorrect results"
2. **Attempt Parsing** - Try anyway, most formats are backward compatible
3. **Fallback Mode** - Use text parsing instead of structured parsing
4. **Report Issue** - Provide instructions to report compatibility issue

#### Version Migration Path

When tools release breaking changes:

**Phase 1: Detection**
- New version released
- CI detects parsing failures
- Create issue to track compatibility

**Phase 2: Support Both Versions**
- Collect fixtures from new version
- Implement new parser or extend existing
- Maintain backward compatibility
- Add tests for both versions

**Phase 3: Deprecation Warning**
- Warn users on old versions
- Document minimum supported version change
- Provide migration timeline

**Phase 4: Drop Old Version**
- Remove old parser code (if significantly different)
- Update minimum version requirement
- Clean up tests

---

## Output Format

### Console Output

```
╔══════════════════════════════════════════════════════════════╗
║                      ANVIL - Quality Gate                     ║
╚══════════════════════════════════════════════════════════════╝

[ANVIL] Running validators for: python, cpp
[ANVIL] Incremental mode: ON (checking 15 modified files)

┌──────────────────────────────────────────────────────────────┐
│ Python Validators                                             │
└──────────────────────────────────────────────────────────────┘

  [✓] flake8         (8 files, 0 errors, 0 warnings) - 0.5s
  [✓] black          (8 files, all formatted)        - 0.3s
  [✓] isort          (8 files, all sorted)           - 0.2s
  [✗] pylint         (8 files, 2 errors, 3 warnings) - 1.2s
  [✓] radon          (8 files, avg complexity: B)    - 0.4s
  [✓] vulture        (8 files, 0 unused items)       - 0.6s
  [✓] pytest         (735 tests, 96.14% coverage)    - 8.5s

┌──────────────────────────────────────────────────────────────┐
│ C++ Validators                                                │
└──────────────────────────────────────────────────────────────┘

  [✓] clang-tidy     (7 files, 0 errors, 0 warnings) - 3.2s
  [✓] clang-format   (7 files, all formatted)        - 0.8s
  [✗] cppcheck       (7 files, 1 error, 2 warnings)  - 2.1s
  [✓] cpplint        (7 files, 0 style violations)   - 1.5s
  [✓] gtest          (125 tests, all passed)         - 2.3s

┌──────────────────────────────────────────────────────────────┐
│ Errors & Warnings                                             │
└──────────────────────────────────────────────────────────────┘

[ERROR] pylint - src/parser.py:45
  Unused argument 'context' (W0613)

[ERROR] pylint - src/validator.py:128
  Too many local variables (8/7) (R0914)

[ERROR] cppcheck - src/engine.cpp:234
  Memory leak: ptr [memleak]

[WARNING] cppcheck - src/utils.cpp:56
  Variable 'result' is assigned a value that is never used.

╔══════════════════════════════════════════════════════════════╗
║                        RESULT: FAILED                         ║
║  Total: 12 validators | Passed: 9 | Failed: 3                ║
║  Errors: 3 | Warnings: 3 | Duration: 22.1s                   ║
╚══════════════════════════════════════════════════════════════╝

[ANVIL] Fix the errors above and run 'anvil check' again.
```

### JSON Output (for CI/CD)

```json
{
  "timestamp": "2026-01-29T14:30:00Z",
  "duration_seconds": 22.1,
  "overall_status": "failed",
  "languages": ["python", "cpp"],
  "validators": {
    "python": {
      "flake8": {"status": "passed", "errors": 0, "warnings": 0, "duration": 0.5},
      "pylint": {
        "status": "failed",
        "errors": 2,
        "warnings": 3,
        "duration": 1.2,
        "issues": [
          {
            "file": "src/parser.py",
            "line": 45,
            "severity": "error",
            "code": "W0613",
            "message": "Unused argument 'context'"
          }
        ]
      }
    },
    "cpp": {
      "cppcheck": {
        "status": "failed",
        "errors": 1,
        "warnings": 2,
        "duration": 2.1,
        "issues": [
          {
            "file": "src/engine.cpp",
            "line": 234,
            "severity": "error",
            "code": "memleak",
            "message": "Memory leak: ptr"
          }
        ]
      }
    }
  },
  "summary": {
    "total_validators": 12,
    "passed": 9,
    "failed": 3,
    "total_errors": 3,
    "total_warnings": 3
  }
}
```

---

## Integration Points

### 1. Git Hooks

Anvil can install itself as a git hook:

```bash
anvil install-hooks
```

This creates `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Anvil pre-commit hook

# Check for bypass keyword in commit message
if git log -1 --pretty=%B | grep -q "ANVIL_SKIP"; then
    echo "[ANVIL] Bypassing validation (ANVIL_SKIP found in commit message)"
    exit 0
fi

# Run incremental validation
anvil check --incremental

exit $?
```

### 2. CI/CD Integration

#### GitHub Actions Example

```yaml
- name: Run Anvil Quality Gates
  run: anvil check --json > anvil-report.json

- name: Upload Anvil Report
  uses: actions/upload-artifact@v3
  with:
    name: anvil-report
    path: anvil-report.json
```

#### Pre-commit Framework Integration

Anvil can also integrate with the `pre-commit` framework:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/lmvcruz/argos
    rev: v1.0.0
    hooks:
      - id: anvil
        name: Anvil Quality Gate
        entry: anvil check
        language: python
        always_run: true
```

### 3. IDE Integration (Future)

Extension points for IDE plugins (VS Code, PyCharm, etc.):
- Real-time validation API
- Problem marker integration
- Quick-fix suggestions

---

## Incremental Validation

Anvil supports fast incremental validation by only checking modified files.

### Git Integration

```python
class GitChangeDetector:
    """Detects changed files using git."""

    def get_modified_files(self, since: str = "HEAD") -> List[str]:
        """Get list of modified files since specified commit/branch."""
        pass

    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        pass
```

### Performance

- **Full validation**: All files in project
- **Incremental validation**: Only modified files
- **Typical speedup**: 10-50x faster for small changes

---

## Error Reporting

### Severity Levels

1. **ERROR**: Must be fixed (blocks commit/build)
2. **WARNING**: Should be fixed (doesn't block by default)
3. **INFO**: Informational only

### Suggested Fixes

Where possible, Anvil shows suggested fixes:

```
[ERROR] black - src/utils.py
  File needs formatting

  Suggested fix:
  $ black src/utils.py
```

---

## Extension Points

### Adding New Languages

To add a new language (e.g., JavaScript):

1. Create `JavaScriptValidator` subclass
2. Implement required methods (name, language, validate, is_available)
3. Register in validator registry
4. Add configuration section to anvil.toml

### Adding New Validators

To add a new Python validator (e.g., mypy):

1. Create `MypyValidator(Validator)` class
2. Implement validation logic
3. Add configuration options
4. Register in Python validator set

---

## Dependencies

### Core Dependencies

- Python ≥3.8
- TOML parser (tomli/tomllib)
- Subprocess management (built-in)
- Git (for incremental checking)

### Python Validator Tools (Optional)

Install with: `pip install anvil[python]`

- flake8
- black
- isort
- pylint
- radon
- vulture
- autoflake
- pytest
- pytest-cov

### C++ Validator Tools (Optional)

Must be installed separately:

- clang-tidy (usually part of LLVM)
- clang-format (usually part of LLVM)
- cppcheck
- cpplint
- include-what-you-use (optional)
- Google Test (for running tests)

---

## Success Criteria

### Functional Requirements

- ✅ Support Python and C++ validation
- ✅ Plugin architecture for extensibility
- ✅ Incremental validation (git-aware)
- ✅ Git hook integration
- ✅ CI/CD integration
- ✅ Configurable quality gates
- ✅ Clear error reporting with suggestions
- ✅ Parallel validator execution
- ✅ JSON output for automation

### Non-Functional Requirements

- **Performance**: Incremental validation completes in <5 seconds for typical changes
- **Reliability**: ≥95% test coverage
- **Usability**: Works with zero configuration for standard projects
- **Maintainability**: Plugin architecture allows easy addition of validators
- **Documentation**: Comprehensive user guide with examples

---

## Future Enhancements (Post Iteration 2)

1. **More Languages**: JavaScript, TypeScript, Java, Rust, Go
2. **IDE Integration**: VS Code extension, LSP server
3. **Auto-fixing**: Automatic code fixes for certain violations
4. **Custom Validators**: User-defined validators via plugins
5. **Dashboard**: Web-based quality metrics dashboard
6. **Historical Tracking**: Track quality metrics over time
7. **Team Policies**: Shared team configuration presets

---

**Next Step**: Create detailed implementation plan (forge-implementation-plan-iter2.md update)
