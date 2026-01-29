# Iterative Planning: Anvil - Code Quality Gate Tool

**Goal:** Implement Anvil, a flexible code quality validation tool that enforces configurable quality standards across Python and C++ projects.

**Prerequisites:**
- Python ≥3.8
- Forge Iteration 1 complete (for shared utilities and patterns)
- Access to validator tools (flake8, black, pylint, clang-tidy, etc.) for integration testing

---

## Iteration 1: Core Framework & Infrastructure

### Overview

Build the foundational architecture that all validators will use: plugin system, configuration management, orchestration, and result aggregation.

---

### Step 1.1: Validator Interface & Base Classes

**Description:** Implement the abstract Validator interface and base classes that all validators must implement. This defines the contract for all validators.

**Testing Approach:**
- **Test Type:** Unit tests
- **Test Description:** Test validator interface and abstract base functionality
- **Test File:** `anvil/tests/test_validator_interface.py`
- **Test Cases:**
  - Test ValidationResult dataclass creation and attributes
  - Test Issue dataclass creation with all fields
  - Test Validator abstract methods raise NotImplementedError
  - Test ValidationResult serialization to dict
  - Test ValidationResult deserialization from dict
  - Test Issue severity validation (must be error/warning/info)
  - Test ValidationResult equality comparison
  - Test ValidationResult with empty error/warning lists
- **Success Criteria:** All abstract classes defined, dataclasses work correctly, 100% coverage

---

### Step 1.2: Configuration Manager

**Description:** Implement TOML configuration file loading, validation, and access. Support both full configuration and minimal zero-config mode with sensible defaults.

**Testing Approach:**
- **Test Type:** Unit tests with fixture TOML files
- **Test Description:** Test configuration loading and validation
- **Test File:** `anvil/tests/test_configuration.py`
- **Test Cases:**
  - Test load valid anvil.toml with all options
  - Test load minimal anvil.toml (empty file)
  - Test load with invalid TOML syntax (should raise error)
  - Test get_validator_config for specific validator
  - Test get_language_config for Python and C++
  - Test default values applied when not specified
  - Test configuration validation (e.g., max_complexity must be positive)
  - Test invalid validator names raise error
  - Test configuration inheritance (language defaults + validator overrides)
  - Test environment variable expansion in config
  - Test loading from custom config path
  - Test configuration merging (defaults + user config)
- **Success Criteria:** Configuration loads correctly, defaults applied, validation works, 100% coverage

---

### Step 1.3: Language Detector

**Description:** Implement automatic language detection based on file extensions. Scan project directory and identify Python and C++ files.

**Testing Approach:**
- **Test Type:** Unit tests with temporary directory structure
- **Test Description:** Test language detection from file extensions
- **Test File:** `anvil/tests/test_language_detector.py`
- **Test Cases:**
  - Test detect_languages finds Python files (*.py)
  - Test detect_languages finds C++ files (*.cpp, *.hpp, *.h, *.cc, *.cxx)
  - Test get_files_for_language returns only Python files
  - Test get_files_for_language returns only C++ files
  - Test detection ignores excluded patterns (.git, __pycache__, build)
  - Test detection follows gitignore rules (if configured)
  - Test detection with mixed language project
  - Test detection with no matching files
  - Test detection respects file_patterns from config
  - Test detection with symbolic links
  - Test detection performance with large directory trees
- **Success Criteria:** Language detection accurate, configurable exclusions work, 95% coverage

---

### Step 1.4: File Collector & Git Integration

**Description:** Implement file collection with support for full and incremental modes. Integrate with git to detect modified/staged files for incremental validation.

**Testing Approach:**
- **Test Type:** Integration tests with git repository
- **Test Description:** Test file collection in full and incremental modes
- **Test File:** `anvil/tests/test_file_collector.py`
- **Test Cases:**
  - Test collect all Python files in full mode
  - Test collect only modified Python files in incremental mode
  - Test collect staged files for pre-commit hook
  - Test git integration detects uncommitted changes
  - Test git integration handles new untracked files
  - Test git integration handles deleted files
  - Test file collection with no git repository (falls back to full)
  - Test file collection respects exclude patterns
  - Test file collection with empty repository
  - Test file collection across multiple commits
  - Test file collection with merge conflicts
- **Success Criteria:** File collection works in both modes, git integration robust, 95% coverage

---

### Step 1.5: Validator Registry & Plugin System

**Description:** Implement validator registry that discovers and registers available validators. Support dynamic loading of validator plugins.

**Testing Approach:**
- **Test Type:** Unit tests
- **Test Description:** Test validator registration and discovery
- **Test File:** `anvil/tests/test_validator_registry.py`
- **Test Cases:**
  - Test register validator by language
  - Test get validators by language
  - Test get specific validator by name
  - Test validator availability check
  - Test list all registered validators
  - Test list validators for specific language
  - Test register duplicate validator (should raise error)
  - Test get nonexistent validator (should raise error)
  - Test filter validators by enabled status from config
  - Test validator ordering (deterministic)
  - Test validator metadata (name, language, description)
- **Success Criteria:** Registry manages validators correctly, discovery works, 100% coverage

---

### Step 1.6: Validation Orchestrator

**Description:** Implement orchestrator that coordinates multiple validators, handles parallel execution, aggregates results, and determines overall pass/fail.

**Testing Approach:**
- **Test Type:** Unit tests with mock validators
- **Test Description:** Test validation orchestration and result aggregation
- **Test File:** `anvil/tests/test_orchestrator.py`
- **Test Cases:**
  - Test run all validators sequentially
  - Test run all validators in parallel (if configured)
  - Test run validators for specific language only
  - Test run specific validator by name
  - Test aggregate results from multiple validators
  - Test overall pass/fail determination
  - Test fail_fast mode (stop on first failure)
  - Test continue on failure mode (run all validators)
  - Test timeout handling for slow validators
  - Test error handling when validator crashes
  - Test error handling when validator tool not found
  - Test result collection with mixed pass/fail results
  - Test execution time tracking
  - Test file count aggregation
- **Success Criteria:** Orchestration works correctly, parallel execution functional, error handling robust, 95% coverage

---

### Step 1.7: Result Aggregation & Reporting

**Description:** Implement result aggregation from multiple validators and generate structured reports (console and JSON).

**Testing Approach:**
- **Test Type:** Unit tests
- **Test Description:** Test result aggregation and report generation
- **Test File:** `anvil/tests/test_reporting.py`
- **Test Cases:**
  - Test aggregate results from multiple validators
  - Test console report generation with box-drawing characters
  - Test JSON report generation
  - Test report includes all errors and warnings
  - Test report shows validator execution times
  - Test report shows overall pass/fail status
  - Test report groups issues by file
  - Test report groups issues by validator
  - Test report shows summary statistics
  - Test colored output (when terminal supports it)
  - Test plain text output (no colors)
  - Test verbose mode includes all details
  - Test quiet mode shows only errors
  - Test report file export
- **Success Criteria:** Reports are clear and informative, multiple formats supported, 95% coverage

---

## Iteration 2: Python Validators (Part 1 - Linting & Formatting)

### Overview

Implement Python validators for linting and code formatting: flake8, black, isort, and autoflake.

---

### Step 2.1: Parser Test Framework

**Description:** Set up fixture-based testing framework for parsers. Create fixtures directory structure and helper functions for parser testing.

**Testing Approach:**
- **Test Type:** Infrastructure setup
- **Test Description:** Create reusable test fixtures and helpers
- **Test File:** `anvil/tests/fixtures/` and `anvil/tests/helpers/parser_test_helpers.py`
- **Test Cases:**
  - Create fixture directory structure (python/, cpp/, sample_code/)
  - Create helper function for loading fixture files
  - Create helper function for running parsers with fixtures
  - Create helper function for asserting ValidationResult structure
  - Create sample good/bad Python code fixtures
  - Create sample good/bad C++ code fixtures
  - Document fixture naming conventions
- **Success Criteria:** Infrastructure ready for parser testing, helper functions tested, 100% coverage

---

### Step 2.2: flake8 Parser

**Description:** Implement parser for flake8 output (JSON format). Execute flake8 with appropriate flags and parse results into ValidationResult.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests with real flake8
- **Test Description:** Test flake8 parser with various output formats
- **Test File:** `anvil/tests/test_flake8_parser.py`
- **Test Cases:**
  - Test parse JSON output with no errors
  - Test parse JSON output with E-series errors (PEP 8 errors)
  - Test parse JSON output with W-series warnings
  - Test parse JSON output with F-series errors (PyFlakes)
  - Test parse JSON output with C-series complexity warnings
  - Test parse multiple files with mixed results
  - Test parse output with excluded files
  - Test build command with various config options
  - Test build command with ignore list
  - Test build command with max-line-length
  - Test parse legacy text format (fallback)
  - Test error when flake8 not installed
  - Test timeout handling
  - Test version detection (flake8 --version)
  - **Integration:** Test with real flake8 on sample code with errors
  - **Integration:** Test with real flake8 on clean code
- **Success Criteria:** Parser handles all flake8 output formats, builds correct commands, 95% coverage

---

### Step 2.3: black Parser

**Description:** Implement parser for black output. Execute black in check mode and parse which files need formatting.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test black parser with formatted and unformatted code
- **Test File:** `anvil/tests/test_black_parser.py`
- **Test Cases:**
  - Test parse output when all files formatted correctly
  - Test parse output when files need formatting
  - Test parse "would reformat" messages
  - Test parse "left unchanged" messages
  - Test parse diff output (when diff enabled)
  - Test build command with line-length option
  - Test build command with target-version
  - Test build command with skip-string-normalization
  - Test parse output with syntax errors
  - Test error when black not installed
  - Test version detection
  - **Integration:** Test with real black on unformatted code
  - **Integration:** Test with real black on formatted code
  - Test suggested fix command generation
- **Success Criteria:** Parser detects formatting issues correctly, 95% coverage

---

### Step 2.4: isort Parser

**Description:** Implement parser for isort output. Execute isort in check mode and parse which files have incorrect import order.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test isort parser with correct and incorrect imports
- **Test File:** `anvil/tests/test_isort_parser.py`
- **Test Cases:**
  - Test parse output with correctly sorted imports
  - Test parse output with incorrectly sorted imports
  - Test parse ERROR messages for incorrect sorting
  - Test parse diff output showing changes needed
  - Test build command with profile option (black, google, etc.)
  - Test build command with line-length
  - Test build command with multi-line-output style
  - Test build command with skip patterns
  - Test parse output with syntax errors
  - Test error when isort not installed
  - Test version detection
  - **Integration:** Test with real isort on unsorted imports
  - **Integration:** Test with real isort on sorted imports
  - Test suggested fix command generation
- **Success Criteria:** Parser detects import ordering issues, 95% coverage

---

### Step 2.5: autoflake Parser

**Description:** Implement parser for autoflake output. Execute autoflake in check mode and parse unused imports/variables.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test autoflake parser for unused code detection
- **Test File:** `anvil/tests/test_autoflake_parser.py`
- **Test Cases:**
  - Test parse output with no unused code
  - Test parse output with unused imports
  - Test parse output with unused variables
  - Test parse output with duplicate keys
  - Test build command with remove-unused-variables
  - Test build command with remove-all-unused-imports
  - Test build command with ignore-init-module-imports
  - Test build command with check-only mode
  - Test parse output grouping by file
  - Test error when autoflake not installed
  - **Integration:** Test with real autoflake on code with unused imports
  - **Integration:** Test with real autoflake on clean code
- **Success Criteria:** Parser detects unused code correctly, 95% coverage

---

## Iteration 3: Python Validators (Part 2 - Static Analysis)

### Overview

Implement Python validators for static analysis: pylint, radon, vulture.

---

### Step 3.1: pylint Parser

**Description:** Implement parser for pylint JSON output. Execute pylint and parse comprehensive static analysis results including scores.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test pylint parser with various issue types
- **Test File:** `anvil/tests/test_pylint_parser.py`
- **Test Cases:**
  - Test parse JSON output with no issues
  - Test parse convention messages (C-series)
  - Test parse refactor suggestions (R-series)
  - Test parse warnings (W-series)
  - Test parse errors (E-series)
  - Test parse fatal errors (F-series)
  - Test extract overall score
  - Test extract score change from previous run
  - Test build command with disable options
  - Test build command with enable options
  - Test build command with max-complexity
  - Test build command with rcfile path
  - Test parse confidence levels
  - Test parse multi-line issues with end line/column
  - Test version detection (pylint 2.x vs 3.x)
  - Test parse output format differences between versions
  - Test error when pylint not installed
  - **Integration:** Test with real pylint on code with violations
  - **Integration:** Test with real pylint on clean code
- **Success Criteria:** Parser handles all pylint issue types, score extraction works, 95% coverage

---

### Step 3.2: radon Parser

**Description:** Implement parser for radon JSON output. Execute radon and parse complexity metrics, maintainability index, and raw metrics.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test radon parser for complexity analysis
- **Test File:** `anvil/tests/test_radon_parser.py`
- **Test Cases:**
  - Test parse cyclomatic complexity (CC) output
  - Test parse maintainability index (MI) output
  - Test parse raw metrics (LOC, LLOC, comments)
  - Test complexity rank calculation (A-F)
  - Test parse function-level complexity
  - Test parse method-level complexity
  - Test parse closure complexity (if enabled)
  - Test aggregate average complexity
  - Test identify high-complexity functions above threshold
  - Test build command for CC mode
  - Test build command for MI mode
  - Test build command for raw metrics mode
  - Test build command with show-closures
  - Test build command with min grade threshold
  - Test error when radon not installed
  - **Integration:** Test with real radon on complex code
  - **Integration:** Test with real radon on simple code
- **Success Criteria:** Parser extracts all complexity metrics, thresholds enforced, 95% coverage

---

### Step 3.3: vulture Parser

**Description:** Implement parser for vulture text output. Execute vulture and parse unused code detection with confidence scores.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test vulture parser for dead code detection
- **Test File:** `anvil/tests/test_vulture_parser.py`
- **Test Cases:**
  - Test parse output with no unused code
  - Test parse unused function detection
  - Test parse unused method detection
  - Test parse unused class detection
  - Test parse unused variable detection
  - Test parse unused import detection
  - Test parse unused property detection
  - Test extract confidence percentages
  - Test filter by minimum confidence threshold
  - Test build command with min-confidence
  - Test build command with exclude patterns
  - Test build command with ignore-decorators
  - Test group unused items by type
  - Test calculate total unused lines
  - Test error when vulture not installed
  - **Integration:** Test with real vulture on code with unused items
  - **Integration:** Test with real vulture on clean code
- **Success Criteria:** Parser identifies unused code by type, confidence filtering works, 95% coverage

---

## Iteration 4: Python Validators (Part 3 - Testing & Coverage)

### Overview

Implement pytest validator with coverage measurement and test case tracking.

---

### Step 4.1: pytest Parser

**Description:** Implement parser for pytest JSON output with coverage data. Execute pytest with coverage plugin and parse detailed test results.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test pytest parser for test execution and coverage
- **Test File:** `anvil/tests/test_pytest_parser.py`
- **Test Cases:**
  - Test parse test results (passed, failed, skipped)
  - Test parse test duration per test
  - Test parse test failure messages
  - Test parse test tracebacks
  - Test parse test parameters (parametrized tests)
  - Test parse coverage percentage (overall)
  - Test parse coverage per module
  - Test parse missing line numbers
  - Test parse branch coverage (if enabled)
  - Test identify tests below coverage threshold
  - Test extract test summary statistics
  - Test extract slowest tests
  - Test build command with coverage options
  - Test build command with markers
  - Test build command with keywords (-k)
  - Test build command with parallel workers
  - Test build command with reruns on failure
  - Test detect flaky tests (pass after retry)
  - Test error when pytest not installed
  - Test error when coverage plugin not installed
  - **Integration:** Test with real pytest on test suite with failures
  - **Integration:** Test with real pytest on passing test suite
  - **Integration:** Test coverage measurement on sample code
- **Success Criteria:** Parser extracts all test data, coverage tracking works, individual test results captured, 95% coverage

---

## Iteration 5: C++ Validators (Part 1 - Static Analysis)

### Overview

Implement C++ validators for static analysis: clang-tidy, cppcheck, cpplint.

---

### Step 5.1: clang-tidy Parser

**Description:** Implement parser for clang-tidy YAML output. Execute clang-tidy and parse comprehensive C++ static analysis results with fix suggestions.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test clang-tidy parser for C++ analysis
- **Test File:** `anvil/tests/test_clang_tidy_parser.py`
- **Test Cases:**
  - Test parse YAML export-fixes format
  - Test parse diagnostic messages by check name
  - Test parse file, line, column information
  - Test parse replacement suggestions
  - Test parse note-level diagnostics
  - Test parse warning-level diagnostics
  - Test parse error-level diagnostics
  - Test build command with checks list
  - Test build command with header-filter
  - Test build command with extra compiler args (std, includes)
  - Test build command with compile_commands.json
  - Test group diagnostics by file
  - Test group diagnostics by check name
  - Test filter by severity
  - Test count fixable diagnostics
  - Test parse output from different clang-tidy versions (12-16)
  - Test error when clang-tidy not installed
  - **Integration:** Test with real clang-tidy on C++ code with issues
  - **Integration:** Test with real clang-tidy on clean C++ code
- **Success Criteria:** Parser handles all clang-tidy diagnostics, fix suggestions extracted, 95% coverage

---

### Step 5.2: cppcheck Parser

**Description:** Implement parser for cppcheck XML output. Execute cppcheck and parse bug detection, undefined behavior, and performance issues.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test cppcheck parser for C++ bug detection
- **Test File:** `anvil/tests/test_cppcheck_parser.py`
- **Test Cases:**
  - Test parse XML version 2 format
  - Test parse error severity issues
  - Test parse warning severity issues
  - Test parse style issues
  - Test parse performance issues
  - Test parse portability issues
  - Test parse information messages
  - Test extract error ID (nullPointer, memleak, etc.)
  - Test extract CWE IDs when available
  - Test parse inconclusive results
  - Test build command with enable categories
  - Test build command with suppressions
  - Test build command with std option (c++11, c++17, etc.)
  - Test build command with platform (unix64, win64, etc.)
  - Test build command with include paths
  - Test build command with defines
  - Test group issues by error ID
  - Test group issues by file
  - Test error when cppcheck not installed
  - **Integration:** Test with real cppcheck on C++ code with bugs
  - **Integration:** Test with real cppcheck on clean C++ code
- **Success Criteria:** Parser handles all cppcheck issue types, XML parsing robust, 95% coverage

---

### Step 5.3: cpplint Parser

**Description:** Implement parser for cpplint text output. Execute cpplint and parse Google C++ Style Guide violations.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test cpplint parser for style checking
- **Test File:** `anvil/tests/test_cpplint_parser.py`
- **Test Cases:**
  - Test parse style violation messages
  - Test parse file, line number from output
  - Test parse category (whitespace, readability, build, etc.)
  - Test parse confidence level (1-5)
  - Test map confidence to severity
  - Test build command with filter options
  - Test build command with linelength
  - Test build command with root directory
  - Test build command with extensions
  - Test group violations by category
  - Test group violations by confidence
  - Test count total violations
  - Test identify most common violations
  - Test error when cpplint not installed
  - **Integration:** Test with real cpplint on code with style issues
  - **Integration:** Test with real cpplint on style-compliant code
- **Success Criteria:** Parser handles all cpplint categories, confidence mapping correct, 95% coverage

---

## Iteration 6: C++ Validators (Part 2 - Formatting & Testing)

### Overview

Implement remaining C++ validators: clang-format, include-what-you-use, Google Test.

---

### Step 6.1: clang-format Parser

**Description:** Implement parser for clang-format output. Execute clang-format in dry-run mode and detect formatting issues.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test clang-format parser for formatting check
- **Test File:** `anvil/tests/test_clang_format_parser.py`
- **Test Cases:**
  - Test parse when all files properly formatted (exit code 0)
  - Test parse when files need formatting (exit code 1)
  - Test parse XML replacements output (if enabled)
  - Test build command with style option (Google, LLVM, etc.)
  - Test build command with .clang-format file
  - Test build command with fallback style
  - Test build command with dry-run and Werror flags
  - Test generate suggested fix command
  - Test count files needing formatting
  - Test error when clang-format not installed
  - Test version detection
  - **Integration:** Test with real clang-format on unformatted C++ code
  - **Integration:** Test with real clang-format on formatted C++ code
- **Success Criteria:** Parser detects formatting issues via exit code, 95% coverage

---

### Step 6.2: include-what-you-use (IWYU) Parser

**Description:** Implement parser for IWYU output. Execute IWYU and parse include optimization suggestions.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test IWYU parser for include analysis
- **Test File:** `anvil/tests/test_iwyu_parser.py`
- **Test Cases:**
  - Test parse suggestions to add includes
  - Test parse suggestions to remove includes
  - Test parse forward declaration suggestions
  - Test parse transitive include information
  - Test build command with mapping file
  - Test build command with compiler flags
  - Test build command with -Xiwyu options
  - Test parse "full include-list" section
  - Test parse "why" explanations
  - Test group suggestions by file
  - Test count unnecessary includes
  - Test count missing includes
  - Test error when IWYU not installed
  - **Integration:** Test with real IWYU on C++ code with include issues
  - **Integration:** Test with real IWYU on clean includes
- **Success Criteria:** Parser extracts all include suggestions, 90% coverage (IWYU optional)

---

### Step 6.3: Google Test (gtest) Parser

**Description:** Implement parser for Google Test JSON output. Execute test binary and parse detailed test results.

**Testing Approach:**
- **Test Type:** Unit tests with fixtures + Integration tests
- **Test Description:** Test gtest parser for C++ test execution
- **Test File:** `anvil/tests/test_gtest_parser.py`
- **Test Cases:**
  - Test parse test suite results
  - Test parse individual test results (PASS, FAIL)
  - Test parse test failure messages
  - Test parse test durations
  - Test parse assertion failures with expected/actual values
  - Test parse file and line number of failures
  - Test extract total test count
  - Test extract passed/failed/skipped counts
  - Test build command with test filter
  - Test build command with repeat option
  - Test build command with shuffle
  - Test build command with output format (json, xml)
  - Test parse disabled tests
  - Test identify slowest tests
  - Test detect flaky tests (if repeat enabled)
  - Test error when test binary not found
  - Test timeout handling
  - **Integration:** Test with real gtest binary with passing tests
  - **Integration:** Test with real gtest binary with failing tests
- **Success Criteria:** Parser extracts all test data, individual test tracking works, 95% coverage

---

## Iteration 7: Statistics & Historical Tracking

### Overview

Implement statistics database for tracking validation history, detecting flaky tests, and enabling smart filtering.

---

### Step 7.1: Statistics Database Schema

**Description:** Implement SQLite database schema for storing validation history. Create tables for runs, validator results, test cases, and file validations.

**Testing Approach:**
- **Test Type:** Unit tests with in-memory database
- **Test Description:** Test database schema and CRUD operations
- **Test File:** `anvil/tests/test_statistics_database.py`
- **Test Cases:**
  - Test create database schema
  - Test insert ValidationRun record
  - Test insert ValidatorRunRecord
  - Test insert TestCaseRecord
  - Test insert FileValidationRecord
  - Test query runs by date range
  - Test query runs by git commit
  - Test query validator results for specific run
  - Test query test cases for specific run
  - Test foreign key constraints enforced
  - Test database migration from v1 to v2 schema
  - Test database with retention policy (delete old records)
  - Test concurrent access (multiple processes)
  - Test database corruption recovery
- **Success Criteria:** Database schema created, CRUD operations work, 100% coverage

---

### Step 7.2: Statistics Persistence

**Description:** Implement statistics persistence layer that saves validation results to database after each run.

**Testing Approach:**
- **Test Type:** Integration tests
- **Test Description:** Test saving validation results to database
- **Test File:** `anvil/tests/test_statistics_persistence.py`
- **Test Cases:**
  - Test save validation run with no issues
  - Test save validation run with errors
  - Test save validation run with warnings
  - Test save validator execution metadata
  - Test save test case results (pytest, gtest)
  - Test save file validation results
  - Test save with git commit information
  - Test save with incremental mode flag
  - Test save with partial results (some validators failed)
  - Test transaction rollback on error
  - Test database path from configuration
  - Test statistics disabled (no-op mode)
- **Success Criteria:** All validation data persisted correctly, 95% coverage

---

### Step 7.3: Statistics Query Engine

**Description:** Implement query engine for analyzing historical data: success rates, flaky tests, problematic files, trends.

**Testing Approach:**
- **Test Type:** Unit tests with populated database
- **Test Description:** Test statistical queries and analysis
- **Test File:** `anvil/tests/test_statistics_queries.py`
- **Test Cases:**
  - Test get_test_success_rate for specific test
  - Test get_flaky_tests with threshold
  - Test get_file_error_frequency for specific file
  - Test get_validator_trends over time
  - Test get_problematic_files with threshold
  - Test query last N runs
  - Test query runs between dates
  - Test query runs for specific git branch
  - Test aggregate success rate across all tests
  - Test identify newly failing tests
  - Test identify newly passing tests
  - Test trend analysis (improving vs degrading)
  - Test performance of queries on large dataset
- **Success Criteria:** All queries return correct results, performance acceptable, 95% coverage

---

### Step 7.4: Smart Filtering

**Description:** Implement smart filtering that uses statistics to optimize test execution: skip high-success tests, prioritize flaky tests.

**Testing Approach:**
- **Test Type:** Integration tests
- **Test Description:** Test smart filtering based on historical data
- **Test File:** `anvil/tests/test_smart_filtering.py`
- **Test Cases:**
  - Test skip tests with success rate > threshold
  - Test prioritize flaky tests (run first)
  - Test prioritize recently failing tests
  - Test include new tests (never seen before)
  - Test include modified test files
  - Test filtering with insufficient history (< N runs)
  - Test filtering disabled mode (run all tests)
  - Test filtering configuration from anvil.toml
  - Test filtering produces correct test list
  - Test filtering reports what was skipped
  - Test filtering respects explicit test selection (--validator)
- **Success Criteria:** Smart filtering optimizes test execution, configurable, 95% coverage

---

## Iteration 8: Git Hooks & CLI

### Overview

Implement git hook integration and command-line interface for all Anvil functionality.

---

### Step 8.1: Git Hook Installation

**Description:** Implement git hook installation and management. Support pre-commit and pre-push hooks with bypass mechanism.

**Testing Approach:**
- **Test Type:** Integration tests with git repository
- **Test Description:** Test git hook installation and execution
- **Test File:** `anvil/tests/test_git_hooks.py`
- **Test Cases:**
  - Test install pre-commit hook
  - Test install pre-push hook
  - Test hook script is executable
  - Test hook script calls anvil check --incremental
  - Test hook respects bypass keyword in commit message
  - Test hook returns correct exit code (0 = pass, 1 = fail)
  - Test uninstall hooks
  - Test update hooks (replace existing)
  - Test hook installation outside git repository (error)
  - Test multi-repository support (different directories)
  - Test hook with Anvil in different location (PATH)
  - Test hook preservation during git operations
  - Test hook execution with environment variables
- **Success Criteria:** Hooks install and execute correctly, bypass mechanism works, 100% coverage

---

### Step 8.2: CLI - Main Commands

**Description:** Implement main CLI commands: check, install-hooks, config, list.

**Testing Approach:**
- **Test Type:** Integration tests via CLI
- **Test Description:** Test CLI command execution
- **Test File:** `anvil/tests/test_cli_commands.py`
- **Test Cases:**
  - Test `anvil check` runs all validators
  - Test `anvil check --incremental` runs on changed files only
  - Test `anvil check --language python` runs Python validators only
  - Test `anvil check --validator flake8` runs specific validator
  - Test `anvil check --verbose` shows detailed output
  - Test `anvil check --quiet` shows only errors
  - Test `anvil install-hooks` installs pre-commit hook
  - Test `anvil install-hooks --uninstall` removes hooks
  - Test `anvil config show` displays configuration
  - Test `anvil config validate` validates anvil.toml
  - Test `anvil config init` generates default config
  - Test `anvil config check-tools` shows available validators
  - Test `anvil list` shows all validators
  - Test `anvil list --language cpp` shows C++ validators
  - Test `anvil list --detailed` shows validator info
  - Test `anvil --help` shows help message
  - Test `anvil --version` shows version
  - Test CLI with missing anvil.toml (uses defaults)
  - Test CLI with invalid anvil.toml (shows error)
  - Test CLI exit codes (0 = pass, 1 = fail, 2 = config error, 3 = missing tools)
- **Success Criteria:** All CLI commands work correctly, help text clear, 100% coverage

---

### Step 8.3: CLI - Statistics Commands

**Description:** Implement CLI commands for statistics: stats report, stats export, stats flaky.

**Testing Approach:**
- **Test Type:** Integration tests
- **Test Description:** Test statistics CLI commands
- **Test File:** `anvil/tests/test_cli_statistics.py`
- **Test Cases:**
  - Test `anvil stats report` shows statistics summary
  - Test `anvil stats report --days 30` filters by date range
  - Test `anvil stats export --format json` exports to JSON
  - Test `anvil stats export --format csv` exports to CSV
  - Test `anvil stats flaky` lists flaky tests
  - Test `anvil stats flaky --threshold 0.7` filters by threshold
  - Test `anvil stats problem-files` lists problematic files
  - Test `anvil stats trends --validator pylint` shows trends
  - Test statistics commands with empty database
  - Test statistics commands with insufficient data
  - Test export to file (--output option)
- **Success Criteria:** Statistics commands provide useful insights, export works, 95% coverage

---

### Step 8.4: CLI - Output Formatting

**Description:** Implement rich console output with box-drawing characters, colors, and progress indicators.

**Testing Approach:**
- **Test Type:** Unit tests
- **Test Description:** Test output formatting functions
- **Test File:** `anvil/tests/test_cli_formatting.py`
- **Test Cases:**
  - Test section header with box-drawing characters (╔═╗)
  - Test validator result line with checkmark/x (✓/✗)
  - Test error message formatting with [ERROR] prefix
  - Test warning message formatting with [WARNING] prefix
  - Test colored output (when enabled)
  - Test plain text output (when disabled)
  - Test output with ANSI color codes
  - Test output without ANSI codes (for CI)
  - Test progress indicator for slow operations
  - Test summary table formatting
  - Test file path truncation for long paths
  - Test message wrapping for long messages
- **Success Criteria:** Output is visually appealing and readable, colors work correctly, 95% coverage

---

## Iteration 9: Integration & Documentation

### Overview

Integration testing across all components, performance optimization, and comprehensive documentation.

---

### Step 9.1: End-to-End Integration Tests

**Description:** Implement comprehensive end-to-end tests that validate entire workflows.

**Testing Approach:**
- **Test Type:** End-to-end integration tests
- **Test Description:** Test complete Anvil workflows
- **Test File:** `anvil/tests/integration/test_end_to_end.py`
- **Test Cases:**
  - Test complete validation workflow: detect languages → collect files → run validators → aggregate results → report
  - Test Python-only project validation
  - Test C++-only project validation
  - Test mixed Python/C++ project validation
  - Test incremental mode with git changes
  - Test full mode (all files)
  - Test with pre-commit hook trigger
  - Test with CI/CD simulation
  - Test with smart filtering enabled
  - Test with parallel execution
  - Test with fail-fast mode
  - Test with configuration from anvil.toml
  - Test with zero-config (defaults only)
  - Test with statistics tracking enabled
  - Test error recovery (validator crash, missing tool)
  - Test performance with large codebase (1000+ files)
- **Success Criteria:** All workflows work end-to-end, no integration issues, 90% coverage

---

### Step 9.2: Performance Optimization

**Description:** Profile and optimize Anvil performance for large codebases.

**Testing Approach:**
- **Test Type:** Performance benchmarks
- **Test Description:** Measure and optimize performance
- **Test File:** `anvil/tests/performance/test_benchmarks.py`
- **Test Cases:**
  - Benchmark file collection on large directory tree (10k files)
  - Benchmark language detection on mixed project
  - Benchmark validator execution (sequential vs parallel)
  - Benchmark incremental mode vs full mode
  - Benchmark database queries with large history (100+ runs)
  - Benchmark smart filtering with 1000+ tests
  - Benchmark JSON parsing for large outputs
  - Benchmark concurrent validator execution
  - Profile memory usage with large files
  - Test incremental validation completes in <5 seconds
  - Test full validation scales linearly with file count
- **Success Criteria:** Incremental validation <5s, no memory leaks, linear scaling, performance documented

---

### Step 9.3: Documentation

**Description:** Write comprehensive user guide, API documentation, and examples.

**Testing Approach:**
- **Test Type:** Documentation validation
- **Test Description:** Ensure all documentation examples work
- **Test File:** Manual validation + `anvil/docs/test_doc_examples.py`
- **Test Cases:**
  - Test all CLI examples in USER_GUIDE.md
  - Test all configuration examples
  - Test all workflow examples
  - Validate README.md examples
  - Validate API.md code samples
  - Test tutorial end-to-end
  - Test troubleshooting guide scenarios
- **Success Criteria:** All documentation complete, examples tested, 100% accuracy

**Documentation Deliverables:**
- `anvil/docs/USER_GUIDE.md` - Comprehensive user guide with examples
- `anvil/docs/API.md` - API documentation for extending Anvil
- `anvil/docs/CONFIGURATION.md` - Complete configuration reference
- `anvil/docs/TROUBLESHOOTING.md` - Common issues and solutions
- `anvil/README.md` - Quick start guide
- `anvil/TUTORIAL.md` - Step-by-step tutorial
- `docs/INTEGRATION.md` - Guide for integrating Anvil with CI/CD

---

### Step 9.4: Cross-Platform Testing

**Description:** Test Anvil on Windows, Linux, and macOS with CI matrix.

**Testing Approach:**
- **Test Type:** CI/CD matrix testing
- **Test Description:** Validate cross-platform compatibility
- **CI Configuration:** GitHub Actions matrix
- **Test Cases:**
  - Test on Ubuntu Linux (latest)
  - Test on Windows Server (latest)
  - Test on macOS (latest)
  - Test with Python 3.8, 3.9, 3.10, 3.11, 3.12
  - Test with various validator tool versions
  - Test path handling (Windows \ vs Unix /)
  - Test line ending handling (CRLF vs LF)
  - Test permissions (hook executability)
  - Test with different shells (bash, zsh, PowerShell)
  - Test git hook integration on each platform
  - Test parallel execution on each platform
- **Success Criteria:** All tests pass on all platforms, CI configured, compatibility matrix documented

---

## Summary

### Development Timeline

- **Iteration 1 (Core Framework)**: 2 weeks
- **Iteration 2 (Python Linting/Formatting)**: 1.5 weeks
- **Iteration 3 (Python Static Analysis)**: 1.5 weeks
- **Iteration 4 (Python Testing)**: 1 week
- **Iteration 5 (C++ Static Analysis)**: 2 weeks
- **Iteration 6 (C++ Formatting/Testing)**: 1.5 weeks
- **Iteration 7 (Statistics)**: 2 weeks
- **Iteration 8 (Git Hooks & CLI)**: 1.5 weeks
- **Iteration 9 (Integration & Documentation)**: 2 weeks

**Total Estimated Time**: 15 weeks

### Test Coverage Goals

- **Core Framework**: 100% coverage
- **Validators (unit tests)**: 95% coverage per validator
- **Validators (integration tests)**: 90% coverage
- **Statistics**: 95% coverage
- **CLI**: 100% coverage
- **Overall**: ≥95% coverage

### Success Criteria

- All validators implemented for Python and C++
- Statistics tracking and smart filtering functional
- Git hook integration working
- CLI complete with all commands
- Performance targets met (incremental <5s)
- Cross-platform compatibility verified
- Documentation complete with tested examples
- All tests passing on Linux, Windows, macOS
- Ready for production use

---

**Next Steps:**
1. Review implementation plan
2. Set up Anvil project structure
3. Begin with Iteration 1: Core Framework
4. Follow TDD approach for all development
5. Run pre-commit checks after each step
6. Update progress tracking as features complete

---

**Plan Version**: 1.0
**Created**: 2026-01-29
**Status**: Ready for implementation
**Prerequisites**: Forge Iteration 1 complete
