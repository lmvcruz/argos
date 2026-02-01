# Anvil Troubleshooting Guide

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Validator Errors](#validator-errors)
4. [Git Hook Issues](#git-hook-issues)
5. [Performance Problems](#performance-problems)
6. [Statistics Issues](#statistics-issues)
7. [Platform-Specific Issues](#platform-specific-issues)
8. [Common Error Messages](#common-error-messages)
9. [Getting Help](#getting-help)

## Installation Issues

### Pip Installation Fails

**Problem**: `pip install -e .` fails with errors

**Solutions**:

1. **Check Python Version**
   ```bash
   python --version  # Must be 3.8+
   ```

2. **Upgrade pip**
   ```bash
   python -m pip install --upgrade pip
   ```

3. **Install in Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -e .
   ```

4. **Check setup.py**
   ```bash
   python setup.py check
   ```

### Command Not Found: anvil

**Problem**: `anvil: command not found` after installation

**Solutions**:

1. **Check Installation**
   ```bash
   pip show anvil
   ```

2. **Add to PATH**
   ```bash
   # Linux/macOS
   export PATH="$HOME/.local/bin:$PATH"

   # Windows (PowerShell)
   $env:PATH += ";$HOME\AppData\Local\Programs\Python\Python3X\Scripts"
   ```

3. **Use Python Module**
   ```bash
   python -m anvil check
   ```

4. **Reinstall**
   ```bash
   pip uninstall anvil
   pip install -e .
   ```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'anvil'`

**Solutions**:

1. **Verify Installation**
   ```bash
   pip list | grep anvil
   ```

2. **Check Python Path**
   ```python
   import sys
   print(sys.path)
   ```

3. **Install in Editable Mode**
   ```bash
   cd anvil/
   pip install -e .
   ```

## Configuration Problems

### Configuration File Not Found

**Problem**: `Configuration error: anvil.toml not found`

**Solutions**:

1. **Create Configuration**
   ```bash
   anvil config init
   ```

2. **Check Working Directory**
   ```bash
   pwd  # Should be project root
   ```

3. **Specify Path**
   ```bash
   anvil check --config /path/to/anvil.toml
   ```

### Invalid Configuration

**Problem**: `Configuration error: Invalid value for ...`

**Solutions**:

1. **Validate Configuration**
   ```bash
   anvil config validate
   ```

2. **Show Parsed Configuration**
   ```bash
   anvil config show
   ```

3. **Check TOML Syntax**
   ```bash
   python -c "import toml; toml.load('anvil.toml')"
   ```

4. **Common Fixes**:
   ```toml
   # Wrong: String instead of array
   languages = "python"

   # Correct:
   languages = ["python"]

   # Wrong: Invalid language
   languages = ["java"]

   # Correct:
   languages = ["python", "cpp"]
   ```

### Validator Not Recognized

**Problem**: `Unknown validator: myvalidator`

**Solutions**:

1. **List Available Validators**
   ```bash
   anvil list
   ```

2. **Check Spelling**
   ```bash
   # Wrong: anvil check --validator flake-8
   # Correct:
   anvil check --validator flake8
   ```

3. **Check Language**
   ```bash
   # Python validator on C++ code won't work
   anvil check --language cpp --validator flake8  # ERROR
   ```

## Validator Errors

### Tool Not Installed

**Problem**: `Error: flake8 not found`

**Solutions**:

1. **Check Tool Availability**
   ```bash
   anvil config check-tools
   ```

2. **Install Missing Tools**
   ```bash
   # Python tools
   pip install flake8 black isort pylint pytest pytest-cov

   # C++ tools (platform-specific)
   # Ubuntu/Debian
   sudo apt install clang-tidy cppcheck cpplint clang-format

   # macOS
   brew install llvm cppcheck cpplint clang-format
   ```

3. **Disable Unavailable Validators**
   ```toml
   [python.mypy]
   enabled = false  # Disable if not installed
   ```

### Timeout Errors

**Problem**: `Validation timed out after 300 seconds`

**Solutions**:

1. **Increase Timeout**
   ```toml
   [validation]
   timeout = 600  # 10 minutes
   ```

2. **Use Incremental Mode**
   ```bash
   anvil check --incremental
   ```

3. **Reduce Parallel Workers**
   ```toml
   [validation]
   max_workers = 2  # Reduce from 4
   ```

4. **Run Specific Validators**
   ```bash
   anvil check --validator flake8  # Only one validator
   ```

### Parser Errors

**Problem**: `Failed to parse output from validator`

**Solutions**:

1. **Check Validator Version**
   ```bash
   flake8 --version
   black --version
   ```

2. **Update Validator**
   ```bash
   pip install --upgrade flake8 black
   ```

3. **Check Output Manually**
   ```bash
   flake8 src/ --format=default
   ```

4. **Enable Verbose Logging**
   ```bash
   anvil check --verbose
   ```

### Coverage Below Threshold

**Problem**: `Coverage 85.5% below minimum 90.0%`

**Solutions**:

1. **Add Tests**
   - Write tests for uncovered code
   - Check coverage report: `pytest --cov --cov-report=html`

2. **Adjust Threshold**
   ```toml
   [python.pytest]
   min_coverage = 85.0  # Lower threshold
   ```

3. **Exclude Files**
   ```toml
   [python.pytest]
   coverage_omit = [
       "tests/*",
       "*/migrations/*",
       "*/__pycache__/*"
   ]
   ```

4. **Check Coverage by File**
   ```bash
   pytest --cov --cov-report=term-missing
   ```

## Git Hook Issues

### Hook Not Running

**Problem**: Git commits succeed without running Anvil

**Solutions**:

1. **Check Hook Installation**
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. **Reinstall Hook**
   ```bash
   anvil install-hooks
   ```

3. **Check Hook Permissions** (Linux/macOS)
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

4. **Test Hook Manually**
   ```bash
   .git/hooks/pre-commit
   ```

### Hook Prevents All Commits

**Problem**: Hook always fails, can't commit

**Solutions**:

1. **Check Hook Output**
   ```bash
   git commit -m "Test"
   # Read error messages
   ```

2. **Fix Issues First**
   ```bash
   anvil check --incremental
   # Fix reported issues
   ```

3. **Bypass Hook Temporarily**
   ```bash
   git commit --no-verify -m "WIP commit"
   ```

4. **Use Bypass Keyword**
   ```bash
   git commit -m "[skip-anvil] WIP changes"
   ```

### Hook Runs on All Files

**Problem**: Pre-commit hook validates all files, not just changed

**Solutions**:

1. **Check Hook Script**
   ```bash
   cat .git/hooks/pre-commit
   # Should have: anvil check --incremental
   ```

2. **Reinstall Hook**
   ```bash
   anvil install-hooks --uninstall
   anvil install-hooks
   ```

3. **Manual Fix**
   Edit `.git/hooks/pre-commit`:
   ```bash
   #!/bin/bash
   anvil check --incremental
   ```

### Hook Fails in CI

**Problem**: Hook works locally but fails in CI

**Solutions**:

1. **Check Git History**
   ```yaml
   # GitHub Actions
   - uses: actions/checkout@v3
     with:
       fetch-depth: 0  # Full history required
   ```

2. **Install Tools in CI**
   ```yaml
   - name: Install Tools
     run: pip install flake8 black isort pylint pytest
   ```

3. **Check CI Environment**
   ```yaml
   - name: Debug
     run: |
       which python
       python --version
       which anvil
       anvil list
   ```

## Performance Problems

### Slow Validation

**Problem**: `anvil check` takes too long

**Solutions**:

1. **Use Incremental Mode**
   ```bash
   anvil check --incremental  # Only changed files
   ```

2. **Enable Parallel Execution**
   ```toml
   [validation]
   parallel = true
   max_workers = 4
   ```

3. **Disable Slow Validators**
   ```toml
   [python.pylint]
   enabled = false  # Slow validator
   ```

4. **Profile Execution**
   ```bash
   anvil check --verbose  # Shows timing per validator
   ```

5. **Use Fail-Fast**
   ```bash
   anvil check --fail-fast  # Stop on first error
   ```

### High Memory Usage

**Problem**: Anvil uses too much memory

**Solutions**:

1. **Reduce Parallel Workers**
   ```toml
   [validation]
   max_workers = 2  # Lower from 4
   ```

2. **Process Files in Batches**
   ```bash
   # Split large projects
   anvil check --validator flake8 src/module1/
   anvil check --validator flake8 src/module2/
   ```

3. **Disable Statistics**
   ```toml
   [statistics]
   enabled = false
   ```

### Database Lock Errors

**Problem**: `Database is locked`

**Solutions**:

1. **Check for Multiple Processes**
   ```bash
   ps aux | grep anvil
   ```

2. **Wait and Retry**
   ```bash
   sleep 5
   anvil check
   ```

3. **Delete Lock File**
   ```bash
   rm .anvil/stats.db-journal
   ```

4. **Recreate Database**
   ```bash
   rm .anvil/stats.db
   anvil check  # Recreates database
   ```

## Statistics Issues

### Statistics Not Tracking

**Problem**: No statistics being recorded

**Solutions**:

1. **Enable Statistics**
   ```toml
   [statistics]
   enabled = true
   ```

2. **Check Database Path**
   ```bash
   ls -la .anvil/stats.db
   ```

3. **Check Permissions**
   ```bash
   # Linux/macOS
   chmod 644 .anvil/stats.db
   ```

4. **Recreate Database**
   ```bash
   rm .anvil/stats.db
   anvil check
   ```

### Invalid Statistics Queries

**Problem**: `anvil stats report` shows errors

**Solutions**:

1. **Check Database Integrity**
   ```bash
   sqlite3 .anvil/stats.db "PRAGMA integrity_check;"
   ```

2. **Export and Reimport**
   ```bash
   anvil stats export --format json --output backup.json
   rm .anvil/stats.db
   # Reimport not implemented - statistics will rebuild
   ```

3. **Check Sufficient History**
   ```bash
   anvil stats report --days 30  # May need more runs
   ```

### Smart Filtering Not Working

**Problem**: Smart filtering doesn't skip tests

**Solutions**:

1. **Check Configuration**
   ```toml
   [smart-filtering]
   enabled = true
   skip_success_threshold = 0.95
   min_history_runs = 10  # Need at least 10 runs
   ```

2. **Build History**
   ```bash
   # Need multiple runs first
   anvil check  # Run 10+ times
   ```

3. **Verify Statistics**
   ```bash
   anvil stats report
   # Check if sufficient history exists
   ```

4. **Check Test Success Rates**
   ```bash
   anvil stats flaky  # Shows test success rates
   ```

## Platform-Specific Issues

### Windows

#### Path Separators

**Problem**: Paths with backslashes cause errors

**Solutions**:
```toml
# Use forward slashes in config
[python.pytest]
test_paths = ["tests/"]  # Not "tests\"
```

#### Line Endings

**Problem**: Git line ending issues

**Solutions**:
```bash
# Configure git
git config core.autocrlf true
```

#### Permission Errors

**Problem**: `Access denied` errors

**Solutions**:
1. Run as Administrator
2. Check file permissions
3. Disable antivirus temporarily

### macOS

#### Command Line Tools

**Problem**: `xcrun: error: invalid active developer path`

**Solutions**:
```bash
xcode-select --install
```

#### Homebrew Tools

**Problem**: Tools not found after Homebrew install

**Solutions**:
```bash
# Add Homebrew to PATH
export PATH="/opt/homebrew/bin:$PATH"

# Or use full path in config
[cpp.clang-tidy]
command = "/opt/homebrew/bin/clang-tidy"
```

### Linux

#### Tool Installation

**Problem**: Validators not found

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip clang-tidy cppcheck

# Fedora/RHEL
sudo dnf install python3-pip clang-tools-extra cppcheck
```

#### Permission Denied

**Problem**: Can't execute validators

**Solutions**:
```bash
chmod +x .git/hooks/pre-commit
```

## Common Error Messages

### "No module named 'anvil'"

**Cause**: Anvil not installed or wrong Python environment

**Fix**:
```bash
pip install -e ./anvil
```

### "Configuration file not found"

**Cause**: Missing `anvil.toml`

**Fix**:
```bash
anvil config init
```

### "Validator not available"

**Cause**: Tool not installed

**Fix**:
```bash
anvil config check-tools
pip install <missing-tool>
```

### "Validation failed with exit code 1"

**Cause**: Validators found issues

**Fix**:
```bash
anvil check --verbose  # See detailed errors
# Fix reported issues
```

### "Database is locked"

**Cause**: Multiple Anvil processes or crashed process

**Fix**:
```bash
# Kill other processes
pkill -9 anvil

# Remove lock
rm .anvil/stats.db-journal
```

### "Failed to parse output"

**Cause**: Validator output format changed

**Fix**:
```bash
# Update validator
pip install --upgrade <validator>

# Update Anvil
pip install --upgrade anvil
```

### "Timeout expired"

**Cause**: Validation took too long

**Fix**:
```toml
[validation]
timeout = 600  # Increase timeout
```

## Getting Help

### Check Documentation

1. **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
2. **Configuration**: [CONFIGURATION.md](CONFIGURATION.md)
3. **API Docs**: [API.md](API.md)

### Debugging Tools

```bash
# Verbose output
anvil check --verbose

# Show configuration
anvil config show

# Validate configuration
anvil config validate

# List validators
anvil list --detailed

# Check tool availability
anvil config check-tools

# View statistics
anvil stats report
```

### Enable Debug Logging

```bash
# Set environment variable
export ANVIL_LOG_LEVEL=DEBUG
anvil check
```

### Create Minimal Reproduction

1. **Create small test case**
   ```bash
   mkdir test-project
   cd test-project
   echo "print('hello')" > test.py
   anvil config init
   anvil check
   ```

2. **Share configuration**
   ```bash
   cat anvil.toml
   ```

3. **Share error output**
   ```bash
   anvil check --verbose 2>&1 | tee anvil-error.log
   ```

### Report Issues

When reporting issues, include:

1. **Anvil version**: `anvil --version`
2. **Python version**: `python --version`
3. **Platform**: `uname -a` (Linux/macOS) or `ver` (Windows)
4. **Configuration**: `anvil.toml` contents
5. **Error output**: Full error message with `--verbose`
6. **Validator versions**: Tool versions (e.g., `flake8 --version`)

### Community Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check docs/ directory
- **Examples**: See examples/ directory

## Quick Reference

### Diagnostic Commands

```bash
# Installation check
pip show anvil

# Configuration check
anvil config validate
anvil config show

# Tool availability
anvil config check-tools
which flake8 black pylint pytest

# Run validation
anvil check --verbose
anvil check --incremental

# Statistics
anvil stats report
anvil stats flaky

# Git hooks
ls -la .git/hooks/
cat .git/hooks/pre-commit
```

### Common Fixes

```bash
# Reinstall Anvil
pip uninstall anvil
pip install -e ./anvil

# Reinstall hooks
anvil install-hooks --uninstall
anvil install-hooks

# Reset database
rm -rf .anvil/
anvil check

# Update tools
pip install --upgrade flake8 black isort pylint pytest

# Clear cache
rm -rf __pycache__/ .pytest_cache/ .coverage
```

## Prevention Tips

1. **Use Virtual Environment**: Isolate Python dependencies
2. **Pin Versions**: Use `requirements.txt` for reproducibility
3. **Test Configuration**: Run `anvil config validate` after changes
4. **Regular Updates**: Keep Anvil and validators updated
5. **Version Control**: Commit `anvil.toml` to repository
6. **CI Testing**: Test hooks in CI pipeline
7. **Documentation**: Document project-specific configuration
8. **Monitoring**: Track validation metrics with statistics

## Further Reading

- [User Guide](USER_GUIDE.md) - Comprehensive usage guide
- [Configuration Reference](CONFIGURATION.md) - All configuration options
- [API Documentation](API.md) - Extending Anvil
- [Tutorial](../TUTORIAL.md) - Step-by-step guide
