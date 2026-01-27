# Forge - Technical Architecture Specification

## Overview

This document provides a detailed technical specification for Forge, covering the class architecture, data models, database schema, and implementation details. Forge is designed as a modular CLI application with clean separation of concerns, enabling future extensibility including potential GUI integration.

---

## Architecture Principles

1. **Separation of Concerns**: Each class has a single, well-defined responsibility
2. **Modularity**: Components can be tested and developed independently
3. **Extensibility**: Architecture supports future enhancements (GUI, plugins, etc.)
4. **Data Persistence**: Clear separation between data models and storage mechanisms
5. **Error Handling**: Robust error handling at each layer

---

## Class Architecture

### 1. ArgumentParser

**File**: `forge/cli/argument_parser.py`

**Responsibility**: Parse and validate command-line arguments.

**Key Methods**:
```python
class ArgumentParser:
    """Handles command-line argument parsing and validation."""

    def __init__(self):
        """Initialize the argument parser with all supported options."""

    def parse_args(self, argv: List[str] = None) -> ForgeArguments:
        """
        Parse command-line arguments.

        Args:
            argv: Command-line arguments (uses sys.argv if None)

        Returns:
            ForgeArguments object with parsed and validated arguments

        Raises:
            ArgumentError: If arguments are invalid or conflicting
        """

    def validate_arguments(self, args: ForgeArguments) -> bool:
        """
        Validate parsed arguments for logical consistency.

        Args:
            args: Parsed arguments to validate

        Returns:
            True if arguments are valid

        Raises:
            ArgumentError: If validation fails
        """

    def print_help(self) -> None:
        """Print help message with usage examples."""

    def print_version(self) -> None:
        """Print version information."""
```

**Data Model**:
```python
@dataclass
class ForgeArguments:
    """Container for parsed command-line arguments."""
    source_dir: Optional[Path]      # Source directory (triggers configure)
    build_dir: Path                  # Build directory (required)
    cmake_args: List[str]            # Additional cmake configuration args
    build_args: List[str]            # Additional build args
    project_name: Optional[str]      # Override project name
    server_url: Optional[str]        # Argus server URL (v0.3+)
    verbose: bool                    # Enable verbose logging
    dry_run: bool                    # Simulate without executing
    database_path: Optional[Path]    # Override default database location
```

---

### 2. CMakeParameterManager

**File**: `forge/cmake/parameter_manager.py`

**Responsibility**: Manage CMake parameters, including user-provided and internally generated parameters.

**Key Methods**:
```python
class CMakeParameterManager:
    """Manages CMake configuration and build parameters."""

    def __init__(self, forge_args: ForgeArguments):
        """
        Initialize with parsed forge arguments.

        Args:
            forge_args: Parsed command-line arguments
        """

    def get_configure_command(self) -> List[str]:
        """
        Build the complete cmake configuration command.

        Returns:
            List of command components [cmake, source_dir, ...args]
        """

    def get_build_command(self) -> List[str]:
        """
        Build the complete cmake build command.

        Returns:
            List of command components [cmake, --build, build_dir, ...args]
        """

    def add_parameter(self, key: str, value: str) -> None:
        """
        Add or override a CMake parameter.

        Args:
            key: Parameter name (e.g., "CMAKE_BUILD_TYPE")
            value: Parameter value
        """

    def get_parameters(self) -> Dict[str, str]:
        """
        Get all CMake parameters as key-value pairs.

        Returns:
            Dictionary of parameter names to values
        """

    def detect_generator(self) -> Optional[str]:
        """
        Detect the CMake generator to be used.

        Returns:
            Generator name if detected, None otherwise
        """
```

**Internal Data**:
```python
@dataclass
class CMakeParameters:
    """Internal representation of CMake parameters."""
    source_dir: Path
    build_dir: Path
    generator: Optional[str]
    build_type: Optional[str]
    custom_params: Dict[str, str]       # User-defined -D parameters
    environment_vars: Dict[str, str]    # Environment variables to set
    working_directory: Path             # Working directory for execution
```

---

### 3. CMakeExecutor

**File**: `forge/cmake/executor.py`

**Responsibility**: Execute CMake commands and capture output in real-time.

**Key Methods**:
```python
class CMakeExecutor:
    """Executes CMake commands and captures output."""

    def __init__(self, verbose: bool = False):
        """
        Initialize executor.

        Args:
            verbose: Enable verbose output
        """

    def execute_configure(
        self,
        command: List[str],
        working_dir: Path
    ) -> ConfigureResult:
        """
        Execute CMake configuration step.

        Args:
            command: Complete cmake command as list
            working_dir: Working directory for execution

        Returns:
            ConfigureResult with timing, output, and status
        """

    def execute_build(
        self,
        command: List[str],
        working_dir: Path
    ) -> BuildResult:
        """
        Execute CMake build step.

        Args:
            command: Complete cmake --build command as list
            working_dir: Working directory for execution

        Returns:
            BuildResult with timing, output, and status
        """

    def _stream_output(
        self,
        process: subprocess.Popen,
        capture_output: bool = True
    ) -> Tuple[str, str]:
        """
        Stream process output to console and capture it.

        Args:
            process: Running subprocess
            capture_output: Whether to capture output

        Returns:
            Tuple of (stdout, stderr)
        """

    def check_cmake_available(self) -> bool:
        """
        Check if CMake is available in PATH.

        Returns:
            True if cmake command is found
        """

    def get_cmake_version(self) -> Optional[str]:
        """
        Get CMake version.

        Returns:
            Version string (e.g., "3.28.1") or None if not available
        """
```

**Result Data Models**:
```python
@dataclass
class ConfigureResult:
    """Result of CMake configuration execution."""
    success: bool
    exit_code: int
    duration: float                 # Seconds with millisecond precision
    stdout: str
    stderr: str
    start_time: datetime
    end_time: datetime
    cmake_version: Optional[str]
    generator: Optional[str]
    compiler_c: Optional[str]
    compiler_cxx: Optional[str]
    build_type: Optional[str]

@dataclass
class BuildResult:
    """Result of CMake build execution."""
    success: bool
    exit_code: int
    duration: float                 # Seconds with millisecond precision
    stdout: str
    stderr: str
    start_time: datetime
    end_time: datetime
    warnings_count: int
    errors_count: int
    targets_built: List[str]
```

---

### 4. BuildInspector

**File**: `forge/inspector/build_inspector.py`

**Responsibility**: Analyze and extract meaningful information from build output.

**Key Methods**:
```python
class BuildInspector:
    """Inspects and analyzes build output to extract metadata."""

    def __init__(self):
        """Initialize inspector with pattern matchers."""

    def inspect_configure_output(
        self,
        result: ConfigureResult
    ) -> ConfigureMetadata:
        """
        Extract metadata from configuration output.

        Args:
            result: Raw configuration result

        Returns:
            Structured metadata extracted from output
        """

    def inspect_build_output(
        self,
        result: BuildResult
    ) -> BuildMetadata:
        """
        Extract metadata from build output.

        Args:
            result: Raw build result

        Returns:
            Structured metadata extracted from output
        """

    def extract_warnings(self, output: str) -> List[Warning]:
        """
        Extract warning messages from build output.

        Args:
            output: Build output text

        Returns:
            List of structured warning objects
        """

    def extract_errors(self, output: str) -> List[Error]:
        """
        Extract error messages from build output.

        Args:
            output: Build output text

        Returns:
            List of structured error objects
        """

    def extract_targets(self, output: str) -> List[str]:
        """
        Extract built target names from output.

        Args:
            output: Build output text

        Returns:
            List of target names
        """

    def detect_project_name(self, source_dir: Path) -> Optional[str]:
        """
        Detect project name from CMakeLists.txt.

        Args:
            source_dir: Path to source directory

        Returns:
            Project name if found, None otherwise
        """
```

**Metadata Models**:
```python
@dataclass
class ConfigureMetadata:
    """Extracted metadata from CMake configuration."""
    project_name: Optional[str]
    cmake_version: str
    generator: str
    compiler_c: Optional[str]
    compiler_cxx: Optional[str]
    build_type: Optional[str]
    system_name: str
    system_processor: str
    found_packages: List[str]      # Packages found via find_package
    configuration_options: Dict[str, str]

@dataclass
class BuildMetadata:
    """Extracted metadata from CMake build."""
    project_name: str
    targets_built: List[str]
    warnings: List[Warning]
    errors: List[Error]
    total_files_compiled: int
    parallel_jobs: Optional[int]

@dataclass
class Warning:
    """Structured warning information."""
    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    warning_type: Optional[str]     # e.g., "unused-variable"

@dataclass
class Error:
    """Structured error information."""
    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    error_type: Optional[str]
```

---

### 5. DataPersistence

**File**: `forge/storage/persistence.py`

**Responsibility**: Save and retrieve data from SQLite database.

**Key Methods**:
```python
class DataPersistence:
    """Handles data persistence to SQLite database."""

    def __init__(self, database_path: Path):
        """
        Initialize database connection.

        Args:
            database_path: Path to SQLite database file
        """

    def initialize_database(self) -> None:
        """Create database tables if they don't exist."""

    def save_configuration(
        self,
        args: ForgeArguments,
        result: ConfigureResult,
        metadata: ConfigureMetadata
    ) -> int:
        """
        Save configuration data to database.

        Args:
            args: Command-line arguments used
            result: Raw configuration result
            metadata: Extracted configuration metadata

        Returns:
            Configuration record ID
        """

    def save_build(
        self,
        args: ForgeArguments,
        result: BuildResult,
        metadata: BuildMetadata,
        config_id: Optional[int] = None
    ) -> int:
        """
        Save build data to database.

        Args:
            args: Command-line arguments used
            result: Raw build result
            metadata: Extracted build metadata
            config_id: Associated configuration ID (if any)

        Returns:
            Build record ID
        """

    def save_warnings(
        self,
        build_id: int,
        warnings: List[Warning]
    ) -> None:
        """
        Save warning records associated with a build.

        Args:
            build_id: Build record ID
            warnings: List of warnings to save
        """

    def save_errors(
        self,
        build_id: int,
        errors: List[Error]
    ) -> None:
        """
        Save error records associated with a build.

        Args:
            build_id: Build record ID
            errors: List of errors to save
        """

    def get_recent_builds(
        self,
        project_name: str,
        limit: int = 10
    ) -> List[BuildRecord]:
        """
        Retrieve recent builds for a project.

        Args:
            project_name: Name of the project
            limit: Maximum number of records to return

        Returns:
            List of build records
        """

    def get_build_statistics(
        self,
        project_name: str
    ) -> BuildStatistics:
        """
        Get aggregate statistics for a project.

        Args:
            project_name: Name of the project

        Returns:
            Statistics object with aggregated data
        """

    def close(self) -> None:
        """Close database connection."""
```

---

## Database Schema

### Configuration Table

```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,              -- ISO 8601 format
    project_name TEXT,
    source_dir TEXT NOT NULL,
    build_dir TEXT NOT NULL,
    cmake_version TEXT,
    generator TEXT,
    compiler_c TEXT,
    compiler_cxx TEXT,
    build_type TEXT,
    system_name TEXT,
    system_processor TEXT,
    cmake_args TEXT,                      -- JSON array
    environment_vars TEXT,                -- JSON object
    duration REAL NOT NULL,               -- Seconds
    exit_code INTEGER NOT NULL,
    success INTEGER NOT NULL,             -- Boolean (0/1)
    stdout TEXT,
    stderr TEXT,
    configuration_options TEXT,           -- JSON object
    found_packages TEXT,                  -- JSON array
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configurations_project ON configurations(project_name);
CREATE INDEX idx_configurations_timestamp ON configurations(timestamp);
CREATE INDEX idx_configurations_success ON configurations(success);
```

### Build Table

```sql
CREATE TABLE builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER,             -- Foreign key to configurations
    timestamp TEXT NOT NULL,              -- ISO 8601 format
    project_name TEXT NOT NULL,
    build_dir TEXT NOT NULL,
    build_args TEXT,                      -- JSON array
    duration REAL NOT NULL,               -- Seconds
    exit_code INTEGER NOT NULL,
    success INTEGER NOT NULL,             -- Boolean (0/1)
    stdout TEXT,
    stderr TEXT,
    warnings_count INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    targets_built TEXT,                   -- JSON array
    total_files_compiled INTEGER,
    parallel_jobs INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES configurations(id)
);

CREATE INDEX idx_builds_project ON builds(project_name);
CREATE INDEX idx_builds_timestamp ON builds(timestamp);
CREATE INDEX idx_builds_success ON builds(success);
CREATE INDEX idx_builds_config ON builds(configuration_id);
```

### Warnings Table

```sql
CREATE TABLE warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    file TEXT,
    line INTEGER,
    column INTEGER,
    message TEXT NOT NULL,
    warning_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX idx_warnings_build ON warnings(build_id);
CREATE INDEX idx_warnings_file ON warnings(file);
CREATE INDEX idx_warnings_type ON warnings(warning_type);
```

### Errors Table

```sql
CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    file TEXT,
    line INTEGER,
    column INTEGER,
    message TEXT NOT NULL,
    error_type TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX idx_errors_build ON errors(build_id);
CREATE INDEX idx_errors_file ON errors(file);
CREATE INDEX idx_errors_type ON errors(error_type);
```

### Build Targets Table

```sql
CREATE TABLE build_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    build_id INTEGER NOT NULL,
    target_name TEXT NOT NULL,
    target_type TEXT,                     -- EXECUTABLE, LIBRARY, etc.
    build_order INTEGER,                  -- Order in which it was built
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (build_id) REFERENCES builds(id) ON DELETE CASCADE
);

CREATE INDEX idx_targets_build ON build_targets(build_id);
CREATE INDEX idx_targets_name ON build_targets(target_name);
```

---

## Data Query API (Future Implementation)

### Query Interface

**File**: `forge/storage/query.py`

```python
class ForgeQuery:
    """High-level query interface for forge data."""

    def __init__(self, database_path: Path):
        """Initialize query interface."""

    def get_builds_by_project(
        self,
        project_name: str,
        success_only: bool = False,
        limit: int = 100
    ) -> List[BuildRecord]:
        """Get builds filtered by project name."""

    def get_builds_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        project_name: Optional[str] = None
    ) -> List[BuildRecord]:
        """Get builds within a date range."""

    def get_build_trends(
        self,
        project_name: str,
        days: int = 30
    ) -> BuildTrends:
        """Get build trend statistics over time."""

    def get_common_warnings(
        self,
        project_name: str,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get most common warnings with occurrence count."""

    def get_common_errors(
        self,
        project_name: str,
        limit: int = 10
    ) -> List[Tuple[str, int]]:
        """Get most common errors with occurrence count."""

    def get_build_duration_statistics(
        self,
        project_name: str
    ) -> DurationStatistics:
        """Get statistics about build durations."""

    def search_builds_by_output(
        self,
        search_term: str,
        project_name: Optional[str] = None
    ) -> List[BuildRecord]:
        """Search builds by content in stdout/stderr."""
```

---

## Main Application Flow

### Forge Main Entry Point

**File**: `forge/__main__.py`

```python
def main() -> int:
    """
    Main entry point for forge application.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # 1. Parse arguments
        parser = ArgumentParser()
        args = parser.parse_args()

        # 2. Initialize components
        param_manager = CMakeParameterManager(args)
        executor = CMakeExecutor(verbose=args.verbose)
        inspector = BuildInspector()
        persistence = DataPersistence(
            args.database_path or get_default_db_path()
        )

        # 3. Initialize database
        persistence.initialize_database()

        # 4. Execute configuration (if source_dir provided)
        config_id = None
        if args.source_dir:
            config_cmd = param_manager.get_configure_command()
            config_result = executor.execute_configure(
                config_cmd,
                args.build_dir
            )

            if not config_result.success:
                print(f"Configuration failed with exit code {config_result.exit_code}")
                return config_result.exit_code

            config_metadata = inspector.inspect_configure_output(config_result)
            config_id = persistence.save_configuration(
                args,
                config_result,
                config_metadata
            )

        # 5. Execute build
        build_cmd = param_manager.get_build_command()
        build_result = executor.execute_build(
            build_cmd,
            args.build_dir
        )

        # 6. Inspect build output
        build_metadata = inspector.inspect_build_output(build_result)

        # 7. Save build data
        build_id = persistence.save_build(
            args,
            build_result,
            build_metadata,
            config_id
        )

        persistence.save_warnings(build_id, build_metadata.warnings)
        persistence.save_errors(build_id, build_metadata.errors)

        # 8. Print summary
        print_build_summary(build_result, build_metadata)

        # 9. Return exit code
        return build_result.exit_code

    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        return 130

    except Exception as e:
        print(f"Forge error: {e}")
        return 1

    finally:
        if 'persistence' in locals():
            persistence.close()


if __name__ == "__main__":
    sys.exit(main())
```

---

## Directory Structure

```
forge/
├── __init__.py
├── __main__.py                   # Main entry point
├── cli/
│   ├── __init__.py
│   └── argument_parser.py        # ArgumentParser class
├── cmake/
│   ├── __init__.py
│   ├── parameter_manager.py      # CMakeParameterManager class
│   └── executor.py               # CMakeExecutor class
├── inspector/
│   ├── __init__.py
│   └── build_inspector.py        # BuildInspector class
├── storage/
│   ├── __init__.py
│   ├── persistence.py            # DataPersistence class
│   ├── query.py                  # ForgeQuery class (future)
│   └── schema.sql                # Database schema
├── models/
│   ├── __init__.py
│   ├── arguments.py              # ForgeArguments dataclass
│   ├── results.py                # ConfigureResult, BuildResult
│   ├── metadata.py               # ConfigureMetadata, BuildMetadata
│   └── records.py                # Database record models
├── utils/
│   ├── __init__.py
│   ├── logging.py                # Logging configuration
│   ├── paths.py                  # Path utilities
│   └── formatting.py             # Output formatting
├── tests/
│   ├── __init__.py
│   ├── test_argument_parser.py
│   ├── test_parameter_manager.py
│   ├── test_executor.py
│   ├── test_inspector.py
│   ├── test_persistence.py
│   └── fixtures/                 # Test fixtures and sample data
├── requirements.txt
└── README.md
```

---

## Future Enhancements

### GUI Integration

The modular architecture supports future GUI integration:

```python
# Example GUI adapter
class ForgeGUI:
    """GUI wrapper for forge functionality."""

    def __init__(self):
        self.executor = CMakeExecutor()
        self.inspector = BuildInspector()
        self.persistence = DataPersistence(get_default_db_path())

    def run_configuration_async(
        self,
        params: CMakeParameters,
        progress_callback: Callable[[str], None]
    ) -> ConfigureResult:
        """Run configuration with progress updates to GUI."""

    def run_build_async(
        self,
        params: CMakeParameters,
        progress_callback: Callable[[str], None]
    ) -> BuildResult:
        """Run build with progress updates to GUI."""
```

### Plugin System

```python
class ForgePlugin:
    """Base class for forge plugins."""

    def on_configure_start(self, params: CMakeParameters) -> None:
        """Called before configuration starts."""

    def on_configure_complete(self, result: ConfigureResult) -> None:
        """Called after configuration completes."""

    def on_build_start(self, params: CMakeParameters) -> None:
        """Called before build starts."""

    def on_build_complete(self, result: BuildResult) -> None:
        """Called after build completes."""
```

---

## Testing Strategy

1. **Unit Tests**: Test each class independently with mocked dependencies
2. **Integration Tests**: Test complete workflow with real CMake projects
3. **Database Tests**: Test schema creation and data integrity
4. **Output Parsing Tests**: Test inspector with various compiler outputs
5. **Error Handling Tests**: Test error scenarios and edge cases

---

## Performance Considerations

1. **Output Buffering**: Use efficient buffering for real-time output streaming
2. **Database Indexing**: Proper indexes for common queries
3. **Lazy Loading**: Load full build output only when needed
4. **Connection Pooling**: Reuse database connections
5. **Async Operations**: Consider async I/O for future GUI integration

---

## Version History

- **v1.0** (2026-01-27): Initial architecture specification
