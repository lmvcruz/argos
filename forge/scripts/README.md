# Development Scripts

This folder contains utility scripts to help maintain code quality and development workflows for the Forge project.

## Scripts Overview

### `pre-commit-check.py`

A Python script that runs the same code quality checks as the CI pipeline, allowing you to catch issues locally before pushing to GitHub.

**What it checks:**
- **Syntax errors**: Uses flake8 to check for Python syntax errors and undefined names (blocking)
- **Code style**: Uses flake8 to check PEP 8 compliance (warnings only, non-blocking)
- **Code formatting**: Uses black to check if code is properly formatted (blocking)
- **Tests**: Runs pytest test suite to ensure all tests pass (blocking)

**Usage:**
```bash
# Run from the forge directory
python scripts/pre-commit-check.py
```

**Exit codes:**
- `0`: All critical checks passed (syntax and formatting are correct)
- `1`: Critical checks failed (syntax errors or formatting issues found)

**When to use:**
- Before committing changes to catch issues early
- After making code changes to verify quality
- As part of your development workflow

**Features:**
- Works on both Windows and Unix-like systems
- Auto-detects project root whether run from scripts/ or .git/hooks/
- Provides clear, colorful output with fix suggestions
- Runs the same checks as GitHub Actions CI pipeline

---

### `setup-git-hooks.py`

A Python script that installs the pre-commit checker as a git hook, so it runs automatically before each commit.

**What it does:**
1. Copies `pre-commit-check.py` to `.git/hooks/pre-commit`
2. Makes the hook executable (on Unix-like systems)
3. Creates a Windows `.bat` wrapper for git integration

**Usage:**
```bash
# Run from the forge directory
python scripts/setup-git-hooks.py
```

**After installation:**
- The pre-commit checks will run automatically before each `git commit`
- Checks include: syntax errors, code style, formatting, and tests
- If checks fail, the commit will be blocked until issues are fixed
- You can bypass the hook with `git commit --no-verify` (not recommended)

**Platform support:**
- **Linux/Mac**: Creates executable shell script
- **Windows**: Creates both the hook file and a `.bat` wrapper

**Note:** In some environments (like VS Code's integrated git), hooks may not execute automatically. In such cases, you can run `python scripts/pre-commit-check.py` manually before committing.

---

## Quick Start Guide

### First Time Setup

1. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) Install git hook:**
   ```bash
   python scripts/setup-git-hooks.py
   ```

### Regular Workflow

**Before committing changes:**
```bash
# Check your code
python scripts/pre-commit-check.py

# If formatting issues are found, auto-fix them:
python -m black .

# Run checks again to confirm
python scripts/pre-commit-check.py

# Commit when all checks pass
git commit -m "Your commit message"
```

### If You See Errors

**Syntax errors (flake8):**
- These must be fixed manually
- The error message shows the file, line, and issue
- Common issues: undefined variables, syntax mistakes

**Formatting issues (black):**
- Auto-fix with: `python -m black .`
- Or fix manually following the diff shown

**Test failures (pytest):**
- Review the test output to identify failing tests
- Fix the code or update tests as needed
- All tests must pass before committing

**Style warnings (flake8):**
- Non-blocking, but good to address
- Follow PEP 8 guidelines
- Can be ignored if justified

---

## Troubleshooting

### "No module named flake8/black"
Install the development dependencies:
```bash
pip install -r requirements.txt
```

### Git hook not running automatically
Some git clients (like VS Code) may not execute hooks. Run the check manually:
```bash
python scripts/pre-commit-check.py
```

### Bypass hook for emergency commit
Only use when absolutely necessary:
```bash
git commit --no-verify -m "Emergency fix"
```

---

## Integration with CI/CD

These scripts mirror the checks performed by the GitHub Actions CI pipeline defined in `.github/workflows/forge-tests.yml`. Running them locally helps you:

- Catch issues before CI fails
- Reduce unnecessary commits fixing formatting
- Maintain consistent code quality
- Save CI/CD resources and time

---

## Contributing

When modifying these scripts:
1. Ensure they work on both Windows and Unix systems
2. Keep output clear and actionable
3. Match the CI pipeline checks exactly
4. Test with intentionally bad code to verify detection
