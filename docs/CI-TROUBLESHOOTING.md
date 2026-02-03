# CI Troubleshooting Guide

**Last Updated**: February 2, 2026
**Maintainer**: Argos Team

## Quick Reference

| Symptom | Likely Cause | Quick Fix | Documentation |
|---------|--------------|-----------|---------------|
| Workflow fails, jobs pass | Workflow configuration | Check required checks | [Section 1.1](#11-workflow-fails-but-jobs-pass) |
| macOS tests fail | Platform-specific code | Review platform markers | [Section 2.1](#21-macos-specific-failures) |
| Windows jobs slow | Missing cache | Enable caching | [Section 3.1](#31-slow-windows-jobs) |
| Tests flaky | Race conditions | Add markers/retries | [Section 4.1](#41-flaky-tests) |

---

## 1. Workflow-Level Issues

### 1.1 Workflow Fails But Jobs Pass

**Symptoms**:
- ✓ All jobs show green checkmarks
- ✗ Overall workflow marked as failed
- No obvious error in job logs

**Possible Causes**:

1. **Required Status Checks Not Met**
   - Branch protection rules require specific checks
   - Some checks are not configured in workflow

2. **Artifact Upload/Download Failures**
   - Jobs depend on artifacts from previous jobs
   - Artifact retention policy expired

3. **Workflow Approval Gates**
   - Manual approval required but not granted
   - Environment protection rules blocking

**Diagnostic Steps**:

```bash
# 1. Get detailed workflow info
scout ci show --run-id <run-id> --verbose

# 2. Check job statuses
scout ci show --run-id <run-id> --jobs

# 3. Download full logs
scout ci download --run-id <run-id> --output ./logs/<run-id>

# 4. Search for errors
grep -r "error\|failed\|Error\|FAILED" ./logs/<run-id>/
```

**Solutions**:

1. **Check GitHub Settings**:
   - Go to repository → Settings → Branches
   - Review branch protection rules
   - Verify required status checks match workflow job names

2. **Review Workflow YAML**:
   ```yaml
   # Ensure all jobs are in workflow
   jobs:
     test-ubuntu:
       # ...
     test-windows:
       # ...
     test-macos:
       # ...

   # Check for conditional steps that might skip
   - name: Some Step
     if: github.event_name == 'push'  # Might skip on PR
   ```

3. **Verify Artifact Dependencies**:
   ```yaml
   - uses: actions/upload-artifact@v3
     with:
       name: test-results
       retention-days: 7  # Check retention
   ```

### 1.2 Workflow Cancelled Unexpectedly

**Symptoms**:
- Workflow shows "cancelled" status
- No manual cancellation by user

**Possible Causes**:
- Timeout (default 6 hours)
- Concurrent workflow cancellation
- Runner out of resources

**Solutions**:

1. **Check Workflow Configuration**:
   ```yaml
   jobs:
     test:
       timeout-minutes: 30  # Set explicit timeout
       runs-on: ubuntu-latest
   ```

2. **Review Concurrency Settings**:
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true  # May cancel previous runs
   ```

---

## 2. Platform-Specific Issues

### 2.1 macOS-Specific Failures

**Current Status**: 80% success rate (1 failing job)

**Common Issues**:

#### 2.1.1 File System Case Sensitivity

**Problem**: macOS uses case-insensitive file system by default.

**Example**:
```python
# Works on Linux, fails on macOS if file is named "MyFile.py"
from myfile import something
```

**Solution**:
- Always use exact case in imports
- Add test for case sensitivity:
  ```python
  @pytest.mark.macos
  def test_case_sensitive_imports():
      # Test that imports work with exact case
      pass
  ```

#### 2.1.2 Path Separators

**Problem**: Path construction differs between platforms.

**Bad**:
```python
path = "tests/test_file.py"  # Hard-coded separator
```

**Good**:
```python
from pathlib import Path
path = Path("tests") / "test_file.py"
```

#### 2.1.3 Permission Issues

**Problem**: macOS has stricter file permissions.

**Solution**:
```python
import os
import stat

# Ensure file is readable
os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
```

**Reproduction Locally** (if on macOS):
```bash
# Run the failing test
pytest tests/test_specific.py -v

# Or use Anvil
anvil test --platform macos --tests tests/test_specific.py
```

### 2.2 Windows-Specific Issues

**Current Status**: 100% success rate, but 4.8x slower than Ubuntu

#### 2.2.1 Slow Dependency Installation

**Problem**: Windows pip installs take longer.

**Solution**: Enable caching
```yaml
- name: Cache pip
  uses: actions/cache@v3
  with:
    path: ~\AppData\Local\pip\Cache
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

#### 2.2.2 Path Length Limitations

**Problem**: Windows has 260-character path limit.

**Solution**:
- Keep test file paths short
- Enable long paths in Git:
  ```bash
  git config --system core.longpaths true
  ```

#### 2.2.3 Line Ending Differences

**Problem**: CRLF vs LF line endings.

**Solution**:
- Configure `.gitattributes`:
  ```
  * text=auto
  *.py text eol=lf
  *.sh text eol=lf
  ```

### 2.3 Ubuntu/Linux Issues

**Current Status**: 100% success rate ✅

No known issues. Ubuntu is the most stable platform.

---

## 3. Performance Issues

### 3.1 Slow Windows Jobs

**Current**: 552s average (4.8x slower than Ubuntu)

**Investigation Steps**:

1. **Download job logs**:
   ```bash
   scout ci download --job-id <windows-job-id> --output ./logs/windows
   ```

2. **Analyze step timings**:
   ```bash
   # Look for slow steps in logs
   grep "##\[group\]" ./logs/windows/*.log
   grep "took" ./logs/windows/*.log
   ```

3. **Common Bottlenecks**:
   - Dependency installation (pip install)
   - Test execution
   - Build/compilation steps

**Optimization Strategies**:

#### 3.1.1 Enable Caching
```yaml
- name: Cache Python dependencies
  uses: actions/cache@v3
  with:
    path: ~\AppData\Local\pip\Cache
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

#### 3.1.2 Parallelize Tests
```yaml
strategy:
  matrix:
    test-group: [unit, integration, e2e]

steps:
  - name: Run tests
    run: pytest tests/${{ matrix.test-group }}
```

#### 3.1.3 Use Faster Runners
```yaml
runs-on: windows-latest  # Default
runs-on: windows-2022    # Specific version
# Consider GitHub-hosted larger runners (paid)
```

### 3.2 Overall Workflow Duration

**Target**: < 10 minutes per workflow

**Strategies**:

1. **Parallel Jobs**:
   ```yaml
   jobs:
     test-ubuntu:
       # Runs in parallel
     test-windows:
       # Runs in parallel
     test-macos:
       # Runs in parallel
   ```

2. **Skip Redundant Steps**:
   ```yaml
   - name: Run linting
     if: matrix.os == 'ubuntu-latest'  # Only on one platform
     run: flake8 .
   ```

3. **Selective Test Execution** (future):
   ```bash
   # Use Lens to identify tests to run
   anvil test --rule quick-check  # Only critical tests
   ```

---

## 4. Test-Specific Issues

### 4.1 Flaky Tests

**Current**: 0 detected (good!)

**Prevention Strategies**:

1. **Mark Platform-Specific Tests**:
   ```python
   @pytest.mark.linux
   def test_linux_only():
       pass

   @pytest.mark.skipif(platform.system() == "Windows", reason="Linux only")
   def test_symlinks():
       pass
   ```

2. **Use Test Retries** (for known flaky tests):
   ```python
   @pytest.mark.flaky(reruns=3)
   def test_sometimes_fails():
       pass
   ```

3. **Add Timeouts**:
   ```python
   @pytest.mark.timeout(30)  # Fail after 30 seconds
   def test_slow_operation():
       pass
   ```

**Detection**:
```bash
# Monitor flakiness over time
lens report flaky-tests --window 30

# Analyze specific test
scout ci analyze --test "tests/test_file.py::test_name"
```

### 4.2 Test Discovery Issues

**Problem**: Tests not found or not running.

**Diagnostic**:
```bash
# Check test discovery patterns in pytest.ini
cat pytest.ini

# Manually discover tests
pytest --collect-only

# Verbose discovery
pytest --collect-only -v
```

**Solution**:
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

## 5. Environment Issues

### 5.1 Dependency Conflicts

**Symptoms**:
- Import errors
- Version conflicts
- "No module named X"

**Diagnostic**:
```bash
# Check installed packages in CI
pip list

# Compare with requirements.txt
pip freeze > ci-packages.txt
diff requirements.txt ci-packages.txt
```

**Solutions**:

1. **Pin Dependency Versions**:
   ```txt
   # requirements.txt
   sqlalchemy==2.0.25  # Exact version
   pytest>=7.0.0,<8.0.0  # Version range
   ```

2. **Use Virtual Environments**:
   ```yaml
   - name: Create venv
     run: python -m venv venv

   - name: Activate venv (Windows)
     run: .\venv\Scripts\activate

   - name: Activate venv (Unix)
     run: source venv/bin/activate
   ```

3. **Update Dependencies**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

### 5.2 Python Version Issues

**Problem**: Code works on one Python version but not another.

**Solution**:
```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']

steps:
  - uses: actions/setup-python@v4
    with:
      python-version: ${{ matrix.python-version }}
```

**Test locally**:
```bash
# Use pyenv or conda
pyenv install 3.8.0
pyenv local 3.8.0
python --version
pytest
```

---

## 6. Debugging Techniques

### 6.1 Enable Debug Logging

**In Workflow**:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

**In Tests**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 6.2 SSH into Runner (Advanced)

**Using tmate**:
```yaml
- name: Setup tmate session
  if: failure()
  uses: mxschmitt/action-tmate@v3
  timeout-minutes: 30
```

### 6.3 Local Reproduction

**Full CI Environment**:
```bash
# Use act (GitHub Actions locally)
act -j test-ubuntu

# Or Docker
docker run -it ubuntu:latest
# Then manually run CI steps
```

**Anvil Cross-Platform Testing** (Phase 0.2 - skipped):
```bash
# Would run tests in Docker
anvil test cross-platform --environment ubuntu-20.04 --tests tests/
```

---

## 7. Common Error Messages

### 7.1 "No module named 'X'"

**Cause**: Dependency not installed or wrong Python path.

**Fix**:
```bash
pip install -r requirements.txt
```

### 7.2 "Permission denied"

**Cause**: File permissions issue.

**Fix**:
```bash
chmod +x script.sh
```

### 7.3 "Connection timeout"

**Cause**: Network issues, slow dependency download.

**Fix**:
```yaml
- name: Install dependencies
  run: pip install --timeout=300 -r requirements.txt
```

### 7.4 "Test collection failed"

**Cause**: Syntax error or import error in tests.

**Fix**:
```bash
# Check syntax
python -m py_compile tests/test_file.py

# Try importing
python -c "import tests.test_file"
```

---

## 8. Emergency Procedures

### 8.1 All CI Runs Failing

1. **Check GitHub Status**: https://www.githubstatus.com/
2. **Review Recent Changes**:
   ```bash
   git log --oneline -10
   ```
3. **Revert Last Change** (if suspicious):
   ```bash
   git revert HEAD
   git push
   ```
4. **Re-run Failed Jobs**: Click "Re-run failed jobs" in GitHub UI

### 8.2 CI Blocking Urgent Release

1. **Identify Critical Failures**:
   ```bash
   lens analyze --window 1  # Last 24 hours
   ```
2. **Create Hotfix Branch**:
   ```bash
   git checkout -b hotfix/ci-bypass
   ```
3. **Document in PR**: Why bypass is needed
4. **Manual Testing**: Run tests locally
5. **Get Approval**: Require 2+ reviews

---

## 9. Best Practices

### 9.1 Preventive Measures

✅ **DO**:
- Run tests locally before pushing
- Use pre-commit hooks
- Keep dependencies updated
- Monitor CI health weekly
- Document known issues

❌ **DON'T**:
- Commit without testing
- Ignore failing tests
- Skip CI checks
- Hard-code paths
- Mix platform-specific code without markers

### 9.2 CI Hygiene

**Daily**:
- Check CI status for your PRs
- Fix failures immediately

**Weekly**:
- Review CI health report:
  ```bash
  lens analyze --window 7
  ```
- Update this troubleshooting guide

**Monthly**:
- Analyze trends:
  ```bash
  lens report ci-health --format html --output monthly-report.html --window 30
  ```
- Update dependency versions
- Review and close old issues

---

## 10. Tool Reference

### Scout (CI Data Collector)

```bash
# Fetch CI data
scout ci fetch --workflow "Anvil Tests" --limit 30

# Show specific run
scout ci show --run-id <run-id> --verbose

# Download logs
scout ci download --run-id <run-id> --output ./logs

# Compare local vs CI
scout ci anvil-compare --local-run <id> --ci-run <id>

# Find CI-specific failures
scout ci ci-failures --days 30
```

### Lens (CI Analytics)

```bash
# Quick health check
lens analyze --window 30

# Platform breakdown
lens report platform-breakdown --window 30

# Flaky tests
lens report flaky-tests --window 30

# Generate HTML report
lens report ci-health --format html --output report.html
```

### Anvil (Validation Framework)

```bash
# Run tests
anvil test --tests tests/

# Cross-platform (when Docker available)
anvil test cross-platform --environment ubuntu-20.04

# Reproduce CI failure
scout ci reproduce --run-id <id> --job-id <id>
```

---

## 11. Getting Help

### Internal Resources

1. **Documentation**:
   - [CI Failure Analysis](./ci-failure-analysis.md)
   - [Platform Notes](./PLATFORM-NOTES.md)
   - [CI Runbook](./CI-RUNBOOK.md)

2. **Team Contacts**:
   - CI/CD Lead: [Name]
   - Platform Specialists:
     - Linux: [Name]
     - Windows: [Name]
     - macOS: [Name]

### External Resources

1. **GitHub Actions**:
   - [Official Documentation](https://docs.github.com/en/actions)
   - [Community Forum](https://github.community/c/code-to-cloud/52)

2. **pytest**:
   - [Documentation](https://docs.pytest.org/)
   - [Platform Markers](https://docs.pytest.org/en/stable/how-to/mark.html)

---

## 12. Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-02 | Initial guide created | GitHub Copilot |
| | Added sections 1-11 | |
| | Based on 13.3% success rate analysis | |

---

**Need to add to this guide?** Submit a PR with updates!
