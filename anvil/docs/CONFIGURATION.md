# Anvil Configuration Reference

## Table of Contents

1. [Configuration File](#configuration-file)
2. [Project Section](#project-section)
3. [Validation Section](#validation-section)
4. [Python Configuration](#python-configuration)
5. [C++ Configuration](#c-configuration)
6. [Statistics Configuration](#statistics-configuration)
7. [Smart Filtering Configuration](#smart-filtering-configuration)
8. [Complete Example](#complete-example)
9. [Configuration Precedence](#configuration-precedence)
10. [Environment Variables](#environment-variables)

## Configuration File

Anvil uses TOML format for configuration. Place `anvil.toml` in your project root.

### Minimal Configuration

```toml
[project]
name = "my-project"
languages = ["python"]
```

### Generate Default Configuration

```bash
anvil config init
```

This creates `anvil.toml` with default values.

## Project Section

Defines project metadata and languages.

```toml
[project]
name = "project-name"      # Project name (required)
version = "1.0.0"          # Project version (optional)
languages = ["python"]     # Languages to validate (required)
```

### `name`
- **Type**: `string`
- **Required**: Yes
- **Description**: Project name for reporting and statistics
- **Example**: `"my-awesome-project"`

### `version`
- **Type**: `string`
- **Required**: No
- **Description**: Project version for tracking
- **Example**: `"1.2.3"` or `"2024.01"`

### `languages`
- **Type**: `array of strings`
- **Required**: Yes
- **Valid Values**: `"python"`, `"cpp"`
- **Description**: Languages to validate
- **Examples**:
  - `["python"]` - Python only
  - `["cpp"]` - C++ only
  - `["python", "cpp"]` - Both languages

## Validation Section

Controls validation behavior.

```toml
[validation]
mode = "full"              # Validation mode: "full" or "incremental"
fail_fast = false          # Stop on first error
parallel = true            # Run validators in parallel
max_workers = 4            # Maximum parallel workers
timeout = 300              # Global timeout in seconds
```

### `mode`
- **Type**: `string`
- **Default**: `"full"`
- **Valid Values**: `"full"`, `"incremental"`
- **Description**: Default validation mode
  - `"full"`: Validate all files
  - `"incremental"`: Only validate changed files (git diff)
- **Override**: `anvil check --incremental`

### `fail_fast`
- **Type**: `boolean`
- **Default**: `false`
- **Description**: Stop validation after first error
- **Override**: `anvil check --fail-fast`
- **Use Case**: Fast feedback during development

### `parallel`
- **Type**: `boolean`
- **Default**: `true`
- **Description**: Run validators concurrently
- **Note**: Improves performance on multi-core systems

### `max_workers`
- **Type**: `integer`
- **Default**: `4`
- **Range**: `1` to `CPU count`
- **Description**: Maximum concurrent validators
- **Recommendation**: Set to number of CPU cores

### `timeout`
- **Type**: `integer`
- **Default**: `300`
- **Unit**: seconds
- **Description**: Global timeout for all validators
- **Note**: Individual validators may have shorter timeouts

## Python Configuration

Configuration for Python validators.

### Enable/Disable Python Validation

```toml
[python]
enabled = true             # Enable Python validation
```

### Python Validators

#### flake8 - Linting and Style

```toml
[python.flake8]
enabled = true
max_line_length = 100
max_complexity = 10
exclude = [
    "build/",
    "dist/",
    ".git/",
    "__pycache__/",
    "*.egg-info/"
]
ignore = []                # Error codes to ignore (e.g., ["E203", "W503"])
per_file_ignores = {}      # Per-file ignore rules
```

**Options:**
- `enabled` (bool): Enable flake8
- `max_line_length` (int): Maximum line length (default: 100)
- `max_complexity` (int): Maximum cyclomatic complexity (default: 10)
- `exclude` (array): Directories/patterns to exclude
- `ignore` (array): Error codes to ignore globally
- `per_file_ignores` (dict): Per-file ignore rules
  - Example: `{"__init__.py" = ["F401"]}`

#### black - Code Formatting

```toml
[python.black]
enabled = true
line_length = 100
check = true               # Check mode (don't modify files)
target_version = ["py38"]  # Target Python version
exclude = []               # Patterns to exclude
```

**Options:**
- `enabled` (bool): Enable black
- `line_length` (int): Line length (default: 100)
- `check` (bool): Check mode vs format mode (default: true)
- `target_version` (array): Target Python versions
  - Valid: `["py38", "py39", "py310", "py311", "py312"]`
- `exclude` (array): File patterns to exclude

#### isort - Import Sorting

```toml
[python.isort]
enabled = true
line_length = 100
profile = "black"          # Compatible with black
force_single_line = false
known_first_party = []     # First-party module names
known_third_party = []     # Third-party module names
```

**Options:**
- `enabled` (bool): Enable isort
- `line_length` (int): Line length (default: 100)
- `profile` (string): Preset configuration
  - Valid: `"black"`, `"django"`, `"pycharm"`, `"google"`, `"open_stack"`
- `force_single_line` (bool): One import per line
- `known_first_party` (array): First-party modules
- `known_third_party` (array): Third-party modules

#### pylint - Static Analysis

```toml
[python.pylint]
enabled = true
min_score = 8.0            # Minimum acceptable score (0-10)
max_line_length = 100
disable = []               # Checks to disable (e.g., ["C0111", "R0903"])
jobs = 1                   # Parallel jobs (0 = auto)
```

**Options:**
- `enabled` (bool): Enable pylint
- `min_score` (float): Minimum score (0.0-10.0, default: 8.0)
- `max_line_length` (int): Maximum line length (default: 100)
- `disable` (array): Check codes to disable
- `jobs` (int): Parallel jobs (0 = auto, default: 1)

#### pytest - Testing

```toml
[python.pytest]
enabled = true
min_coverage = 90.0        # Minimum coverage percentage
test_paths = ["tests/"]    # Test directories
markers = []               # Test markers to run
keywords = []              # Test keywords to run (-k)
parallel = true            # Run tests in parallel
max_workers = "auto"       # Parallel workers
reruns = 0                 # Retry failed tests
```

**Options:**
- `enabled` (bool): Enable pytest
- `min_coverage` (float): Minimum coverage % (0-100, default: 90.0)
- `test_paths` (array): Test directories (default: `["tests/"]`)
- `markers` (array): Markers to run (e.g., `["unit", "integration"]`)
- `keywords` (array): Keywords to run
- `parallel` (bool): Use pytest-xdist (default: true)
- `max_workers` (string/int): Workers for parallel (default: `"auto"`)
- `reruns` (int): Retry failed tests (requires pytest-rerunfailures)

#### autoflake - Unused Code Detection

```toml
[python.autoflake]
enabled = true
check = true               # Check mode (don't modify files)
remove_all_unused_imports = true
remove_unused_variables = true
exclude = []               # Patterns to exclude
```

**Options:**
- `enabled` (bool): Enable autoflake
- `check` (bool): Check mode vs fix mode (default: true)
- `remove_all_unused_imports` (bool): Remove all unused imports
- `remove_unused_variables` (bool): Remove unused variables
- `exclude` (array): File patterns to exclude

#### radon - Complexity Analysis

```toml
[python.radon]
enabled = true
cc_min = "B"               # Cyclomatic complexity threshold
mi_min = 50.0              # Maintainability index minimum
show_complexity = true     # Show complexity in output
```

**Options:**
- `enabled` (bool): Enable radon
- `cc_min` (string): Complexity grade threshold
  - Valid: `"A"` (best), `"B"`, `"C"`, `"D"`, `"E"`, `"F"` (worst)
- `mi_min` (float): Maintainability index (0-100, default: 50.0)
- `show_complexity` (bool): Display complexity in output

#### vulture - Dead Code Detection

```toml
[python.vulture]
enabled = true
min_confidence = 80        # Minimum confidence % (0-100)
exclude = []               # Patterns to exclude
ignore_decorators = []     # Decorators to ignore
```

**Options:**
- `enabled` (bool): Enable vulture
- `min_confidence` (int): Confidence threshold (0-100, default: 80)
- `exclude` (array): File patterns to exclude
- `ignore_decorators` (array): Decorators that mark code as used

## C++ Configuration

Configuration for C++ validators.

### Enable/Disable C++ Validation

```toml
[cpp]
enabled = true             # Enable C++ validation
std = "c++17"              # C++ standard
include_dirs = []          # Include directories
defines = []               # Preprocessor defines
```

### C++ Validators

#### clang-tidy - Static Analysis

```toml
[cpp.clang-tidy]
enabled = true
checks = ["*"]             # Checks to enable
header_filter = ".*"       # Header file regex
format_style = "file"      # Format style (file, llvm, google, etc.)
extra_args = []            # Extra compiler arguments
compile_commands = "build/compile_commands.json"
```

**Options:**
- `enabled` (bool): Enable clang-tidy
- `checks` (array): Check patterns (default: `["*"]`)
  - Enable: `"modernize-*"`, `"readability-*"`
  - Disable: `"-readability-braces-around-statements"`
- `header_filter` (string): Regex for headers to check (default: `".*"`)
- `format_style` (string): Format style (default: `"file"`)
- `extra_args` (array): Compiler arguments (e.g., `["-std=c++17"]`)
- `compile_commands` (string): Path to compile_commands.json

#### cppcheck - Bug Detection

```toml
[cpp.cppcheck]
enabled = true
std = "c++17"              # C++ standard
enable = [                 # Categories to enable
    "warning",
    "style",
    "performance",
    "portability"
]
suppress = []              # Suppressions (e.g., ["uninitvar:file.cpp:10"])
platform = "unix64"        # Target platform
inconclusive = false       # Show inconclusive warnings
```

**Options:**
- `enabled` (bool): Enable cppcheck
- `std` (string): C++ standard (c++11, c++14, c++17, c++20, etc.)
- `enable` (array): Categories to check
  - Valid: `"warning"`, `"style"`, `"performance"`, `"portability"`, `"information"`
- `suppress` (array): Specific suppressions
- `platform` (string): Target platform (unix32, unix64, win32, win64)
- `inconclusive` (bool): Report inconclusive results

#### cpplint - Style Checking

```toml
[cpp.cpplint]
enabled = true
linelength = 100           # Maximum line length
filter = []                # Filters (e.g., ["-whitespace/braces"])
root = "."                 # Project root for header guards
extensions = ["cpp", "cc", "h", "hpp"]
```

**Options:**
- `enabled` (bool): Enable cpplint
- `linelength` (int): Maximum line length (default: 100)
- `filter` (array): Category filters
  - Disable: `"-whitespace/braces"`, `"-build/include_order"`
- `root` (string): Root for header guard checks
- `extensions` (array): File extensions to check

#### clang-format - Formatting

```toml
[cpp.clang-format]
enabled = true
style = "Google"           # Format style or path to .clang-format
fallback_style = "LLVM"    # Fallback if style not found
```

**Options:**
- `enabled` (bool): Enable clang-format
- `style` (string): Style name or path
  - Predefined: `"LLVM"`, `"Google"`, `"Chromium"`, `"Mozilla"`, `"WebKit"`, `"Microsoft"`
  - Path: `"file"` or `"/path/to/.clang-format"`
- `fallback_style` (string): Fallback style if file not found

#### include-what-you-use (IWYU) - Include Analysis

```toml
[cpp.iwyu]
enabled = true
mapping_file = ""          # Path to mapping file
extra_args = []            # Extra compiler arguments
```

**Options:**
- `enabled` (bool): Enable IWYU
- `mapping_file` (string): Path to IWYU mapping file
- `extra_args` (array): Compiler arguments

#### Google Test - Testing

```toml
[cpp.gtest]
enabled = true
test_binary = "build/tests/test_runner"  # Path to test executable
filter = ""                # Test filter (e.g., "MyTest.*")
repeat = 1                 # Repeat tests N times
shuffle = false            # Shuffle test order
output = "json"            # Output format (json, xml)
```

**Options:**
- `enabled` (bool): Enable Google Test
- `test_binary` (string): Path to test executable (required)
- `filter` (string): Test name filter (googletest --gtest_filter)
- `repeat` (int): Repeat tests N times (default: 1)
- `shuffle` (bool): Randomize test order
- `output` (string): Output format (`"json"` or `"xml"`)

## Statistics Configuration

Track validation history for analytics and smart filtering.

```toml
[statistics]
enabled = true                    # Enable statistics tracking
database = ".anvil/stats.db"      # Database path
retention_days = 90               # Days to keep history
```

### `enabled`
- **Type**: `boolean`
- **Default**: `true`
- **Description**: Enable statistics tracking
- **Note**: Required for smart filtering

### `database`
- **Type**: `string`
- **Default**: `".anvil/stats.db"`
- **Description**: SQLite database path
- **Note**: Relative to project root

### `retention_days`
- **Type**: `integer`
- **Default**: `90`
- **Description**: Days to retain history
- **Note**: Old records automatically deleted

## Smart Filtering Configuration

Optimize test execution using historical data.

```toml
[smart-filtering]
enabled = true                    # Enable smart filtering
skip_success_threshold = 0.95     # Skip tests above success rate
prioritize_flaky = true           # Run flaky tests first
min_history_runs = 10             # Minimum runs before filtering
```

### `enabled`
- **Type**: `boolean`
- **Default**: `false`
- **Description**: Enable smart filtering
- **Requirements**: Statistics must be enabled

### `skip_success_threshold`
- **Type**: `float`
- **Range**: `0.0` to `1.0`
- **Default**: `0.95`
- **Description**: Skip tests with success rate above threshold
- **Example**: `0.95` = skip tests passing 95%+ of the time

### `prioritize_flaky`
- **Type**: `boolean`
- **Default**: `true`
- **Description**: Run flaky tests first
- **Note**: Helps catch intermittent failures early

### `min_history_runs`
- **Type**: `integer`
- **Default**: `10`
- **Description**: Minimum runs before applying filters
- **Note**: Ensures sufficient data for decisions

## Complete Example

Full configuration with all options:

```toml
# Project metadata
[project]
name = "my-awesome-project"
version = "2.0.0"
languages = ["python", "cpp"]

# Validation behavior
[validation]
mode = "full"
fail_fast = false
parallel = true
max_workers = 4
timeout = 300

# Python validation
[python]
enabled = true

[python.flake8]
enabled = true
max_line_length = 100
max_complexity = 10
exclude = ["build/", ".git/", "__pycache__/"]
ignore = ["E203", "W503"]

[python.black]
enabled = true
line_length = 100
check = true
target_version = ["py38", "py39", "py310"]

[python.isort]
enabled = true
line_length = 100
profile = "black"
known_first_party = ["myproject"]

[python.pylint]
enabled = true
min_score = 8.0
disable = ["C0111", "R0903"]

[python.pytest]
enabled = true
min_coverage = 90.0
test_paths = ["tests/"]
parallel = true
max_workers = "auto"
reruns = 3

[python.autoflake]
enabled = true
check = true
remove_all_unused_imports = true

[python.radon]
enabled = true
cc_min = "B"
mi_min = 50.0

[python.vulture]
enabled = true
min_confidence = 80

# C++ validation
[cpp]
enabled = true
std = "c++17"

[cpp.clang-tidy]
enabled = true
checks = [
    "*",
    "-readability-braces-around-statements",
    "-modernize-use-trailing-return-type"
]
compile_commands = "build/compile_commands.json"

[cpp.cppcheck]
enabled = true
std = "c++17"
enable = ["warning", "style", "performance"]

[cpp.cpplint]
enabled = true
linelength = 100
filter = ["-whitespace/braces"]

[cpp.clang-format]
enabled = true
style = "Google"

[cpp.gtest]
enabled = true
test_binary = "build/tests/all_tests"
output = "json"

# Statistics tracking
[statistics]
enabled = true
database = ".anvil/stats.db"
retention_days = 90

# Smart filtering
[smart-filtering]
enabled = true
skip_success_threshold = 0.95
prioritize_flaky = true
min_history_runs = 10
```

## Configuration Precedence

Configuration is loaded in order (later overrides earlier):

1. **Default Values**: Built-in defaults
2. **anvil.toml**: Project configuration file
3. **Environment Variables**: Runtime overrides
4. **Command-Line Arguments**: Explicit overrides

### Example

```toml
# anvil.toml
[validation]
mode = "full"
```

```bash
# Environment variable overrides config file
export ANVIL_VALIDATION_MODE=incremental

# Command-line overrides everything
anvil check --incremental
```

## Environment Variables

Override configuration with environment variables.

### Format

`ANVIL_<SECTION>_<KEY>=<value>`

### Examples

```bash
# Project
export ANVIL_PROJECT_NAME=myproject

# Validation
export ANVIL_VALIDATION_MODE=incremental
export ANVIL_VALIDATION_FAIL_FAST=true
export ANVIL_VALIDATION_PARALLEL=false

# Python flake8
export ANVIL_PYTHON_FLAKE8_ENABLED=true
export ANVIL_PYTHON_FLAKE8_MAX_LINE_LENGTH=120

# Python pytest
export ANVIL_PYTHON_PYTEST_MIN_COVERAGE=85.0

# Statistics
export ANVIL_STATISTICS_ENABLED=false

# Database path
export ANVIL_STATISTICS_DATABASE=/tmp/anvil-stats.db
```

### Use Cases

- **CI/CD**: Override settings per environment
- **Development**: Temporary configuration changes
- **Testing**: Isolate test configuration

## Validation

### Validate Configuration

```bash
# Check configuration validity
anvil config validate

# Show parsed configuration
anvil config show
```

### Common Errors

#### Missing Required Fields

```toml
[project]
# Missing 'name' - ERROR
languages = ["python"]
```

**Error**: `Configuration error: Missing required field 'project.name'`

#### Invalid Language

```toml
[project]
name = "myproject"
languages = ["java"]  # Invalid language
```

**Error**: `Configuration error: Invalid language 'java'. Valid: python, cpp`

#### Invalid Threshold

```toml
[python.pytest]
min_coverage = 150.0  # Invalid: > 100
```

**Error**: `Configuration error: min_coverage must be between 0 and 100`

### Configuration Help

```bash
# Generate default configuration
anvil config init

# Show available validators
anvil list --detailed

# Check tool availability
anvil config check-tools
```

## Best Practices

1. **Start Simple**: Begin with minimal config, add complexity as needed
2. **Use Defaults**: Rely on sensible defaults, override only when necessary
3. **Version Control**: Commit `anvil.toml` to repository
4. **Document Overrides**: Comment why you deviate from defaults
5. **Test Configuration**: Run `anvil config validate` regularly
6. **Tool Availability**: Use `anvil config check-tools` to verify setup

## Further Reading

- [User Guide](USER_GUIDE.md) - Using Anvil
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [API Documentation](API.md) - Extending Anvil
