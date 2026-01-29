# Forge Troubleshooting Guide

This guide helps you diagnose and fix common issues when using Forge.
> **Note:** Commands in this guide use `python -m forge` which works without installation. If you've installed Forge with `pip install -e .`, you can use `forge` instead.
## Table of Contents

1. [Installation Issues](#installation-issues)
2. [CMake Detection Problems](#cmake-detection-problems)
3. [Build Failures](#build-failures)
4. [Database Issues](#database-issues)
5. [Performance Problems](#performance-problems)
6. [Platform-Specific Issues](#platform-specific-issues)
7. [Error Messages Reference](#error-messages-reference)
8. [Getting Help](#getting-help)

---

## Installation Issues

### Problem: "forge: command not found"

**Symptoms:**
```bash
$ forge --version
bash: forge: command not found
```

**Solutions:**

1. **If running from source (not installed):**

   ```bash
   # Make sure you're in the argos parent directory
   cd /path/to/argos  # NOT argos/forge
   python -m forge --version
   ```

2. **To install Forge and enable the `forge` command:**

   ```bash
   cd /path/to/argos/forge
   pip install -e .

   # Verify installation
   forge --version
   pip list | grep forge
   ```

3. **Check Python scripts directory in PATH (after installation):**
   ```bash
   # Linux/macOS
   echo $PATH | grep -o '[^:]*python[^:]*'

   # Windows
   echo %PATH% | findstr Python
   ```

   Add Python scripts to PATH if missing:
   ```bash
   # Linux/macOS (add to ~/.bashrc or ~/.zshrc)
   export PATH="$HOME/.local/bin:$PATH"

   # Windows (System Properties > Environment Variables)
   # Add: %USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts
   ```

### Problem: "ModuleNotFoundError: No module named 'forge'"

**Symptoms:**
```python
Traceback (most recent call last):
  File "...", line 1, in <module>
    from forge.storage.data_persistence import DataPersistence
ModuleNotFoundError: No module named 'forge'
```

**Solutions:**

1. **Install in editable mode:**
   ```bash
   cd /path/to/argos/forge
   pip install -e .
   ```

2. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

3. **Verify PYTHONPATH:**
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   # Should include forge directory
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Problem: "Permission denied" during installation

**Symptoms:**
```bash
ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied
```

**Solutions:**

1. **Use virtual environment (recommended):**
   ```bash
   python -m venv forge-env
   source forge-env/bin/activate  # Linux/macOS
   forge-env\Scripts\activate     # Windows
   pip install -e .
   ```

2. **User installation:**
   ```bash
   pip install --user -e .
   ```

3. **Use sudo (not recommended):**
   ```bash
   sudo pip install -e .
   ```

---

## CMake Detection Problems

### Problem: "CMake not found in PATH"

**Symptoms:**
```bash
$ python -m forge --source . --build ./build --configure
Error: CMake not found in PATH
```

**Solutions:**

1. **Verify CMake installation:**
   ```bash
   cmake --version
   ```

   If not found, install CMake:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install cmake

   # macOS
   brew install cmake

   # Windows
   # Download from https://cmake.org/download/
   ```

2. **Add CMake to PATH:**
   ```bash
   # Linux/macOS (add to ~/.bashrc)
   export PATH="/opt/cmake/bin:$PATH"

   # Windows (System Properties > Environment Variables)
   # Add: C:\Program Files\CMake\bin
   ```

3. **Specify CMake path explicitly:**
   ```bash
   export CMAKE_EXECUTABLE=/path/to/cmake
   python -m forge --source . --build ./build --configure
   ```

### Problem: "CMake version too old"

**Symptoms:**
```bash
Error: CMake 3.10.2 is too old. Forge requires CMake 3.15 or newer.
```

**Solutions:**

1. **Upgrade CMake:**
   ```bash
   # Ubuntu (using Kitware APT repository)
   wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null | sudo apt-key add -
   sudo apt-add-repository 'deb https://apt.kitware.com/ubuntu/ focal main'
   sudo apt-get update
   sudo apt-get install cmake

   # macOS
   brew upgrade cmake

   # Windows
   # Download latest from https://cmake.org/download/
   ```

2. **Use newer CMake from pip:**
   ```bash
   pip install cmake --upgrade
   ```

3. **Build CMake from source:**
   ```bash
   wget https://github.com/Kitware/CMake/releases/download/v3.25.1/cmake-3.25.1.tar.gz
   tar -xzf cmake-3.25.1.tar.gz
   cd cmake-3.25.1
   ./bootstrap && make && sudo make install
   ```

---

## Build Failures

### Problem: "Configuration failed"

**Symptoms:**
```bash
[CMAKE] CMake Error: The source directory "/path" does not contain a CMakeLists.txt
Configuration failed with exit code 1
```

**Solutions:**

1. **Verify CMakeLists.txt exists:**
   ```bash
   ls -la CMakeLists.txt
   ```

2. **Check source directory path:**
   ```bash
   # Use absolute path
   python -m forge --source /absolute/path/to/project --build ./build --configure

   # Or use current directory explicitly
   python -m forge --source $(pwd) --build ./build --configure
   ```

3. **Check file permissions:**
   ```bash
   chmod 644 CMakeLists.txt
   ```

### Problem: "Build failed with compiler errors"

**Symptoms:**
```bash
error: 'iostream' file not found
#include <iostream>
         ^~~~~~~~~~
Build failed with exit code 2
```

**Solutions:**

1. **Verify compiler installation:**
   ```bash
   # Check C++ compiler
   g++ --version
   clang++ --version
   ```

   Install if missing:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install build-essential

   # macOS
   xcode-select --install

   # Windows
   # Install Visual Studio Build Tools or MinGW
   ```

2. **Specify compiler explicitly:**
   ```bash
   python -m forge --source . --build ./build --configure \
     -D CMAKE_C_COMPILER=gcc \
     -D CMAKE_CXX_COMPILER=g++
   ```

3. **Check include paths:**
   ```bash
   # Verify standard library location
   echo '#include <iostream>' | g++ -x c++ -E -v -
   ```

### Problem: "Generator not available"

**Symptoms:**
```bash
CMake Error: Could not create named generator Ninja
```

**Solutions:**

1. **Install required generator:**
   ```bash
   # Ninja
   sudo apt-get install ninja-build  # Ubuntu
   brew install ninja                # macOS

   # Make (usually pre-installed on Linux/macOS)
   sudo apt-get install make
   ```

2. **Use different generator:**
   ```bash
   # Use Unix Makefiles
   python -m forge --source . --build ./build --configure --generator "Unix Makefiles"

   # Auto-detect generator (omit --generator)
   python -m forge --source . --build ./build --configure
   ```

3. **List available generators:**
   ```bash
   cmake --help
   # Look for "Generators" section
   ```

### Problem: "Permission denied" accessing build directory

**Symptoms:**
```bash
CMake Error: Cannot write to build directory: Permission denied
```

**Solutions:**

1. **Check directory permissions:**
   ```bash
   ls -ld ./build
   ```

2. **Remove and recreate:**
   ```bash
   rm -rf ./build
   mkdir ./build
   ```

3. **Use different build location:**
   ```bash
   python -m forge --source . --build ~/tmp/build --configure --build-cmd
   ```

4. **Fix ownership:**
   ```bash
   sudo chown -R $USER:$USER ./build
   ```

---

## Database Issues

### Problem: "Database file locked"

**Symptoms:**
```bash
Error: database is locked
```

**Solutions:**

1. **Close other Forge instances:**
   ```bash
   # Check running processes
   ps aux | grep forge

   # Kill if necessary
   pkill -f forge
   ```

2. **Remove lock file:**
   ```bash
   rm ~/.forge/builds.db-journal
   ```

3. **Use different database:**
   ```bash
   python -m forge --db-path ./build-data.db --source . --build ./build --configure
   ```

4. **Wait and retry:**
   SQLite locks are usually brief. Wait a few seconds and try again.

### Problem: "Database corruption"

**Symptoms:**
```bash
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions:**

1. **Backup current database:**
   ```bash
   cp ~/.forge/builds.db ~/.forge/builds.db.backup
   ```

2. **Attempt repair:**
   ```bash
   sqlite3 ~/.forge/builds.db "PRAGMA integrity_check;"
   sqlite3 ~/.forge/builds.db ".dump" | sqlite3 ~/.forge/builds_new.db
   mv ~/.forge/builds_new.db ~/.forge/builds.db
   ```

3. **Reset database (loses history):**
   ```bash
   rm ~/.forge/builds.db
   python -m forge --source . --build ./build --configure
   # New database will be created
   ```

4. **Export data before reset:**
   ```python
   from forge.storage.data_persistence import DataPersistence
   import json

   db = DataPersistence()
   builds = db.get_recent_builds(limit=1000)
   with open('builds_backup.json', 'w') as f:
       json.dump(builds, f, indent=2)
   ```

### Problem: "Cannot find database"

**Symptoms:**
```python
FileNotFoundError: No such file or directory: '/home/user/.forge/builds.db'
```

**Solutions:**

1. **Create database directory:**
   ```bash
   mkdir -p ~/.forge
   ```

2. **Initialize database explicitly:**
   ```python
   from forge.storage.data_persistence import DataPersistence
   db = DataPersistence()
   db.initialize_database()
   ```

3. **Specify database location:**
   ```bash
   python -m forge --db-path ./my-builds.db --source . --build ./build --configure
   ```

---

## Performance Problems

### Problem: "Builds are very slow"

**Symptoms:**
- Forge builds take significantly longer than plain CMake
- Build times increased after switching to Forge

**Solutions:**

1. **Use parallel builds:**
   ```bash
   python -m forge --source . --build ./build --build-cmd -j
   ```

2. **Check CPU usage:**
   ```bash
   # During build, monitor CPU
   top
   htop
   ```

3. **Verify disk speed:**
   ```bash
   # Test write speed to build directory
   dd if=/dev/zero of=./build/test.dat bs=1M count=1024
   ```

4. **Use faster build directory:**
   ```bash
   # Use tmpfs (RAM disk) on Linux
   mkdir /tmp/build
   python -m forge --source . --build /tmp/build --configure --build-cmd

   # Use SSD instead of HDD
   python -m forge --source . --build /mnt/ssd/build --configure --build-cmd
   ```

5. **Enable ccache:**
   ```bash
   sudo apt-get install ccache
   python -m forge --source . --build ./build --configure \
     -D CMAKE_C_COMPILER_LAUNCHER=ccache \
     -D CMAKE_CXX_COMPILER_LAUNCHER=ccache
   ```

### Problem: "Database queries are slow"

**Symptoms:**
```python
# Takes several seconds
builds = db.get_recent_builds()
```

**Solutions:**

1. **Check database size:**
   ```bash
   ls -lh ~/.forge/builds.db
   # If > 100MB, consider pruning
   ```

2. **Vacuum database:**
   ```bash
   sqlite3 ~/.forge/builds.db "VACUUM;"
   ```

3. **Limit query results:**
   ```python
   # Instead of getting all builds
   builds = db.get_recent_builds(limit=100)
   ```

4. **Archive old data:**
   ```python
   # Export old builds
   old_builds = db.get_builds_before(cutoff_date)
   # ... export to file ...
   # Delete from database
   db.delete_builds_before(cutoff_date)
   ```

### Problem: "High memory usage"

**Symptoms:**
- Forge process uses excessive RAM
- System becomes unresponsive during builds

**Solutions:**

1. **Reduce parallel jobs:**
   ```bash
   # Use fewer cores
   python -m forge --build-cmd -j 2
   ```

2. **Monitor memory:**
   ```bash
   # During build
   watch -n 1 'ps aux | grep forge'
   ```

3. **Disable output buffering:**
   ```bash
   # Use unbuffered output
   python -u -m python -m forge --source . --build ./build --configure
   ```

4. **Build incrementally:**
   ```bash
   # Build one target at a time
   python -m forge --build-cmd --target mylib
   python -m forge --build-cmd --target myapp
   ```

---

## Platform-Specific Issues

### Windows

#### Problem: "Path too long"

**Symptoms:**
```
The system cannot find the path specified
```

**Solutions:**

1. **Enable long paths:**
   ```powershell
   # Run as Administrator
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
     -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

2. **Use shorter build path:**
   ```bash
   python -m forge --source . --build C:\b --configure
   ```

3. **Use subst to create drive:**
   ```batch
   subst B: C:\very\long\path\to\project
   python -m forge --source B:\ --build B:\build --configure
   ```

#### Problem: "MSVC not found"

**Symptoms:**
```
Could not find Visual Studio installation
```

**Solutions:**

1. **Install Visual Studio Build Tools:**
   - Download from https://visualstudio.microsoft.com/downloads/
   - Select "Build Tools for Visual Studio"
   - Install C++ build tools

2. **Use Visual Studio Developer Command Prompt:**
   ```batch
   # Run forge from VS Developer Command Prompt
   "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
   python -m forge --source . --build ./build --configure
   ```

3. **Specify generator explicitly:**
   ```bash
   python -m forge --source . --build ./build --configure --generator "Visual Studio 16 2019"
   ```

### macOS

#### Problem: "xcrun: error: invalid active developer path"

**Symptoms:**
```
xcrun: error: invalid active developer path (/Library/Developer/CommandLineTools)
```

**Solutions:**

1. **Install Xcode Command Line Tools:**
   ```bash
   xcode-select --install
   ```

2. **Reset developer directory:**
   ```bash
   sudo xcode-select --reset
   ```

3. **Accept Xcode license:**
   ```bash
   sudo xcodebuild -license accept
   ```

#### Problem: "Library not loaded" errors

**Symptoms:**
```
dyld: Library not loaded: @rpath/libsomething.dylib
```

**Solutions:**

1. **Check library paths:**
   ```bash
   otool -L ./build/myapp
   ```

2. **Set DYLD_LIBRARY_PATH:**
   ```bash
   export DYLD_LIBRARY_PATH=/path/to/libs:$DYLD_LIBRARY_PATH
   python -m forge --build-cmd
   ```

3. **Use rpath:**
   ```bash
   python -m forge --configure -D CMAKE_INSTALL_RPATH_USE_LINK_PATH=ON
   ```

### Linux

#### Problem: "cannot find -lstdc++"

**Symptoms:**
```
/usr/bin/ld: cannot find -lstdc++
```

**Solutions:**

1. **Install C++ standard library:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libstdc++-11-dev

   # Fedora/RHEL
   sudo dnf install libstdc++-devel
   ```

2. **Verify linker paths:**
   ```bash
   ld --verbose | grep SEARCH_DIR
   ```

3. **Specify library path:**
   ```bash
   python -m forge --configure -D CMAKE_EXE_LINKER_FLAGS="-L/usr/lib/x86_64-linux-gnu"
   ```

#### Problem: "Permission denied" for /usr/local

**Symptoms:**
```
CMake Error: Cannot create directory /usr/local/...
```

**Solutions:**

1. **Use user-local install prefix:**
   ```bash
   python -m forge --configure -D CMAKE_INSTALL_PREFIX=$HOME/.local
   ```

2. **Build without installing:**
   ```bash
   python -m forge --build-cmd  # Don't run install target
   ```

---

## Error Messages Reference

### "ArgumentError: Source directory does not exist"

**Cause:** Specified source directory doesn't exist or path is wrong.

**Fix:**
```bash
# Check path
ls -la /path/to/source

# Use correct path
python -m forge --source /correct/path --build ./build --configure
```

### "CMakeExecutionError: CMake returned non-zero exit code"

**Cause:** CMake configuration or build failed.

**Fix:**
```bash
# Run with verbose output to see details
python -m forge --source . --build ./build --configure --build-cmd --verbose

# Check CMakeLists.txt for errors
cmake-gui .  # Visual inspection
```

### "DatabaseConnectionError: Unable to connect to database"

**Cause:** Database file permissions or corruption.

**Fix:**
```bash
# Check permissions
ls -l ~/.forge/builds.db

# Reset permissions
chmod 644 ~/.forge/builds.db

# Or use new database
python -m forge --db-path ./new-builds.db --source . --build ./build --configure
```

### "GeneratorError: Unsupported generator"

**Cause:** Specified CMake generator not available.

**Fix:**
```bash
# List available generators
cmake --help | grep -A 20 "Generators"

# Use available generator
python -m forge --generator "Unix Makefiles" --source . --build ./build --configure
```

---

## Getting Help

### Diagnostic Information

When reporting issues, include:

```bash
# Forge version
python -m forge --version

# CMake version
cmake --version

# Python version
python --version

# Operating system
uname -a  # Linux/macOS
systeminfo | findstr /B /C:"OS"  # Windows

# Full command that failed
python -m forge --source . --build ./build --configure --build-cmd --verbose 2>&1 | tee forge-error.log
```

### Enable Debug Logging

```bash
# Set environment variable for verbose logging
export FORGE_DEBUG=1
python -m forge --source . --build ./build --configure --build-cmd --verbose
```

### Test with Minimal Example

Create minimal test case:

```bash
mkdir ~/forge-test
cd ~/forge-test

# Create minimal CMakeLists.txt
cat > CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.15)
project(Test)
add_executable(test main.cpp)
EOF

# Create minimal source
cat > main.cpp << 'EOF'
int main() { return 0; }
EOF

# Test with Forge
python -m forge --source . --build ./build --configure --build-cmd --verbose
```

### Community Resources

- **GitHub Issues**: https://github.com/lmvcruz/argos/issues
- **Documentation**: https://github.com/lmvcruz/argos/tree/main/forge/docs
- **Source Code**: https://github.com/lmvcruz/argos/tree/main/forge

### Reporting Bugs

When filing a bug report, include:

1. Operating system and version
2. Python version
3. CMake version
4. Forge version
5. Complete command that failed
6. Full error output (with `--verbose`)
7. Minimal reproducible example
8. `forge-error.log` file

### Feature Requests

To request features:

1. Check existing issues first
2. Describe use case clearly
3. Explain expected behavior
4. Provide examples if possible

---

## Common Workarounds

### Workaround: Bypass Forge for debugging

If Forge is causing issues, test with plain CMake:

```bash
# Plain CMake equivalent of Forge commands
cmake -B ./build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build ./build -j

# If this works but Forge doesn't, file a bug report
```

### Workaround: Reset everything

Nuclear option - start completely fresh:

```bash
# Remove build directory
rm -rf ./build

# Remove database
rm -rf ~/.forge

# Remove CMake cache
rm -rf CMakeCache.txt CMakeFiles/

# Reinstall Forge
pip uninstall forge
cd /path/to/argos/forge
pip install -e .

# Try again
python -m forge --source . --build ./build --configure --build-cmd
```

### Workaround: Use Docker

If local environment is problematic, use Docker:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip cmake build-essential ninja-build

COPY forge/ /forge
WORKDIR /forge
RUN pip3 install -e .

WORKDIR /project
CMD ["bash"]
```

Build and run:

```bash
docker build -t forge .
docker run -v $(pwd):/project -it forge
python -m forge --source . --build ./build --configure --build-cmd
```

---

**Still having issues? Open a GitHub issue with diagnostic information!**
