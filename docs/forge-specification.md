# Forge - CMake Build Wrapper Specification

## Overview

**Forge** is Argus's complete CMake wrapper tool that captures both configuration and build events, output, and metadata without requiring any modifications to the monitored projects. It wraps the entire CMake workflow—from initial project configuration to final compilation—transparently recording all information to a local SQLite database.

Named to complement Argus (the all-seeing watcher), forge represents the creation process—configuring and building applications while Argus observes them.

## Design Principles

1. **Non-Intrusive**: Zero modifications required to CMakeLists.txt or build configurations
2. **Transparent**: Streams build output to console in real-time, behaving identically to `cmake --build`
3. **Simple**: Drop-in replacement for the standard build command
4. **Local-First**: Stores data locally in SQLite (v0.1), with optional server upload in later versions
5. **Reliable**: Captures complete build output regardless of success or failure

## Command-Line Interface

### Basic Usage

```bash
# Configure and build (typical usage)
python forge --source-dir <path> --build-dir <path>

# Build only (if already configured)
python forge --build-dir <path>
```

### Parameters

- `--source-dir <path>` (optional): Path to the source directory containing CMakeLists.txt. If provided, forge will run configuration step first.
- `--build-dir <path>` (required): Path to the CMake build directory (created if doesn't exist)
- `--cmake-args <args>` (optional): Additional arguments to pass to cmake during configuration (e.g., `-DCMAKE_BUILD_TYPE=Release`)
- `--build-args <args>` (optional): Additional arguments to pass to cmake --build (e.g., `-j8` for parallel builds)
- `--server <url>` (optional, v0.3+): Argus server URL for data upload
- `--project-name <name>` (optional): Override project name detection
- `--verbose` (optional): Enable detailed logging

### Examples

```bash
# Configure and build (most common usage)
python forge --source-dir . --build-dir ./build

# Configure with specific options and build
python forge --source-dir . --build-dir ./build --cmake-args "-DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=ON"

# Configure and build with parallel compilation
python forge --source-dir . --build-dir ./build --build-args "-j8"

# Build only (skip configure if already done)
python forge --build-dir ./build

# Full workflow with custom project name
python forge --source-dir . --build-dir ./build --project-name TerrainSimulation

# Configure, build, and upload to Argus server (v0.3+)
python forge --source-dir . --build-dir ./build --server http://localhost:8000
```

## Functionality

### Configure Execution (when `--source-dir` provided)

1. **Build Directory Creation**: Creates build directory if it doesn't exist
2. **Process Spawning**: Executes `cmake <source-dir> [cmake-args]` in the build directory
3. **Output Streaming**: Captures stdout/stderr and displays in real-time to the console
4. **Exit Code Checking**: If configuration fails, forge exits without attempting build
5. **Metadata Capture**: Records configuration time, options, detected compilers, and libraries

### Build Execution

1. **Process Spawning**: Executes `cmake --build <build-dir> [build-args]` as a subprocess
2. **Output Streaming**: Captures stdout/stderr and displays in real-time to the console
3. **Exit Code Propagation**: Returns the same exit code as the CMake build process

### Data Capture

#### Configuration Metadata (when configure step runs)

- **Timestamp**: Configuration start time with millisecond precision (ISO 8601 format)
- **Source Directory**: Absolute path to the source directory
- **Build Directory**: Absolute path to the build directory
- **CMake Arguments**: All configuration arguments passed to cmake
- **CMake Version**: Detected CMake version
- **Generator**: CMake generator used (e.g., "Unix Makefiles", "Ninja")
- **Compiler**: Detected C/C++ compiler (extracted from output)
- **Build Type**: CMAKE_BUILD_TYPE if specified
- **Duration**: Configuration time in seconds (floating point)
- **Exit Code**: CMake configure exit code (0 = success)
- **Success Status**: Boolean derived from exit code
- **Output**: Complete configure output

#### Build Metadata

- **Timestamp**: Build start time with millisecond precision (ISO 8601 format)
- **Build Directory**: Absolute path to the build directory
- **Project Name**: Extracted from CMakeLists.txt or provided via CLI
- **Build Arguments**: Arguments passed to cmake --build
- **Duration**: Build time in seconds (floating point)
- **Exit Code**: CMake build exit code (0 = success)
- **Success Status**: Boolean derived from exit code
- **Configuration ID**: Foreign key linking to the configuration record (if configure was run)

#### Output Recording

- **Complete Capture**: Full stdout and stderr streams merged in chronological order
- **Preserves Formatting**: ANSI color codes and terminal formatting retained
- **Compiler Messages**: All warnings, errors, and informational messages included

### Data Storage

#### SQLite Schema (v0.1)

**Database File**: `argus_builds.db` (created in user's home directory or `~/.argus/`)

**Table: configurations**

```sql
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,                  -- ISO 8601 format: 2026-01-27T14:23:45.123Z
    project_name TEXT NOT NULL,               -- e.g., "TerrainSimulation"
    source_dir TEXT NOT NULL,                 -- Absolute path to source
    build_dir TEXT NOT NULL,                  -- Absolute path to build
    cmake_version TEXT,                       -- e.g., "3.25.1"
    generator TEXT,                           -- e.g., "Unix Makefiles"
    cmake_args TEXT,                          -- Configuration arguments
    build_type TEXT,                          -- e.g., "Release", "Debug"
    compiler_c TEXT,                          -- Detected C compiler
    compiler_cxx TEXT,                        -- Detected C++ compiler
    duration_seconds REAL NOT NULL,           -- e.g., 2.345
    exit_code INTEGER NOT NULL,               -- 0 for success
    success BOOLEAN NOT NULL,                 -- 1 for success, 0 for failure
    output_text TEXT NOT NULL,                -- Complete configuration output
    hostname TEXT,                            -- Machine name
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configurations_timestamp ON configurations(timestamp);
CREATE INDEX idx_configurations_project ON configurations(project_name);
CREATE INDEX idx_configurations_success ON configurations(success);
```

**Table: builds**

```sql
CREATE TABLE builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    configuration_id INTEGER,                 -- Foreign key to configurations table (NULL if build-only)
    timestamp TEXT NOT NULL,                  -- ISO 8601 format: 2026-01-27T14:23:45.123Z
    project_name TEXT NOT NULL,               -- e.g., "TerrainSimulation"
    build_dir TEXT NOT NULL,                  -- Absolute path
    build_args TEXT,                          -- Build arguments (e.g., "-j8")
    duration_seconds REAL NOT NULL,           -- e.g., 45.678
    exit_code INTEGER NOT NULL,               -- 0 for success
    success BOOLEAN NOT NULL,                 -- 1 for success, 0 for failure
    output_text TEXT NOT NULL,                -- Complete build output
    hostname TEXT,                            -- Machine name
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES configurations(id)
);

CREATE INDEX idx_builds_timestamp ON builds(timestamp);
CREATE INDEX idx_builds_project ON builds(project_name);
CREATE INDEX idx_builds_success ON builds(success);
CREATE INDEX idx_builds_configuration ON builds(configuration_id);
```

#### Server Upload (v0.3+)

When `--server` is provided, forge will POST configuration and build data to the Argus server:

**Endpoint**: `POST /api/ingest`

**Configuration Event Payload**:
```json
{
    "event_type": "configure",
    "timestamp": "2026-01-27T14:23:40.000Z",
    "project_name": "TerrainSimulation",
    "source_dir": "/home/user/projects/terrain",
    "build_dir": "/home/user/projects/terrain/build",
    "cmake_version": "3.25.1",
    "generator": "Unix Makefiles",
    "cmake_args": "-DCMAKE_BUILD_TYPE=Release",
    "build_type": "Release",
    "compiler_c": "gcc",
    "compiler_cxx": "g++",
    "duration_seconds": 2.345,
    "exit_code": 0,
    "success": true,
    "output_text": "-- The C compiler identification is GNU 11.3.0...",
    "hostname": "dev-machine"
}
```

**Build Event Payload**:
```json
{
    "event_type": "build",
    "timestamp": "2026-01-27T14:23:45.123Z",
    "project_name": "TerrainSimulation",
    "build_dir": "/home/user/projects/terrain/build",
    "build_args": "-j8",
    "duration_seconds": 45.678,
    "exit_code": 0,
    "success": true,
    "output_text": "[ 10%] Building CXX object...",
    "hostname": "dev-machine",
    "configuration_id": 123
}
```

## Implementation Details

### Language and Dependencies

- **Language**: Python 3.8+
- **Core Libraries**:
  - `subprocess`: Process execution and output capture
  - `sqlite3`: Database operations (standard library)
  - `argparse`: Command-line argument parsing
  - `datetime`: Timestamp handling
  - `pathlib`: Path manipulation
  - `socket`: Hostname detection
- **Optional Dependencies** (v0.3+):
  - `requests` or `httpx`: HTTP client for server communication

### Project Name Detection

Priority order for determining project name:

1. `--project-name` CLI argument (if provided)
2. Parse `project()` command from `CMakeLists.txt` in source directory
3. Parse `project()` from `CMakeLists.txt` in build directory parent (for build-only mode)
4. Use source directory folder name as fallback
5. Default to "UnknownProject" if all else fails

### Configuration Information Extraction

Forge parses the configuration output to extract:

- **CMake Version**: From "cmake version X.Y.Z" line
- **Generator**: From "-- The build generator is: ..." or CMakeCache.txt
- **C Compiler**: From "-- The C compiler identification is..." line
- **C++ Compiler**: From "-- The CXX compiler identification is..." line
- **Build Type**: From CMAKE_BUILD_TYPE argument or CMakeCache.txt

### Error Handling

- **Source Directory Not Found**: Exit with error message, code 1
- **CMakeLists.txt Missing**: Exit with error message, code 1
- **CMake Not Available**: Exit with error message, code 2
- **Configuration Failure**: Save configuration record, display output, exit with configure exit code (do NOT attempt build)
- **Build Directory Not Found** (build-only mode): Exit with error message, code 1
- **Database Write Failure**: Log warning, continue execution, exit with CMake exit code
- **Server Upload Failure** (v0.3+): Log warning, store locally, exit with CMake exit code

### Output Format

#### Console Output (Configure + Build)

```
[Forge] Starting configuration: TerrainSimulation
[Forge] Source directory: /home/user/projects/terrain
[Forge] Build directory: /home/user/projects/terrain/build
[Forge] Timestamp: 2026-01-27 14:23:40

-- The C compiler identification is GNU 11.3.0
-- The CXX compiler identification is GNU 11.3.0
-- Detecting C compiler ABI info
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features
-- Detecting C compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to: /home/user/projects/terrain/build

[Forge] Configuration completed in 2.35 seconds
[Forge] Status: SUCCESS
[Forge] Starting build: TerrainSimulation
[Forge] Timestamp: 2026-01-27 14:23:45

[ 10%] Building CXX object CMakeFiles/terrain.dir/src/main.cpp.o
[ 20%] Building CXX object CMakeFiles/terrain.dir/src/terrain.cpp.o
...
[100%] Built target terrain

[Forge] Build completed in 45.68 seconds
[Forge] Status: SUCCESS
[Forge] Data saved to: ~/.argus/argus_builds.db
```

#### Verbose Mode

When `--verbose` is enabled:
```
[Forge] Verbose mode enabled
[Forge] Python version: 3.11.2
[Forge] CMake version: 3.25.1
[Forge] Database path: /home/user/.argus/argus_builds.db
[Forge] Detected project name: TerrainSimulation (from CMakeLists.txt)
...
```

## Usage Workflow

### Development Workflow Integration

```bash
# Standard CMake workflow (WITHOUT forge)
mkdir build
cd build
cmake ..
cmake --build .

# Complete replacement WITH forge (recommended)
python forge --source-dir . --build-dir ./build

# Subsequent builds (if no config changes)
python forge --build-dir ./build
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Build with Argus monitoring
  run: python forge --build-dir build --server ${{ secrets.ARGUS_SERVER }}
```

### Iterative Development

```bash
# Initial setup
python forge --source-dir . --build-dir ./build

# Developer makes code changes (no config changes)
vim src/main.cpp

# Rebuild only (skip configure)
python forge --build-dir ./build

# Developer modifies CMakeLists.txt
vim CMakeLists.txt

# Reconfigure and rebuild
python forge --source-dir . --build-dir ./build

# Query build and configuration history
sqlite3 ~/.argus/argus_builds.db "SELECT timestamp, duration_seconds, success FROM builds ORDER BY timestamp DESC LIMIT 10;"
sqlite3 ~/.argus/argus_builds.db "SELECT timestamp, cmake_args, compiler_cxx, success FROM configurations ORDER BY timestamp DESC LIMIT 10;"
```

## Future Enhancements (v0.2+)

### Planned Features

- **Build Cache Detection**: Detect and report full vs. incremental builds
- **Parallel Build Tracking**: Capture and report parallelization level (`-j` flag)
- **Compiler Detection**: Identify and record compiler type and version
- **Warning/Error Parsing**: Extract and categorize warnings and errors
- **Build Statistics**: Track files compiled, link time vs. compile time
- **Build Comparison**: Compare current build with historical builds
- **Configuration Tracking**: Record CMake configuration changes

### Potential Options

```bash
# Parse and categorize warnings/errors
python forge --build-dir build --parse-output

# Compare with previous build
python forge --build-dir build --compare-previous

# Track incremental vs full build
python forge --build-dir build --track-cache
```

## Compatibility

### Supported Build Systems

- **Primary**: CMake 3.10+
- **Future**: Potential adapters for Make, Ninja, MSBuild

### Supported Platforms

- Linux (Ubuntu 20.04+, Fedora 35+, Arch)
- macOS (11.0+)
- Windows (10/11 with Python 3.8+)

### CMake Generators

Compatible with all CMake generators:
- Unix Makefiles
- Ninja
- Visual Studio
- Xcode

## Testing Strategy

### Unit Tests

- Argument parsing validation
- Project name detection logic
- Database schema creation
- Timestamp formatting

### Integration Tests

- Build a minimal CMake project successfully
- Build a project that fails (deliberate error)
- Capture output with ANSI color codes
- Verify database record accuracy
- Test with various CMake generators

### End-to-End Tests

- Build Terrain Simulation and verify database record
- Simulate server upload (v0.3+)
- Test on all supported platforms

## Performance Considerations

### Overhead

- **Expected Overhead**: < 100ms for typical builds
- **Measurement**: Total runtime vs. direct `cmake --build` execution
- **Target**: < 1% overhead for builds longer than 10 seconds

### Scalability

- **Large Builds**: Tested with builds producing > 100MB of output
- **Database Size**: No automatic cleanup in v0.1 (manual management)
- **Memory Usage**: Streaming output capture to minimize memory footprint

## Security Considerations

- **Output Sanitization**: None in v0.1 (outputs stored as-is)
- **Path Validation**: Prevent directory traversal attacks
- **Server Communication** (v0.3+): HTTPS recommended, API key authentication
- **Database Permissions**: Created with user-only read/write permissions

## Success Criteria (from Project Plan)

1. ✅ Running `python forge --source-dir . --build-dir ./build` successfully executes CMake configure and build commands
2. ✅ Configuration and build output display in real-time in the terminal
3. ✅ Complete stdout/stderr captured with millisecond-precision timestamps for both steps
4. ✅ SQLite database contains configuration records queryable with `SELECT * FROM configurations;`
5. ✅ SQLite database contains build records queryable with `SELECT * FROM builds;`
6. ✅ Build records link to their configuration via configuration_id foreign key
7. ✅ All configuration and build history stored locally for later analysis
8. ✅ Running `python forge --build-dir ./build` (without --source-dir) performs build-only operation

---

**Version**: 0.1.0 (Specification)
**Status**: Design Phase
**Last Updated**: 2026-01-27
