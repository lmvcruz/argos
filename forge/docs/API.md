# Forge API Documentation

This document provides comprehensive API documentation for the Forge CMake build wrapper.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Data Models](#data-models)
- [Utilities](#utilities)
- [Command Line Interface](#command-line-interface)

## Installation

```bash
pip install forge
```

Or install from source:

```bash
git clone https://github.com/yourusername/forge.git
cd forge
pip install -e .
```

## Quick Start

### Basic Usage

Run a CMake configuration and build:

```bash
forge build /path/to/build/dir --source /path/to/source
```

Build only (skip configuration):

```bash
forge build /path/to/build/dir --no-configure
```

### Python API

```python
from pathlib import Path
from forge.models.arguments import ForgeArguments
from forge.cmake.executor import CMakeExecutor
from forge.cmake.parameter_manager import CMakeParameterManager

# Create arguments
args = ForgeArguments(
    build_dir=Path("build"),
    source_dir=Path("src"),
    verbose=True
)

# Setup CMake parameters
param_manager = CMakeParameterManager(args)
configure_cmd = param_manager.build_configure_command()

# Execute
executor = CMakeExecutor()
result = executor.execute_configure(configure_cmd, working_dir=args.build_dir)

if result.success:
    print(f"Configuration completed in {result.duration:.2f}s")
else:
    print(f"Configuration failed: {result.stderr}")
```

## Core Components

### CMake Execution

#### CMakeExecutor

Executes CMake commands and captures output.

```python
from forge.cmake.executor import CMakeExecutor
from pathlib import Path

executor = CMakeExecutor(cmake_command="cmake")

# Execute configure
result = executor.execute_configure(
    command=["cmake", "-B", "build", "-S", "."],
    working_dir=Path("."),
    stream_output=True
)

# Execute build
build_result = executor.execute_build(
    command=["cmake", "--build", "build"],
    working_dir=Path("."),
    stream_output=True
)
```

**Methods:**

- `execute_configure(command, working_dir, timeout, stream_output)`: Execute CMake configure step
  - Returns: `ConfigureResult`
  - Parameters:
    - `command`: List of command arguments
    - `working_dir`: Directory to run command in
    - `timeout`: Optional timeout in seconds
    - `stream_output`: Whether to stream output to console

- `execute_build(command, working_dir, timeout, stream_output)`: Execute CMake build step
  - Returns: `BuildResult`
  - Parameters: Same as `execute_configure`

- `check_cmake_available()`: Check if CMake is available on the system
  - Returns: `bool`

- `get_cmake_version()`: Get CMake version string
  - Returns: `Optional[str]` (e.g., "3.27.1")

#### CMakeParameterManager

Manages CMake command-line parameters and generator selection.

```python
from forge.cmake.parameter_manager import CMakeParameterManager
from forge.models.arguments import ForgeArguments
from pathlib import Path

args = ForgeArguments(
    build_dir=Path("build"),
    source_dir=Path("src"),
    cmake_args=["-DCMAKE_BUILD_TYPE=Release"]
)

manager = CMakeParameterManager(args)

# Build configure command
configure_cmd = manager.build_configure_command()
# Output: ["cmake", "-B", "build", "-S", "src", "-DCMAKE_BUILD_TYPE=Release"]

# Build build command
build_cmd = manager.build_build_command()
# Output: ["cmake", "--build", "build"]

# Add parameter programmatically
manager.add_parameter("CMAKE_EXPORT_COMPILE_COMMANDS", "ON")
```

**Methods:**

- `build_configure_command()`: Build complete CMake configure command
  - Returns: `List[str]`

- `build_build_command()`: Build complete CMake build command
  - Returns: `List[str]`

- `add_parameter(key, value)`: Add or override a CMake parameter
  - Parameters:
    - `key`: CMake variable name (without -D prefix)
    - `value`: Value to set

- `detect_generator()`: Detect or select appropriate CMake generator
  - Returns: `Optional[str]` (e.g., "Ninja", "Unix Makefiles")

### Build Inspection

#### BuildInspector

Analyzes build output to extract metadata, warnings, and errors.

```python
from forge.inspector.build_inspector import BuildInspector
from pathlib import Path

inspector = BuildInspector(source_dir=Path("src"))

# Inspect configuration output
configure_metadata = inspector.inspect_configure_output(
    output="CMake output text...",
    success=True
)

# Inspect build output
build_metadata = inspector.inspect_build_output(
    output="Build output text...",
    success=True
)

# Extract warnings and errors
warnings = inspector.extract_warnings("Build output with warnings...")
errors = inspector.extract_errors("Build output with errors...")

# Detect project name
project_name = inspector.detect_project_name()
```

**Methods:**

- `inspect_configure_output(output, success)`: Extract configuration metadata
  - Returns: `ConfigureMetadata`

- `inspect_build_output(output, success)`: Extract build metadata
  - Returns: `BuildMetadata`

- `extract_warnings(output)`: Parse compiler warnings from output
  - Returns: `List[BuildWarning]`

- `extract_errors(output)`: Parse compiler errors from output
  - Returns: `List[Error]`

- `extract_targets(output)`: Extract built targets from output
  - Returns: `List[str]`

- `detect_project_name()`: Detect project name from CMakeLists.txt
  - Returns: `Optional[str]`

### Data Persistence

#### DataPersistence

Stores build data in SQLite database for history and analysis.

```python
from forge.storage.persistence import DataPersistence
from pathlib import Path

# Initialize database
db = DataPersistence(db_path=Path(".forge/forge.db"))
db.initialize_database()

# Save configuration
config_id = db.save_configuration(configure_result)

# Save build
build_id = db.save_build(build_result, configuration_id=config_id)

# Save warnings and errors
db.save_warnings(warnings, build_id=build_id)
db.save_errors(errors, build_id=build_id)

# Query data
recent_builds = db.get_recent_builds(limit=10)
statistics = db.get_build_statistics(project_name="MyProject")
```

**Methods:**

- `initialize_database()`: Create database schema if not exists

- `save_configuration(result)`: Save configuration result
  - Returns: `int` (configuration ID)

- `save_build(result, configuration_id)`: Save build result
  - Returns: `int` (build ID)

- `save_warnings(warnings, build_id)`: Save warning records
  - Returns: `int` (number of warnings saved)

- `save_errors(errors, build_id)`: Save error records
  - Returns: `int` (number of errors saved)

- `get_recent_builds(limit, project_name)`: Get recent build records
  - Returns: `List[Dict]`

- `get_build_statistics(project_name)`: Get aggregated build statistics
  - Returns: `Dict` (success rate, average duration, etc.)

## Data Models

### ForgeArguments

Command-line arguments representation.

```python
from forge.models.arguments import ForgeArguments
from pathlib import Path

args = ForgeArguments(
    build_dir=Path("build"),
    source_dir=Path("src"),
    cmake_args=["-DCMAKE_BUILD_TYPE=Debug"],
    build_args=["--parallel", "4"],
    project_name="MyProject",
    verbose=True,
    configure=True,
    clean_build=False,
    dry_run=False
)

# Convert to dict for serialization
data = args.to_dict()

# Create from dict
args2 = ForgeArguments.from_dict(data)
```

**Attributes:**

- `build_dir`: Path to build directory (required)
- `source_dir`: Path to source directory
- `cmake_args`: Arguments for CMake configure
- `build_args`: Arguments for CMake build
- `project_name`: Project name override
- `server_url`: Argus server URL for data upload
- `verbose`: Enable verbose output
- `configure`: Whether to run configure step
- `clean_build`: Clean build directory first
- `dry_run`: Don't execute, just show commands
- `database_path`: Custom database location

### ConfigureResult

Results from CMake configuration step.

```python
from forge.models.results import ConfigureResult
from datetime import datetime

result = ConfigureResult(
    success=True,
    exit_code=0,
    stdout="CMake output...",
    stderr="",
    duration=2.5,
    start_time=datetime.now(),
    end_time=datetime.now(),
    metadata=configure_metadata  # ConfigureMetadata object
)
```

**Attributes:**

- `success`: Whether configuration succeeded
- `exit_code`: Process exit code
- `stdout`: Standard output text
- `stderr`: Standard error text
- `duration`: Duration in seconds
- `start_time`: Start timestamp
- `end_time`: End timestamp
- `metadata`: ConfigureMetadata object (optional)

### BuildResult

Results from CMake build step.

```python
from forge.models.results import BuildResult

result = BuildResult(
    success=True,
    exit_code=0,
    stdout="Build output...",
    stderr="",
    duration=15.3,
    start_time=datetime.now(),
    end_time=datetime.now(),
    metadata=build_metadata  # BuildMetadata object
)
```

**Attributes:** Same as ConfigureResult, with `metadata` being `BuildMetadata`.

### ConfigureMetadata

Metadata extracted from configuration output.

```python
from forge.models.metadata import ConfigureMetadata

metadata = ConfigureMetadata(
    project_name="MyProject",
    cmake_version="3.27.1",
    generator="Ninja",
    c_compiler="/usr/bin/gcc",
    cxx_compiler="/usr/bin/g++",
    system_name="Linux",
    system_processor="x86_64",
    build_type="Release",
    found_packages=["OpenSSL", "Boost"]
)
```

### BuildMetadata

Metadata extracted from build output.

```python
from forge.models.metadata import BuildMetadata

metadata = BuildMetadata(
    targets=["myapp", "mylib"],
    warning_count=2,
    error_count=0,
    files_compiled=42,
    parallel_jobs=4
)
```

### BuildWarning / Error

Represents a compiler warning or error.

```python
from forge.models.metadata import BuildWarning, Error

warning = BuildWarning(
    file="src/main.cpp",
    line=42,
    column=15,
    message="unused variable 'x'",
    warning_type="unused-variable"
)

error = Error(
    file="src/util.cpp",
    line=10,
    column=5,
    message="expected ';' before '}'",
    error_type="syntax-error"
)
```

## Utilities

### Formatting

Output formatting utilities for console display.

```python
from forge.utils.formatting import (
    format_duration,
    format_timestamp,
    print_success,
    print_error,
    print_warning,
    print_section_header,
    print_configure_summary,
    print_build_summary,
    supports_color
)

# Format duration
duration_str = format_duration(125.5)  # "2m 5s"

# Format timestamp
from datetime import datetime
ts_str = format_timestamp(datetime.now())  # "2026-01-29 14:30:45"

# Print colored messages
print_success("Build completed successfully!")
print_error("Build failed")
print_warning("Found 3 warnings")

# Print summaries
print_configure_summary(configure_result, verbose=True)
print_build_summary(build_result, verbose=False)

# Check color support
if supports_color():
    print("Terminal supports colors")
```

### Logging Configuration

```python
from forge.utils.logging_config import configure_logging, get_logger

# Configure logging
configure_logging(verbose=True, log_file="forge.log")

# Get logger
logger = get_logger(__name__)
logger.info("Starting build")
logger.debug("Detailed debug information")
logger.error("Build failed", exc_info=True)
```

## Command Line Interface

### Basic Commands

```bash
# Configure and build
forge build /path/to/build --source /path/to/source

# Build only (skip configure)
forge build /path/to/build --no-configure

# Verbose output
forge build /path/to/build -v

# Pass CMake arguments
forge build /path/to/build --cmake-args="-DCMAKE_BUILD_TYPE=Debug" "-DENABLE_TESTS=ON"

# Pass build arguments
forge build /path/to/build --build-args="--parallel" "8"

# Clean build
forge build /path/to/build --clean

# Dry run
forge build /path/to/build --dry-run

# Custom database
forge build /path/to/build --database /custom/path/forge.db

# Project name override
forge build /path/to/build --project-name MyProject
```

### Exit Codes

- `0`: Success
- `1`: Configuration failed
- `2`: Build failed
- `3`: CMake not found
- `127`: Command not found
- Other: Propagated from CMake

## Best Practices

### 1. Error Handling

Always check result objects for success:

```python
result = executor.execute_configure(cmd, working_dir=build_dir)
if not result.success:
    print(f"Configuration failed with exit code {result.exit_code}")
    print(f"Error output: {result.stderr}")
    return result.exit_code
```

### 2. Verbose Output

Enable verbose mode for debugging:

```python
args = ForgeArguments(
    build_dir=Path("build"),
    verbose=True  # Show detailed output
)
```

### 3. Database Management

Use a consistent database location:

```python
db_path = Path.home() / ".forge" / "forge.db"
db = DataPersistence(db_path=db_path)
db.initialize_database()
```

### 4. Platform Detection

Let Forge auto-detect the best generator:

```python
param_manager = CMakeParameterManager(args)
generator = param_manager.detect_generator()
# Returns "Ninja" on Unix if available, "Unix Makefiles" otherwise
# Returns "Ninja" or "Visual Studio" on Windows
```

### 5. Output Inspection

Always inspect build output for warnings:

```python
inspector = BuildInspector(source_dir=args.source_dir)
warnings = inspector.extract_warnings(result.stdout)

if warnings:
    print(f"Found {len(warnings)} warnings:")
    for warning in warnings[:5]:  # Show first 5
        print(f"  {warning.file}:{warning.line}: {warning.message}")
```

## Examples

### Complete Build Workflow

```python
from pathlib import Path
from forge.models.arguments import ForgeArguments
from forge.cmake.executor import CMakeExecutor
from forge.cmake.parameter_manager import CMakeParameterManager
from forge.inspector.build_inspector import BuildInspector
from forge.storage.persistence import DataPersistence
from forge.utils.formatting import print_configure_summary, print_build_summary

# Setup
args = ForgeArguments(
    build_dir=Path("build"),
    source_dir=Path("src"),
    cmake_args=["-DCMAKE_BUILD_TYPE=Release"],
    verbose=True
)

# Initialize components
param_manager = CMakeParameterManager(args)
executor = CMakeExecutor()
inspector = BuildInspector(source_dir=args.source_dir)
db = DataPersistence()
db.initialize_database()

# Configure
configure_cmd = param_manager.build_configure_command()
configure_result = executor.execute_configure(
    configure_cmd,
    working_dir=args.build_dir
)

if not configure_result.success:
    print_configure_summary(configure_result)
    exit(1)

# Inspect configure output
configure_metadata = inspector.inspect_configure_output(
    configure_result.stdout,
    configure_result.success
)
configure_result.metadata = configure_metadata

# Save configuration
config_id = db.save_configuration(configure_result)

print_configure_summary(configure_result, verbose=True)

# Build
build_cmd = param_manager.build_build_command()
build_result = executor.execute_build(
    build_cmd,
    working_dir=args.build_dir
)

# Inspect build output
build_metadata = inspector.inspect_build_output(
    build_result.stdout,
    build_result.success
)
build_result.metadata = build_metadata

# Extract diagnostics
warnings = inspector.extract_warnings(build_result.stdout)
errors = inspector.extract_errors(build_result.stderr)

# Save build data
build_id = db.save_build(build_result, configuration_id=config_id)
db.save_warnings(warnings, build_id=build_id)
db.save_errors(errors, build_id=build_id)

print_build_summary(build_result, verbose=True)

exit(0 if build_result.success else 2)
```

### Query Build History

```python
from forge.storage.persistence import DataPersistence
from pathlib import Path

db = DataPersistence(db_path=Path(".forge/forge.db"))

# Get recent builds
builds = db.get_recent_builds(limit=10, project_name="MyProject")

print("Recent builds:")
for build in builds:
    status = "✓" if build["success"] else "✗"
    print(f"{status} {build['timestamp']} - {build['duration']:.1f}s")

# Get statistics
stats = db.get_build_statistics(project_name="MyProject")
print(f"\nBuild Statistics:")
print(f"Total builds: {stats['total_builds']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average duration: {stats['avg_duration']:.1f}s")
print(f"Total warnings: {stats['total_warnings']}")
print(f"Total errors: {stats['total_errors']}")
```

## API Reference Summary

### Classes

- `CMakeExecutor`: Execute CMake commands
- `CMakeParameterManager`: Manage CMake parameters
- `BuildInspector`: Analyze build output
- `DataPersistence`: SQLite database operations
- `ForgeArguments`: Command-line arguments
- `ConfigureResult`: Configuration results
- `BuildResult`: Build results
- `ConfigureMetadata`: Configuration metadata
- `BuildMetadata`: Build metadata
- `BuildWarning`: Warning information
- `Error`: Error information

### Functions

- `format_duration(seconds)`: Format duration string
- `format_timestamp(timestamp)`: Format timestamp string
- `print_success(message)`: Print success message
- `print_error(message)`: Print error message
- `print_warning(message)`: Print warning message
- `print_section_header(title)`: Print section header
- `print_configure_summary(result, verbose)`: Print configuration summary
- `print_build_summary(result, verbose)`: Print build summary
- `supports_color()`: Check terminal color support
- `configure_logging(verbose, log_file)`: Configure logging
- `get_logger(name)`: Get logger instance

## Contributing

See the main README.md for contribution guidelines.

## License

See LICENSE file for details.
