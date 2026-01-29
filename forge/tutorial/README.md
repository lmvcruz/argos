# Forge Tutorial

Welcome to the Forge hands-on tutorial! This directory contains everything you need to learn Forge through practical examples.

## Getting Started

### Prerequisites

- Python 3.8+ installed
- CMake 3.15+ installed
- A C++ compiler (MSVC, GCC, or Clang)
- PowerShell (Windows PowerShell 5.1+ or PowerShell Core 7+)

### Directory Structure

```
tutorial/
├── README.md                    # This file
├── TUTORIAL.md                  # Complete step-by-step tutorial
├── sample-project/              # Created during tutorial
│   ├── CMakeLists.txt
│   ├── src/
│   │   ├── main.cpp
│   │   ├── greeter.h
│   │   └── greeter.cpp
│   ├── build/                   # Build output
│   ├── build-debug/             # Debug build
│   └── build-release/           # Release build
├── analyze_builds.py            # Build analysis script
├── build_details.py             # Detailed build info script
├── performance_monitor.py       # Performance tracking script
├── performance_alert.py         # Performance alert script
└── pre-commit-check.ps1         # Git pre-commit hook
```

## Quick Start

### Step 1: Navigate to Tutorial Directory

```powershell
# From anywhere in the repository
cd argos/forge/tutorial
```

### Step 2: Verify Prerequisites

```powershell
# Check Python
python --version

# Check CMake
cmake --version

# Check Forge
cd ..\..\..
python -m forge --version
cd forge\tutorial
```

### Step 3: Follow the Tutorial

Open [TUTORIAL.md](TUTORIAL.md) and follow the step-by-step instructions. The tutorial will guide you through:

1. **Tutorial Setup** - Creating a sample C++ project
2. **Tutorial 1** - Your first build with Forge
3. **Tutorial 2** - Working with Debug and Release builds
4. **Tutorial 3** - Analyzing build data with Python
5. **Tutorial 4** - Tracking build performance over time
6. **Tutorial 5** - Integrating Forge into CI/CD pipelines

## Important Notes

### Working Directory

**All tutorial commands assume you're in the `forge/tutorial` directory** unless otherwise specified. Commands that need to run Forge will navigate to the `argos` parent directory temporarily:

```powershell
# Typical Forge command pattern in the tutorial
cd ..\..\..                          # Navigate to argos directory
python -m forge [options]            # Run Forge
cd forge\tutorial                    # Return to tutorial directory
```

### PowerShell Focus

This tutorial uses PowerShell syntax throughout. All examples are designed to work in:
- Windows PowerShell 5.1+
- PowerShell Core 7+ (cross-platform)

The commands will work on Windows, Linux, and macOS with PowerShell Core installed.

### Python Scripts

Python analysis scripts in this directory need to import the Forge module. They handle this by adding the parent directory to the Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from forge.storage.data_persistence import DataPersistence
```

## Troubleshooting

### "python: command not found"

Make sure Python is installed and in your PATH. Try `python3` instead of `python` on some systems.

### "cmake: command not found"

Install CMake and add it to your PATH. Download from: https://cmake.org/download/

### "No module named 'forge'"

Make sure you're running commands from the correct directory structure:
```
argos/
├── forge/
│   └── tutorial/    # ← You should be here
```

### Build Errors

Check that you have a C++ compiler installed:
- **Windows**: Install Visual Studio or Visual Studio Build Tools
- **Linux**: Install `build-essential` package
- **macOS**: Install Xcode Command Line Tools

## Next Steps

After completing the tutorial:

1. Read the [User Guide](../docs/USER_GUIDE.md) for comprehensive documentation
2. Check the [API Documentation](../docs/API.md) for programmatic usage
3. See [Troubleshooting Guide](../docs/TROUBLESHOOTING.md) for common issues
4. Try Forge with your own projects!

## Questions or Issues?

- Check the [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
- Open an issue on [GitHub](https://github.com/lmvcruz/argos/issues)
- Read the full [User Guide](../docs/USER_GUIDE.md)

Happy building with Forge! 🔨
