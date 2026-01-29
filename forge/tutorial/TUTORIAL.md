# Forge Tutorial: Step-by-Step Guide

This tutorial walks you through using Forge with real examples, from basic builds to advanced workflows.

> **Important Working Directory:** All commands in this tutorial should be executed from the `argos/forge/tutorial` directory.
>
> **PowerShell Focus:** This tutorial uses PowerShell syntax. All commands are designed to run in PowerShell on Windows (also compatible with PowerShell Core on Linux/macOS).
>
> **Running Forge:** We use `..\..\..\python -m forge` to run Forge from the source code (relative to the tutorial directory). The `..\..\..` navigates up to the `argos` parent directory where the forge module is located.

## Table of Contents

1. [Tutorial Setup](#tutorial-setup)
2. [Tutorial 1: Your First Build](#tutorial-1-your-first-build)
3. [Tutorial 2: Working with Build Types](#tutorial-2-working-with-build-types)
4. [Tutorial 3: Analyzing Build Data](#tutorial-3-analyzing-build-data)
5. [Tutorial 4: Tracking Build Performance](#tutorial-4-tracking-build-performance)
6. [Tutorial 5: CI/CD Integration](#tutorial-5-cicd-integration)
7. [Next Steps](#next-steps)

---

## Tutorial Setup

### Prerequisites Check

Before starting, make sure you're in the correct directory and verify your environment:

```powershell
# Navigate to the tutorial directory (if not already there)
cd argos/forge/tutorial

# Check Python version (need 3.8+)
python --version
# Expected: Python 3.8.x or higher

# Check CMake version (need 3.15+)
cmake --version
# Expected: cmake version 3.15.x or higher

# Check Forge (run from argos parent directory)
cd ..\..\..
python -m forge --version
cd forge\tutorial
# Expected: forge 0.1.0
```

### Sample Project

We'll create a simple C++ project in this tutorial directory:

```powershell
# Ensure you're in argos/forge/tutorial directory
# All tutorial files will be created here

# Create project structure
New-Item -ItemType Directory -Path "sample-project" -Force
Set-Location sample-project

# Create source files directory
New-Item -ItemType Directory -Path "src" -Force
```

Create `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.15)
project(HelloForge VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Main executable
add_executable(hello src/main.cpp)

# Library
add_library(greeter src/greeter.cpp)
target_include_directories(greeter PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)

# Link library to executable
target_link_libraries(hello PRIVATE greeter)
```

Create `src/greeter.h`:

```cpp
#pragma once
#include <string>

class Greeter {
public:
    std::string greet(const std::string& name);
};
```

Create `src/greeter.cpp`:

```cpp
#include "greeter.h"

std::string Greeter::greet(const std::string& name) {
    return "Hello, " + name + "!";
}
```

Create `src/main.cpp`:

```cpp
#include <iostream>
#include "greeter.h"

int main() {
    Greeter greeter;
    std::cout << greeter.greet("Forge") << std::endl;
    return 0;
}
```

Verify the project structure:

```powershell
# View directory structure
Get-ChildItem -Recurse | Select-Object FullName

# Expected output:
# sample-project\
# ├── CMakeLists.txt
# └── src\
#     ├── greeter.cpp
#     ├── greeter.h
#     └── main.cpp
```

---

## Tutorial 1: Your First Build

### Step 1: Basic Configuration and Build

Let's build our project with Forge (remember: we're in `forge/tutorial/sample-project`):

```powershell
# First, create the build directory
New-Item -ItemType Directory -Path build -Force

# Configure and build using Forge
# Note: We use ..\..\.. to reach the argos directory where forge module is
cd ..\..\..
python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build --verbose
cd forge\tutorial\sample-project
```

**What happened?**

1. Forge ran CMake to configure the project
2. CMake generated build files in `./build`
3. Forge compiled the source files
4. All output and metadata were captured
5. Results were stored in the database

### Step 2: Examine the Output

You should see output like this:

```
[FORGE] Starting CMake configuration...
[CMAKE] -- The C compiler identification is GNU 11.4.0
[CMAKE] -- The CXX compiler identification is GNU 11.4.0
[CMAKE] -- Configuring done
[CMAKE] -- Generating done
[CMAKE] -- Build files written to: /home/user/forge-tutorial/build

[FORGE] Configuration completed in 2.3s

[FORGE] Starting build...
[BUILD] [1/4] Building CXX object CMakeFiles/greeter.dir/src/greeter.cpp.o
[BUILD] [2/4] Linking CXX static library libgreeter.a
[BUILD] [3/4] Building CXX object CMakeFiles/hello.dir/src/main.cpp.o
[BUILD] [4/4] Linking CXX executable hello

[FORGE] Build completed in 5.1s

╔════════════════════════════════════════════════════════════════╗
║                        BUILD SUMMARY                            ║
╠════════════════════════════════════════════════════════════════╣
║ Project:     HelloForge                                         ║
║ Status:      ✓ SUCCESS                                          ║
║ Duration:    7.4s                                               ║
║ Targets:     2 (hello, libgreeter.a)                           ║
║ Warnings:    0                                                  ║
║ Errors:      0                                                  ║
╚════════════════════════════════════════════════════════════════╝
```

### Step 3: Run Your Program

```powershell
# Run the compiled program (Windows with MSVC)
cd build\Debug
.\hello.exe
# Expected output: Hello, Forge!

# Return to project directory
cd ..\..

# Note: On Linux/macOS or with MinGW, the executable is in ./build/hello
```

### Step 4: Build Again (Incremental)

Make a small change to `src/main.cpp`:

```cpp
// Change the main function
int main() {
    Greeter greeter;
    std::cout << greeter.greet("World") << std::endl;  // Changed "Forge" to "World"
    return 0;
}
```

Now rebuild (without reconfiguring):

```powershell
cd ..\..\..
python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build --no-configure
cd forge\tutorial\sample-project
```

**Notice:** Only the changed file and affected targets are rebuilt:

```
[FORGE] Starting build...
[BUILD] [1/2] Building CXX object CMakeFiles/hello.dir/src/main.cpp.o
[BUILD] [2/2] Linking CXX executable hello

[FORGE] Build completed in 1.2s
```

Much faster! Forge respects CMake's incremental build capabilities.

---

## Tutorial 2: Working with Build Types

### Debug Build (Default)

Debpowershell
cd ..\..\..
python -m forge --source forge\tutorial\sample-project --build forge\tutorial\sample-project\build-debug --configure --build-cmd --build-type Debug
cd forge\tutorial\sample-project
```

### Release Build

Release builds are optimized for performance:

```powershell
# Create release build directory  
New-Item -ItemType Directory -Path build-release -Force

# Note: To specify build type, you need to pass it as a CMake parameter
cd ..\..\..
python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build-release
cd forge\tutorial\sample-project

# With MSVC, use: cmake --build build-release --config Release
# Or configure with: -D CMAKE_BUILD_TYPE=Release for single-config generators
```

### Compare Build Outputs

Let's compare the binary sizes:

```powershell
# Debug build size
Get-Item .\build-debug\Debug\hello.exe | Select-Object Name, Length
# Expected: ~50KB+ (includes debug symbols)

# Release build size
Get-Item .\build-release\Release\hello.exe | Select-Object Name, Length
# Expected: ~15KB+ (optimized, may be
ls -lh ./build-release/hello
# Expected: ~15KB (optimized, stripped)
```

### Run Performance Comparison

Create a more computationally intensive function to see the difference.

Update `src/greeter.cpp`:

```cpp
#include "greeter.h"
#include <sstream>

std::string Greeter::greet(const std::string& name) {
    // Simulate some work
    std::stringstream ss;
    for (int i = 0; i < 10000; ++i) {
        ss << "Hello, " << name << "! ";
    }
    return ss.str();
}
```

Update `src/main.cpp`:

```cpp
#include <iostream>
#include <chrono>
#include "greeter.h"

int main() {
    Greeter greeter;

    auto start = std::chrono::high_resolution_clock::now();
    std::string result = greeter.greet("Forge");
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "Greeting took: " << duration.count() << "ms" << std::endl;

    return 0;
}
```

Rebuild both:

```powershell
# Rebuild Debug
cd ..\..\..
python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build-debug --no-configure
cd forge\tutorial\sample-project

# Rebuild Release
cd ..\..\..
python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build-release --no-configure
cd forge\tutorial\sample-project
```

Test performance:

```powershell
# Debug performance
cd build-debug\Debug
.\hello.exe
cd ..\..
# Expected: Greeting took: ~20-50ms

# Release performance
cd build-release\Release
.\hello.exe
cd ..\..
# Expected: Greeting took: ~5-10ms (much faster!)
```

---

## Tutorial 3: Analyzing Build Data

### Access Build History with Python

Create `analyze_builds.py` in the `tutorial` directory:

```python
#!/usr/bin/env python3
"""
Analyze Forge build data.
"""
import sys
from pathlib import Path

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from forge.storage.data_persistence import DataPersistence
from datetime import datetime

# Connect to database
db = DataPersistence()
db.initialize_database()

# Get recent builds
print("=== Recent Builds ===\n")
builds = db.get_recent_builds(limit=5)

for build in builds:
    timestamp = datetime.fromisoformat(build['timestamp'])
    status = "✓ SUCCESS" if build['success'] else "✗ FAILED"

    print(f"Build #{build['id']}")
    print(f"  Project:  {build['project_name']}")
    print(f"  Time:     {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Status:   {status}")
    print(f"  Duration: {build['duration']:.1f}s")
    print(f"  Warnings: {build['warning_count']}")
    print(f"  Errors:   {build['error_count']}")
    print()

# Get statistics
print("=== Build Statistics ===\n")
stats = db.get_build_statistics()

print(f"Total builds:     {stats['total_builds']}")
print(f"Successful:       {stats['successful_builds']}")
print(f"Failed:           {stats['failed_builds']}")
print(f"Success rate:     {stats['success_rate']:.1f}%")
print(f"Average duration: {stats['avg_duration']:.1f}s")
```

Run the analysis:

```powershell
# From the tutorial directory
python analyze_builds.py
```

Expected output:

```
=== Recent Builds ===

Build #3
  Project:  HelloForge
  Time:     2026-01-29 14:30:15
  Status:   ✓ SUCCESS
  Duration: 1.2s
  Warnings: 0
  Errors:   0

Build #2
  Project:  HelloForge
  Time:     2026-01-29 14:28:42
  Status:   ✓ SUCCESS
  Duration: 5.3s
  Warnings: 0
  Errors:   0

Build #1
  Project:  HelloForge
  Time:     2026-01-29 14:25:10
  Status:   ✓ SUCCESS
  Duration: 7.4s
  Warnings: 0
  Errors:   0

=== Build Statistics ===

Total builds:     3
Successful:       3
Failed:           0
Success rate:     100.0%
Average duration: 4.6s
```

### Query Specific Build Details
 in the `tutorial` directory:

```python
#!/usr/bin/env python3
"""
Get detailed information about a specific build.
"""
import sys
from pathlib import Path

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from forge.storage.data_persistence import DataPersistence.storage.data_persistence import DataPersistence
import sys

if len(sys.argv) < 2:
    print("Usage: python build_details.py <build_id>")
    sys.exit(1)

build_id = int(sys.argv[1])

# Connect to database
db = DataPersistence()
db.initialize_database()

# Get build details
build = db.get_build_by_id(build_id)

if not build:
    print(f"Build #{build_id} not found")
    sys.exit(1)

print(f"=== Build #{build['id']} Details ===\n")
print(f"Project:       {build['project_name']}")
print(f"Build Type:    {build.get('build_type', 'N/A')}")
print(f"Generator:     {build.get('generator', 'N/A')}")
print(f"Compiler:      {build.get('compiler', 'N/A')}")
print(f"CMake Version: {build.get('cmake_version', 'N/A')}")
print(f"Start Time:    {build['start_time']}")
print(f"End Time:      {build['end_time']}")
print(f"Duration:      {build['duration']:.2f}s")
print(f"Success:       {build['success']}")
print(f"Exit Code:     {build['exit_code']}")

if build['targets']:
    print(f"\nTargets Built: {', '.join(build['targets'])}")

if build['warning_count'] > 0:
    print(f"\nWarnings ({build['warning_count']}):")
    warnings = db.get_warnings(build_id)
    for w in warnings[:5]:  # Show first 5
        print(f"  {w['file']}:{w['line']}: {w['message']}")

if build['error_count'] > 0:
    print(f"\nErrors ({build['error_count']}):")
    errors = db.get_errors(build_id)
    for e in errors:
   powershell print(f"  {e['file']}:{e['line']}: {e['message']}")
```

Use it:

```bash
python build_details.py 1
```

---

## Tutorial 4: Tracking Build Performance

### Create a Performance Monitor

Let's track how build times change over multiple runs.

Create `performance_monitor.py` in the `tutorial` directory:

```python
#!/usr/bin/env python3
"""
Monitor build performance over time.
"""
import sys
from pathlib import Path

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from forge.storage.data_persistence import DataPersistence
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Connect to database
db = DataPersistence()
db.initialize_database()

# Get builds from last 7 days
since = datetime.now() - timedelta(days=7)
builds = db.get_builds_since(since)

# Filter for our project
project_builds = [b for b in builds if b['project_name'] == 'HelloForge']

if not project_builds:
    print("No builds found for HelloForge in the last 7 days")
    exit(0)

# Extract data
timestamps = [datetime.fromisoformat(b['timestamp']) for b in project_builds]
durations = [b['duration'] for b in project_builds]
build_numbers = list(range(1, len(project_builds) + 1))

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

# Plot 1: Build duration over time
ax1.plot(timestamps, durations, marker='o', linewidth=2, markersize=6)
ax1.set_xlabel('Time')
ax1.set_ylabel('Duration (seconds)')
ax1.set_title('Build Duration Over Time')
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45)

# Add average line
avg_duration = sum(durations) / len(durations)
ax1.axhline(y=avg_duration, color='r', linestyle='--',
            label=f'Average: {avg_duration:.1f}s')
ax1.legend()

# Plot 2: Build number vs duration
colors = ['green' if b['success'] else 'red' for b in project_builds]
ax2.bar(build_numbers, durations, color=colors, alpha=0.6)
ax2.set_xlabel('Build Number')
ax2.set_ylabel('Duration (seconds)')
ax2.set_title('Build Duration by Build Number (Green=Success, Red=Failed)')
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('build_performance.png', dpi=150)
print("Performance chart saved to: build_performance.png")

# Print summary statistics
print("\n=== Performance Summary ===")
print(f"Total builds:        {len(project_builds)}")
print(f"Average duration:    {avg_duration:.2f}s")
print(f"Fastest build:       {min(durations):.2f}s")
print(f"Slowest build:       {max(durations):.2f}s")
print(f"Duration variance:   {max(durations) - min(durations):.2f}s")

# Identify performance trends
if len(durations) >= 5:
    recent_avg = sum(durations[-5:]) / 5
    older_avg = sum(durations[:-5]) / len(durations[:-5]) if len(durations) > 5 else avg_duration

    if recent_avg > older_avg * 1.1:
        print(f"\n⚠️  Builds are getting slower! Recent avg: {recent_avg:.1f}s vs {older_avg:.1f}s")
    elif recent_avg < older_avg * 0.9:
        print(f"\n✓ Builds are getting faster! Recent avg: {recent_avg:.1f}s vs {older_avg:.1f}s")
    else:
        print(f"\n✓ Build performance is stable")
```

Install matplotlib if needed:

```powershell
pip install matplotlib
```

Run several builds to collect data:

```powershell
# From tutorial directory
# Do 10 builds
for ($i=1; $i -le 10; $i++) {
    Write-Host "Build #$i"
    cd ..\..\..
    python -m forge --source-dir forge\tutorial\sample-project --build-dir forge\tutorial\sample-project\build --no-configure 2>&1 | Out-Null
    cd forge\tutorial
    Start-Sleep -Seconds 2
}

# Analyze performance
python performance_monitor.py
```

Open `build_performance.png` to see your build performance trends!

### Set Up Performance Alerts

Create `performance_alert.py` in the `tutorial` directory:

```python
#!/usr/bin/env python3
"""
Alert if build performance degrades.
"""
import sys
from pathlib import Path

# Add forge to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from forge.storage.data_persistence import DataPersistence
from datetime import datetime, timedelta

# Thresholds
MAX_DURATION = 10.0  # seconds
MAX_WARNINGS = 5
MIN_SUCCESS_RATE = 95.0  # percent

# Connect to database
db = DataPersistence()
db.initialize_database()

# Get recent builds
since = datetime.now() - timedelta(days=1)
builds = db.get_builds_since(since)

if not builds:
    print("No recent builds to analyze")
    sys.exit(0)

# Check for issues
issues = []

# Check duration
avg_duration = sum(b['duration'] for b in builds) / len(builds)
if avg_duration > MAX_DURATION:
    issues.append(f"Average build duration ({avg_duration:.1f}s) exceeds threshold ({MAX_DURATION}s)")

# Check warnings
total_warnings = sum(b['warning_count'] for b in builds)
if total_warnings > MAX_WARNINGS:
    issues.append(f"Total warnings ({total_warnings}) exceeds threshold ({MAX_WARNINGS})")

# Check success rate
success_count = sum(1 for b in builds if b['success'])
success_rate = (success_count / len(builds)) * 100
if success_rate < MIN_SUCCESS_RATE:
    issues.append(f"Success rate ({success_rate:.1f}%) below threshold ({MIN_SUCCESS_RATE}%)")

# Report
if issues:
    print("⚠️  BUILD PERFORMANCE ALERTS\n")
    for issue in issues:
        print(f"  • {issue}")
    sys.exit(1)
else:
    print("✓ All build performance metrics are healthy")
   powershell
# Run after build
cd ..\..\..
python -m forge --source forge\tutorial\sample-project --build forge\tutorial\sample-project\build --configure --build-cmd
cd forge\tutorial
python performance_alert.py
if ($LASTEXITCODE -ne 0) { exit 1 }

```bash
# Run after build
python -m forge --source . --build ./build --configure --build-cmd
python performance_alert.py || exit 1
```

---

## Tutorial 5: CI/CD Integration

### GitHub Actions Integration

Create `.github/workflows/forge-build.yml` in your project root:

```yaml
name: Build with Forge

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    name: Build on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        build_type: [Debug, Release]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install CMake
        uses: jwlawson/actions-setup-cmake@v2
        with:
          cmake-version: '3.25.x'

      - name: Install Forge
        run: |
          pip install -e .
        working-directory: ./forge

      - name: Build with Forge
        shell: pwsh
        run: |
          New-Item -ItemType Directory -Path forge/tutorial/sample-project/build -Force
          python -m forge --source-dir forge/tutorial/sample-project --build-dir forge/tutorial/sample-project/build --verbose

      - name: Run executable (Windows)
        if: runner.os == 'Windows'
        shell: pwsh
        run: |
          .\forge\tutorial\sample-project\build\${{ matrix.build_type }}\hello.exe

      - name: Run executable (Unix)
        if: runner.os != 'Windows'
        shell: bash
        run: |
          ./forge/tutorial/sample-project/build/hello

      - name: Upload build database
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: build-data-${{ matrix.os }}-${{ matrix.build_type }}
          path: |
            ~/.forge/builds.db
            forge/tutorial/build_performance.png

      - name: Check build health
        shell: pwsh
        run: |
          cd forge/tutorial
          python performance_alert.py
        continue-on-error: true
```

### PowerShell Pre-commit Script

Create `pre-commit-check.ps1` in the `tutorial` directory:

```powershell
#!/usr/bin/env pwsh
#
# Pre-commit validation: Validate build before committing
#

Write-Host "🔨 Running pre-commit build validation..." -ForegroundColor Cyan

# Save current location
Push-Location

try {
    # Navigate to argos directory
    Set-Location $PSScriptRoot\..\..\..

    # Run Forge build
    if (!(Test-Path forge\tutorial\sample-project\build-pre-commit)) {
        New-Item -ItemType Directory -Path forge\tutorial\sample-project\build-pre-commit
    }
    python -m forge --source-dir forge\tutorial\sample-project `
        --build-dir forge\tutorial\sample-project\build-pre-commit `
        2>&1 | Out-Null

    $buildResult = $LASTEXITCODE

    # Clean up
    if (Test-Path forge\tutorial\sample-project\build-pre-commit) {
        Remove-Item -Recurse -Force forge\tutorial\sample-project\build-pre-commit
    }

    if ($buildResult -ne 0) {
        Write-Host "❌ Build failed! Please fix build errors before committing." -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Build validation passed!" -ForegroundColor Green
    exit 0
}
finally {
    # Restore location
    Pop-Location
}
```

To use it as a git hook, create `.git/hooks/pre-commit`:

```powershell
# Content of .git/hooks/pre-commit (no extension on Unix)
#!/usr/bin/env pwsh
& "$PSScriptRoot\..\..\forge\tutorial\pre-commit-check.ps1"
```

Test it:

```powershell
# Make it executable (Unix/macOS)
# chmod +x .git/hooks/pre-commit

# Test manually
.\pre-commit-check.ps1

# Or commit to trigger automatically
git add .
git commit -m "Test pre-commit hook"
```

### Jenkins Pipeline

Create `Jenkinsfile` in your project root:

```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'BUILD_TYPE',
            choices: ['Debug', 'Release', 'RelWithDebInfo'],
            description: 'CMake build type'
        )
    }

    environment {
        FORGE_DB = "${WORKSPACE}\\.forge\\builds.db"
    }

    stages {
        stage('Setup') {
            steps {
                pwsh '''
                    python -m pip install --user -e ./forge
                '''
            }
        }

        stage('Build') {
            steps {
                pwsh """
                    if (!(Test-Path forge/tutorial/sample-project/build)) {
                        New-Item -ItemType Directory -Path forge/tutorial/sample-project/build
                    }
                    python -m forge --source-dir forge/tutorial/sample-project `
                        --build-dir forge/tutorial/sample-project/build `
                        --database ${env.FORGE_DB} `
                        --verbose
                """
            }
        }

        stage('Test') {
            steps {
                pwsh '''
                    if ($IsWindows) {
                        .\\forge\\tutorial\\sample-project\\build\\Debug\\hello.exe
                    } else {
                        ./forge/tutorial/sample-project/build/hello
                    }
                '''
            }
        }

        stage('Analyze') {
            steps {
                pwsh '''
                    cd forge/tutorial
                    python analyze_builds.py
                    python performance_monitor.py
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '.forge/builds.db,forge/tutorial/build_performance.png',
                            allowEmptyArchive: true
        }
        success {
            echo 'Build completed successfully!'
        }
        failure {
            echo 'Build failed!'
        }
    }
}
```

---

## Next Steps

Congratulations! You've completed the Forge tutorial. Here's what to explore next:

### Advanced Topics

1. **Custom Build Configurations**
   - Multi-configuration generators
   - Toolchain files
   - Cross-compilation

2. **Build Optimization**
   - ccache integration
   - Distributed builds
   - Pre-compiled headers

3. **Advanced Analysis**
   - Warning trend analysis
   - Build time profiling
   - Dependency tracking

### Additional Resources

- [User Guide](USER_GUIDE.md) - Complete reference
- [API Documentation](API.md) - Python API reference
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- [GitHub Repository](https://github.com/lmvcruz/argos) - Source code and issues

### Practice Projects

Try using Forge with:
- Your own C/C++ projects
- Open-source CMake projects
- Multi-library projects with dependencies

### Community

- Report issues on GitHub
- Share your Forge workflows
- Contribute improvements

---

**Happy Building with Forge! 🔨**
