# Forge User Guide

**Version:** 1.0
**Last Updated:** January 2026

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Basic Usage](#basic-usage)
5. [Advanced Features](#advanced-features)
6. [Configuration](#configuration)
7. [Working with Build Data](#working-with-build-data)
8. [Integration Workflows](#integration-workflows)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Introduction

> **Important:** Throughout this guide, commands are shown using `python -m forge`. This works in two ways:
>
> - **Running from source**: Navigate to the `argos` directory (parent of `forge/`) and run `python -m forge`
> - **After installation**: Install with `pip install -e .` from the `forge/` directory, then use `forge` from anywhere

### What is Forge?

Forge is a non-intrusive CMake build wrapper that captures comprehensive build metadata without requiring any modifications to your CMake projects. It's designed for developers, build engineers, and CI/CD systems who need detailed insights into their build process.

### Key Features

- **Zero Configuration**: Works with any CMake project without modifications
- **Comprehensive Metadata**: Captures build times, warnings, errors, targets, and compiler information
- **Database Storage**: Stores all build data in SQLite for historical analysis
- **Real-time Output**: Streams build output to console while capturing data
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **CI/CD Ready**: Easy integration with continuous integration systems

### When to Use Forge

Use Forge when you need to:
- Track build performance over time
- Monitor warnings and errors across builds
- Analyze build metadata for optimization
- Integrate build data into dashboards or reporting systems
- Debug build issues with detailed logging
- Compare build configurations and their impact

---

## Installation

### Prerequisites

- **Python 3.8+** (Python 3.11+ recommended)
- **CMake 3.15+** installed and available in PATH
- **Git** (optional, for development)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/lmvcruz/argos.git
cd argos/forge

# Install dependencies
pip install -r requirements.txt

# Option 1: Install in development mode (recommended - enables 'forge' command)
pip install -e .

# Option 2: Run without installation (use 'python -m forge' from argos directory)
cd ..  # Go to argos directory
python -m forge --version
```

### Verify Installation

```bash
# Check that forge is available
python -m forge --version

# Verify CMake is detected
python -m forge --help
```

Expected output:
```
Forge - CMake Build Wrapper
Version: 1.0.0
```

---

## Quick Start

### Your First Build

Let's build a simple CMake project with Forge:

```bash
# Navigate to your CMake project
cd /path/to/your/cmake/project

# Configure and build in one command
python -m forge --source . --build ./build --configure --build-cmd
```

That's it! Forge will:
1. Configure your project with CMake
2. Build it
3. Capture all output and metadata
4. Store everything in a database

### View Build Results

After the build completes, Forge displays a summary:

```
╔════════════════════════════════════════════════════════════════╗
║                      BUILD SUMMARY                              ║
╠════════════════════════════════════════════════════════════════╣
║ Project:     MyProject                                          ║
║ Status:      ✓ SUCCESS                                          ║
║ Duration:    23.5s                                              ║
║ Targets:     3 built                                            ║
║ Warnings:    2                                                  ║
║ Errors:      0                                                  ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Basic Usage

### Command Structure

```bash
forge [options] --source <path> --build <path> [--configure] [--build-cmd]
```

### Essential Options

#### Source and Build Directories

```bash
# Specify source directory (where CMakeLists.txt is)
python -m forge --source /path/to/source --build /path/to/build --configure

# Use current directory as source
python -m forge --source . --build ./build --configure
```

#### Configure Only

Run CMake configuration without building:

```bash
python -m forge --source . --build ./build --configure
```

#### Build Only

Build an already-configured project:

```bash
python -m forge --source . --build ./build --build-cmd
```

#### Configure and Build

Do both in sequence:

```bash
python -m forge --source . --build ./build --configure --build-cmd
```

### CMake Options

#### Build Type

```bash
# Debug build (default)
python -m forge --source . --build ./build --configure --build-type Debug

# Release build
python -m forge --source . --build ./build --configure --build-type Release

# Other build types
python -m forge --source . --build ./build --configure --build-type RelWithDebInfo
python -m forge --source . --build ./build --configure --build-type MinSizeRel
```

#### Generator Selection

```bash
# Use Ninja generator
python -m forge --source . --build ./build --configure --generator Ninja

# Use Unix Makefiles
python -m forge --source . --build ./build --configure --generator "Unix Makefiles"

# Use Visual Studio 2019
python -m forge --source . --build ./build --configure --generator "Visual Studio 16 2019"
```

#### CMake Variables

```bash
# Set single variable
python -m forge --source . --build ./build --configure -D BUILD_SHARED_LIBS=ON

# Set multiple variables
python -m forge --source . --build ./build --configure \
  -D BUILD_SHARED_LIBS=ON \
  -D BUILD_TESTING=OFF \
  -D CMAKE_INSTALL_PREFIX=/usr/local
```

### Build Options

#### Parallel Builds

```bash
# Use all available cores
python -m forge --source . --build ./build --build-cmd -j

# Use specific number of cores
python -m forge --source . --build ./build --build-cmd -j 4
```

#### Build Specific Target

```bash
# Build specific target
python -m forge --source . --build ./build --build-cmd --target myapp

# Build multiple targets
python -m forge --source . --build ./build --build-cmd --target myapp --target mylib
```

#### Verbose Output

```bash
# Enable verbose output
python -m forge --source . --build ./build --build-cmd --verbose
```

---

## Advanced Features

### Database Management

#### Custom Database Location

```bash
# Specify custom database path
python -m forge --source . --build ./build --configure --build-cmd \
  --db-path ./my-builds.db
```

#### Database Location

By default, Forge stores build data in:
- **Linux/macOS**: `~/.forge/builds.db`
- **Windows**: `%USERPROFILE%\.forge\builds.db`

### Output Control

#### Disable Color Output

```bash
# Disable colored output (useful for CI logs)
python -m forge --source . --build ./build --configure --no-color
```

#### Quiet Mode

```bash
# Reduce output verbosity
python -m forge --source . --build ./build --configure --quiet
```

### Environment Variables

Forge respects these environment variables:

```bash
# Specify CMake executable
export CMAKE_EXECUTABLE=/usr/local/bin/cmake
python -m forge --source . --build ./build --configure

# Set default build type
export CMAKE_BUILD_TYPE=Release
python -m forge --source . --build ./build --configure
```

### Working with Multiple Configurations

```bash
# Build Debug configuration
python -m forge --source . --build ./build-debug --configure --build-cmd \
  --build-type Debug

# Build Release configuration
python -m forge --source . --build ./build-release --configure --build-cmd \
  --build-type Release

# Compare results using Python API (see below)
```

---

## Configuration

### Configuration Files

Forge supports configuration files to avoid repetitive command-line arguments.

#### forge.yaml

Create a `forge.yaml` in your project root:

```yaml
# forge.yaml
source: .
build: ./build
build_type: Release
generator: Ninja
cmake_args:
  - BUILD_SHARED_LIBS=ON
  - BUILD_TESTING=OFF
parallel_jobs: 4
```

Then run simply:

```bash
python -m forge --configure --build-cmd
```

#### Environment-Specific Configs

```yaml
# forge.yaml
profiles:
  debug:
    build_type: Debug
    build: ./build-debug
    cmake_args:
      - ENABLE_DEBUG_LOGGING=ON

  release:
    build_type: Release
    build: ./build-release
    cmake_args:
      - ENABLE_OPTIMIZATIONS=ON
```

Use with:

```bash
python -m forge --profile debug --configure --build-cmd
python -m forge --profile release --configure --build-cmd
```

---

## Working with Build Data

### Python API

Access build data programmatically:

```python
from forge.storage.data_persistence import DataPersistence
from pathlib import Path

# Open database
db = DataPersistence()
db.initialize_database()

# Get recent builds
recent_builds = db.get_recent_builds(limit=10)
for build in recent_builds:
    print(f"Project: {build['project_name']}")
    print(f"Status: {build['success']}")
    print(f"Duration: {build['duration']}s")
    print(f"Warnings: {build['warning_count']}")
    print()

# Get build statistics
stats = db.get_build_statistics()
print(f"Total builds: {stats['total_builds']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
print(f"Avg duration: {stats['avg_duration']:.1f}s")
```

### Querying Build History

```python
# Find builds by project name
builds = db.get_builds_by_project("MyProject")

# Get builds within date range
from datetime import datetime, timedelta
since = datetime.now() - timedelta(days=7)
recent = db.get_builds_since(since)

# Find failed builds
failed_builds = db.get_failed_builds()
for build in failed_builds:
    print(f"Build {build['id']} failed: {build['error_count']} errors")
```

### Analyzing Warnings

```python
# Get all warnings for a build
warnings = db.get_warnings(build_id=123)
for warning in warnings:
    print(f"{warning['file']}:{warning['line']}: {warning['message']}")

# Find most common warnings
warning_stats = db.get_warning_statistics()
for warning_type, count in warning_stats.items():
    print(f"{warning_type}: {count} occurrences")
```

### Exporting Data

```python
# Export to JSON
import json
builds = db.get_recent_builds(limit=100)
with open('builds.json', 'w') as f:
    json.dump(builds, f, indent=2)

# Export to CSV
import csv
with open('builds.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['project', 'status', 'duration'])
    writer.writeheader()
    for build in builds:
        writer.writerow({
            'project': build['project_name'],
            'status': 'success' if build['success'] else 'failed',
            'duration': build['duration']
        })
```

---

## Integration Workflows

### Continuous Integration

#### GitHub Actions

```yaml
# .github/workflows/build.yml
name: Build with Forge

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Forge
        run: |
          pip install -r requirements.txt
          pip install -e .
        working-directory: ./forge

      - name: Build with Forge
        run: |
          python -m forge --source . --build ./build \
            --configure --build-cmd \
            --build-type Release \
            -j

      - name: Upload build database
        uses: actions/upload-artifact@v3
        with:
          name: build-data
          path: ~/.forge/builds.db
```

#### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh '''
                    cd forge
                    pip install -r requirements.txt
                    pip install -e .
                '''

                sh '''
                    python -m forge --source . --build ./build \
                        --configure --build-cmd \
                        --build-type Release \
                        -j ${BUILD_NUMBER}
                '''
            }
        }

        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: '**/.forge/builds.db'
            }
        }
    }
}
```

#### GitLab CI

```yaml
# .gitlab-ci.yml
build:
  image: python:3.11
  script:
    - cd forge
    - pip install -r requirements.txt
    - pip install -e .
    - python -m forge --source . --build ./build --configure --build-cmd -j
  artifacts:
    paths:
      - ~/.forge/builds.db
    expire_in: 1 week
```

### Pre-commit Hook

Validate builds before committing:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running build validation with Forge..."
python -m forge --source . --build ./build --configure --build-cmd --quiet

if [ $? -ne 0 ]; then
    echo "Build failed! Commit aborted."
    exit 1
fi

echo "Build successful!"
exit 0
```

### Build Dashboard

Create a simple dashboard using the Python API:

```python
# dashboard.py
from forge.storage.data_persistence import DataPersistence
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

db = DataPersistence()
db.initialize_database()

# Get last 30 days of builds
since = datetime.now() - timedelta(days=30)
builds = db.get_builds_since(since)

# Plot build duration over time
dates = [b['timestamp'] for b in builds]
durations = [b['duration'] for b in builds]

plt.figure(figsize=(12, 6))
plt.plot(dates, durations, marker='o')
plt.xlabel('Date')
plt.ylabel('Duration (seconds)')
plt.title('Build Duration Over Time')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('build_duration.png')

# Plot success rate
success_count = sum(1 for b in builds if b['success'])
fail_count = len(builds) - success_count

plt.figure(figsize=(8, 8))
plt.pie([success_count, fail_count],
        labels=['Success', 'Failed'],
        autopct='%1.1f%%',
        colors=['green', 'red'])
plt.title('Build Success Rate (Last 30 Days)')
plt.savefig('success_rate.png')

print(f"Dashboard generated: build_duration.png, success_rate.png")
```

---

## Best Practices

### 1. Use Separate Build Directories

Always use out-of-source builds:

```bash
# Good: separate build directory
python -m forge --source . --build ./build --configure --build-cmd

# Avoid: in-source builds
python -m forge --source . --build . --configure --build-cmd
```

### 2. Configure Once, Build Many Times

After initial configuration, you can build repeatedly without reconfiguring:

```bash
# Initial setup
python -m forge --source . --build ./build --configure

# Subsequent builds (faster)
python -m forge --source . --build ./build --build-cmd
python -m forge --source . --build ./build --build-cmd
```

### 3. Use Build Type Appropriately

Choose the right build type for your needs:

```bash
# Development: faster builds, easier debugging
python -m forge --build-type Debug

# Testing: some optimizations, debug info
python -m forge --build-type RelWithDebInfo

# Production: maximum performance
python -m forge --build-type Release

# Embedded/size-constrained: minimize binary size
python -m forge --build-type MinSizeRel
```

### 4. Leverage Parallel Builds

Always use parallel builds when possible:

```bash
# Use all cores
python -m forge --build-cmd -j

# Conservative: leave cores for other work
python -m forge --build-cmd -j $(($(nproc) - 2))
```

### 5. Monitor Build Metrics

Regularly check build statistics:

```python
from forge.storage.data_persistence import DataPersistence

db = DataPersistence()
db.initialize_database()

# Weekly build health check
stats = db.get_build_statistics()
if stats['success_rate'] < 90:
    print("⚠️  Build success rate below 90%")
if stats['avg_duration'] > 300:
    print("⚠️  Average build time exceeds 5 minutes")
```

### 6. Clean Build Directory Periodically

```bash
# Remove build directory
rm -rf ./build

# Reconfigure from scratch
python -m forge --source . --build ./build --configure --build-cmd
```

### 7. Version Control Integration

Add to `.gitignore`:

```gitignore
# Build directories
build/
build-*/
*.db

# Forge local data
.forge/
```

### 8. Document Build Requirements

Create a `BUILD.md` in your project:

```markdown
# Build Instructions

## Prerequisites
- CMake 3.20+
- C++17 compiler
- Ninja (recommended)

## Building with Forge

```bash
python -m forge --source . --build ./build \
  --configure --build-cmd \
  --generator Ninja \
  --build-type Release \
  -j
```

## Build Options

- `BUILD_TESTS`: Enable test compilation (default: OFF)
- `BUILD_DOCS`: Enable documentation (default: OFF)
```
```

---

## FAQ

### General Questions

**Q: Do I need to modify my CMakeLists.txt to use Forge?**
A: No! Forge is completely non-intrusive. It wraps CMake without requiring any project modifications.

**Q: Can I use Forge with existing CMake projects?**
A: Yes! Forge works with any standard CMake project (3.15+).

**Q: Does Forge affect build performance?**
A: Overhead is minimal (< 5%). The actual build runs at native speed.

**Q: Where is build data stored?**
A: By default in `~/.forge/builds.db` (SQLite database). You can specify a custom location with `--db-path`.

**Q: Can I use Forge in CI/CD?**
A: Absolutely! Forge is designed for CI/CD integration. See [Integration Workflows](#integration-workflows).

### Troubleshooting

**Q: Forge says "CMake not found"**
A: Ensure CMake is installed and available in your PATH:
```bash
# Check CMake availability
cmake --version

# Add CMake to PATH (if needed)
export PATH="/path/to/cmake/bin:$PATH"
```

**Q: Build fails but works with plain CMake**
A: This shouldn't happen! Please report an issue with:
```bash
# Run with verbose output
python -m forge --source . --build ./build --configure --build-cmd --verbose

# Compare with plain CMake
cmake -B ./build -S .
cmake --build ./build
```

**Q: How do I delete old build data?**
A: You can delete the database file:
```bash
# Linux/macOS
rm ~/.forge/builds.db

# Windows
del %USERPROFILE%\.forge\builds.db
```

**Q: Can I use Forge with custom CMake toolchain files?**
A: Yes! Pass toolchain files as CMake variables:
```bash
python -m forge --source . --build ./build --configure \
  -D CMAKE_TOOLCHAIN_FILE=/path/to/toolchain.cmake
```

**Q: Forge hangs during build**
A: This might be a build timeout issue. Check:
1. Is the build actually stuck? (check CPU/disk activity)
2. Is it a long-running build? (Forge waits for completion)
3. Try building the same target directly with CMake to isolate the issue

**Q: How do I export build data?**
A: Use the Python API to export in various formats:
```python
from forge.storage.data_persistence import DataPersistence
import json

db = DataPersistence()
db.initialize_database()
builds = db.get_recent_builds()

with open('builds.json', 'w') as f:
    json.dump(builds, f, indent=2)
```

### Advanced Usage

**Q: Can I query the database directly?**
A: Yes! It's a standard SQLite database:
```bash
sqlite3 ~/.forge/builds.db
sqlite> SELECT project_name, success, duration FROM builds LIMIT 10;
```

**Q: How do I migrate build data between systems?**
A: Simply copy the database file:
```bash
# Backup on machine A
cp ~/.forge/builds.db ~/builds-backup.db

# Restore on machine B
cp ~/builds-backup.db ~/.forge/builds.db
```

**Q: Can I customize output formatting?**
A: Currently, output formatting is built-in. Custom formatters are planned for a future release.

**Q: Does Forge support incremental builds?**
A: Yes! Forge respects CMake's incremental build behavior. Only changed files are rebuilt.

**Q: Can I run multiple Forge instances simultaneously?**
A: Yes, as long as they use different build directories or databases. SQLite handles concurrent reads well, but writes are serialized.

---

## Getting Help

### Resources

- **Documentation**: [docs/](.)
- **API Reference**: [API.md](API.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **GitHub Issues**: [github.com/lmvcruz/argos/issues](https://github.com/lmvcruz/argos/issues)

### Reporting Issues

When reporting issues, include:

1. Forge version: `python -m forge --version`
2. CMake version: `cmake --version`
3. Operating system and version
4. Complete command that failed
5. Relevant error messages (use `--verbose`)

### Contributing

We welcome contributions! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

---

**Next Steps:**
- Try the [Tutorial](TUTORIAL.md) for hands-on examples
- Explore the [API Reference](API.md) for programmatic access
- Check out [Advanced Patterns](ADVANCED.md) for power user features
