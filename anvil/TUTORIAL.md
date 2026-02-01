# Anvil Tutorial

A step-by-step guide to using Anvil for code quality validation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Tutorial 1: Basic Python Project](#tutorial-1-basic-python-project)
3. [Tutorial 2: Git Hook Integration](#tutorial-2-git-hook-integration)
4. [Tutorial 3: Advanced Configuration](#tutorial-3-advanced-configuration)
5. [Tutorial 4: Statistics and Trends](#tutorial-4-statistics-and-trends)
6. [Tutorial 5: Custom Validators](#tutorial-5-custom-validators)
7. [Tutorial 6: CI/CD Integration](#tutorial-6-cicd-integration)

## Getting Started

### Prerequisites

Before starting this tutorial, ensure you have:

- Python 3.8 or higher installed
- Git installed (for hook tutorials)
- Basic knowledge of Python and command line

### Installation

Install Anvil from source:

```bash
cd anvil
pip install -e .
```

Verify the installation:

```bash
anvil --version
anvil list
```

Expected output:
```
Anvil version 1.0.0
Available validators: flake8, black, isort, pylint, pytest, ...
```

## Tutorial 1: Basic Python Project

In this tutorial, you'll set up Anvil for a simple Python project.

### Step 1: Create a Sample Project

```bash
# Create project directory
mkdir my-python-project
cd my-python-project

# Initialize git
git init

# Create a simple Python file
cat > calculator.py << 'EOF'
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
EOF
```

### Step 2: Initialize Anvil Configuration

```bash
anvil config init
```

This creates `anvil.toml`:

```toml
[project]
name = "my-python-project"
languages = ["python"]

[python]
enabled = true

[python.flake8]
enabled = true
max_line_length = 100

[python.black]
enabled = true
line_length = 100
```

### Step 3: Install Python Validators

```bash
pip install flake8 black isort pytest pytest-cov
```

### Step 4: Run First Validation

```bash
anvil check
```

Expected output:
```
╔═══════════════════════════════════════╗
║      Anvil - Code Quality Gate       ║
╚═══════════════════════════════════════╝

Running validators...

✓ flake8: PASSED (0 errors, 0 warnings)
✓ black: PASSED (all files formatted)

All validators passed!
```

### Step 5: Fix Code Issues

Let's add some intentional issues:

```python
# calculator.py with issues
import os  # Unused import

def add(a,b):  # Missing spaces
    return a+b  # Missing spaces

def subtract( a, b ):  # Extra spaces
    return a - b

def multiply(a, b):
    x = 1  # Unused variable
    return a * b
```

Run validation:

```bash
anvil check
```

Output will show errors:
```
✗ flake8: FAILED (3 errors, 1 warning)
  calculator.py:1:1: F401 'os' imported but unused
  calculator.py:3:13: E231 missing whitespace after ','
  ...
```

Fix the issues:

```bash
# Auto-fix with black
black calculator.py

# Remove unused imports
autoflake --remove-all-unused-imports -i calculator.py
```

Validate again:

```bash
anvil check
```

### Step 6: Add Tests

Create a test file:

```python
# test_calculator.py
from calculator import add, subtract, multiply, divide
import pytest


def test_add():
    """Test addition."""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    """Test subtraction."""
    assert subtract(5, 3) == 2
    assert subtract(0, 1) == -1


def test_multiply():
    """Test multiplication."""
    assert multiply(2, 3) == 6
    assert multiply(-2, 3) == -6


def test_divide():
    """Test division."""
    assert divide(6, 2) == 3
    assert divide(5, 2) == 2.5

    with pytest.raises(ValueError):
        divide(1, 0)
```

Enable pytest in configuration:

```toml
[python.pytest]
enabled = true
min_coverage = 90.0
```

Run validation with tests:

```bash
anvil check
```

### Step 7: Incremental Validation

Make a small change to one file:

```bash
# Edit calculator.py
echo "" >> calculator.py
```

Run incremental validation:

```bash
anvil check --incremental
```

Only validates changed files (faster!).

## Tutorial 2: Git Hook Integration

Set up automatic validation on commits.

### Step 1: Install Pre-Commit Hook

```bash
anvil install-hooks
```

This creates `.git/hooks/pre-commit`.

### Step 2: Test the Hook

Make a change with an intentional error:

```python
# calculator.py
def add(a, b):
    return a+b  # Missing spaces
```

Try to commit:

```bash
git add calculator.py
git commit -m "Update add function"
```

Hook runs and prevents commit:
```
Running Anvil pre-commit hook...

✗ flake8: FAILED (1 error)
  calculator.py:2:15: E225 missing whitespace around operator

Commit rejected. Fix issues and try again.
```

### Step 3: Fix and Commit

```bash
# Fix the issue
black calculator.py

# Commit again
git add calculator.py
git commit -m "Update add function"
```

Hook passes, commit succeeds:
```
Running Anvil pre-commit hook...

✓ All validators passed!

[main abc123] Update add function
 1 file changed, 1 insertion(+)
```

### Step 4: Bypass Hook (When Needed)

For emergency commits:

```bash
git commit --no-verify -m "WIP: Work in progress"
```

Or use bypass keyword:

```bash
git commit -m "[skip-anvil] Temporary changes"
```

### Step 5: Uninstall Hook

To remove the hook:

```bash
anvil install-hooks --uninstall
```

## Tutorial 3: Advanced Configuration

Customize Anvil for your project's needs.

### Step 1: Configure Multiple Validators

Edit `anvil.toml`:

```toml
[project]
name = "my-project"
languages = ["python"]

[validation]
mode = "full"
parallel = true
max_workers = 4

[python.flake8]
enabled = true
max_line_length = 100
max_complexity = 10
exclude = ["build/", "__pycache__/"]
ignore = ["E203", "W503"]

[python.black]
enabled = true
line_length = 100
check = true

[python.isort]
enabled = true
line_length = 100
profile = "black"

[python.pylint]
enabled = true
min_score = 8.0
disable = ["C0111", "R0903"]

[python.pytest]
enabled = true
min_coverage = 90.0
test_paths = ["tests/"]
```

### Step 2: Per-Validator Configuration

Create `.flake8`:

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
per-file-ignores =
    __init__.py:F401
    tests/*:D100,D101,D102
```

Create `.pylintrc`:

```ini
[MESSAGES CONTROL]
disable=C0111,R0903

[FORMAT]
max-line-length=100
```

### Step 3: Validate Configuration

```bash
anvil config validate
```

Shows any configuration errors.

### Step 4: View Effective Configuration

```bash
anvil config show
```

Displays merged configuration from all sources.

### Step 5: Run Specific Validators

```bash
# Only flake8
anvil check --validator flake8

# Multiple validators
anvil check --validator flake8 --validator black

# Language-specific
anvil check --language python
```

## Tutorial 4: Statistics and Trends

Track validation history and identify patterns.

### Step 1: Enable Statistics

Edit `anvil.toml`:

```toml
[statistics]
enabled = true
database = ".anvil/stats.db"
retention_days = 90

[smart-filtering]
enabled = true
skip_success_threshold = 0.95
prioritize_flaky = true
```

### Step 2: Build History

Run validation multiple times:

```bash
# Make changes and validate
for i in {1..10}; do
    echo "# Build $i" >> calculator.py
    anvil check
    git add calculator.py
    git commit -m "Build $i"
done
```

### Step 3: View Statistics

```bash
# Summary report
anvil stats report
```

Output:
```
Validation Statistics Report
============================

Total Runs: 10
Success Rate: 90%
Average Duration: 2.5s

Validators:
  flake8: 10 runs, 100% success
  black: 10 runs, 100% success
  pytest: 10 runs, 80% success (2 failures)
```

### Step 4: Find Flaky Tests

```bash
anvil stats flaky
```

Output:
```
Flaky Tests (50-90% success rate):
  test_edge_case: 6/10 passed (60%)
  test_concurrent: 7/10 passed (70%)
```

### Step 5: Identify Problem Files

```bash
anvil stats problem-files
```

Output:
```
Files with Most Errors:
  calculator.py: 5 errors in last 30 days
  utils.py: 3 errors in last 30 days
```

### Step 6: View Trends

```bash
anvil stats trends --validator pylint
```

Output:
```
Pylint Score Trend (last 10 runs):
  Run 1: 7.5
  Run 2: 7.8
  Run 3: 8.1
  ...
  Run 10: 9.2 ✓ (improving)
```

### Step 7: Export Statistics

```bash
# Export to JSON
anvil stats export --format json --output stats.json

# Export to CSV
anvil stats export --format csv --output stats.csv
```

## Tutorial 5: Custom Validators

Create a custom validator for project-specific checks.

### Step 1: Create Validator Structure

```bash
mkdir -p custom_validators
cd custom_validators
```

### Step 2: Implement Custom Validator

Create `copyright_validator.py`:

```python
"""Custom validator to check copyright headers."""

from anvil.validators.base import ValidatorBase
from anvil.models.validation_result import ValidationResult, Issue
from typing import List
import re


class CopyrightValidator(ValidatorBase):
    """
    Validates copyright headers in source files.

    Checks that each file has a copyright notice at the top.
    """

    def __init__(self, config: dict):
        """
        Initialize copyright validator.

        Args:
            config: Configuration from anvil.toml
        """
        super().__init__(config)
        self.required_year = config.get("required_year", "2024")
        self.required_owner = config.get("required_owner", "MyCompany")

    @property
    def name(self) -> str:
        """Get validator name."""
        return "copyright"

    @property
    def language(self) -> str:
        """Get target language."""
        return "python"

    def is_available(self) -> bool:
        """Check if validator is available (always true)."""
        return True

    def validate(self, files: List[str]) -> ValidationResult:
        """
        Validate copyright headers.

        Args:
            files: List of files to check

        Returns:
            ValidationResult with issues
        """
        issues = []

        for file_path in files:
            if not file_path.endswith(".py"):
                continue

            with open(file_path, 'r') as f:
                content = f.read()

            # Check for copyright
            pattern = rf"# Copyright.*{self.required_year}.*{self.required_owner}"
            if not re.search(pattern, content, re.IGNORECASE):
                issues.append(Issue(
                    file=file_path,
                    line=1,
                    column=0,
                    severity="warning",
                    message=f"Missing copyright header ({self.required_year} {self.required_owner})",
                    code="COPYRIGHT001",
                    source="copyright",
                    suggestion=f"Add: # Copyright {self.required_year} {self.required_owner}"
                ))

        return ValidationResult(
            validator="copyright",
            passed=(len(issues) == 0),
            issues=issues,
            errors_count=0,
            warnings_count=len(issues),
            files_checked=len(files),
            duration=0.0,
            metadata={}
        )
```

### Step 3: Register Validator

Edit `anvil/validators/registry.py`:

```python
from custom_validators.copyright_validator import CopyrightValidator

PYTHON_VALIDATORS = {
    "flake8": Flake8Validator,
    "black": BlackValidator,
    "copyright": CopyrightValidator,  # Add custom validator
    # ...
}
```

### Step 4: Configure Custom Validator

Edit `anvil.toml`:

```toml
[python.copyright]
enabled = true
required_year = "2024"
required_owner = "MyCompany"
```

### Step 5: Run Custom Validator

```bash
anvil check --validator copyright
```

### Step 6: Add Copyright Headers

```python
# calculator.py
# Copyright 2024 MyCompany
# All rights reserved.

def add(a, b):
    """Add two numbers."""
    return a + b

# ...
```

### Step 7: Validate Again

```bash
anvil check --validator copyright
```

Now passes!

## Tutorial 6: CI/CD Integration

Integrate Anvil into your continuous integration pipeline.

### Step 1: GitHub Actions Setup

Create `.github/workflows/quality.yml`:

```yaml
name: Code Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  anvil-validation:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for incremental mode

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -e ./anvil
          pip install flake8 black isort pylint pytest pytest-cov

      - name: Run Anvil (Full)
        if: github.ref == 'refs/heads/main'
        run: anvil check --verbose

      - name: Run Anvil (Incremental)
        if: github.event_name == 'pull_request'
        run: anvil check --incremental --verbose

      - name: Export Statistics
        if: always()
        run: anvil stats export --format json --output anvil-stats.json

      - name: Upload Statistics
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: anvil-statistics
          path: anvil-stats.json

      - name: Comment on PR
        if: failure() && github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Anvil quality gate failed. Please fix issues before merging.'
            })
```

### Step 2: GitLab CI Setup

Create `.gitlab-ci.yml`:

```yaml
stages:
  - quality

anvil-check:
  stage: quality
  image: python:3.11

  before_script:
    - pip install -e ./anvil
    - pip install flake8 black isort pylint pytest pytest-cov

  script:
    - |
      if [ "$CI_MERGE_REQUEST_IID" ]; then
        anvil check --incremental --verbose
      else
        anvil check --verbose
      fi

  after_script:
    - anvil stats export --format json --output anvil-stats.json

  artifacts:
    paths:
      - anvil-stats.json
    when: always

  only:
    - merge_requests
    - main
```

### Step 3: Jenkins Pipeline

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -e ./anvil'
                sh 'pip install flake8 black isort pylint pytest pytest-cov'
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    if (env.CHANGE_ID) {
                        sh 'anvil check --incremental --verbose'
                    } else {
                        sh 'anvil check --verbose'
                    }
                }
            }
        }

        stage('Export Stats') {
            when {
                expression { return true }
            }
            steps {
                sh 'anvil stats export --format json --output anvil-stats.json'
                archiveArtifacts artifacts: 'anvil-stats.json', allowEmptyArchive: true
            }
        }
    }

    post {
        failure {
            echo 'Quality gate failed!'
        }
        success {
            echo 'Quality gate passed!'
        }
    }
}
```

### Step 4: Test CI Locally

Use `act` to test GitHub Actions locally:

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow locally
act push
```

### Step 5: Monitor CI Results

Check CI output for quality metrics:

```
Running Anvil validation...

✓ flake8: PASSED (0 errors)
✓ black: PASSED (all formatted)
✓ pytest: PASSED (42 tests, 95% coverage)

Quality gate: PASSED ✓
```

## Next Steps

### Continue Learning

1. **Advanced Topics**:
   - Multi-language projects (Python + C++)
   - Custom parsers for proprietary tools
   - Advanced statistics queries
   - Performance optimization

2. **Best Practices**:
   - Team configuration standards
   - Graduated quality thresholds
   - Monitoring and dashboards
   - Integration with code review tools

3. **Reference Documentation**:
   - [User Guide](docs/USER_GUIDE.md): Complete feature reference
   - [API Documentation](docs/API.md): Extending Anvil
   - [Configuration Reference](docs/CONFIGURATION.md): All options
   - [Troubleshooting](docs/TROUBLESHOOTING.md): Common issues

### Practice Projects

1. **Simple Python Library**: Apply Anvil to a small Python package
2. **Mixed Project**: Python backend + C++ performance code
3. **Legacy Codebase**: Gradually improve quality metrics
4. **CI/CD Pipeline**: Full integration with testing and deployment

## Conclusion

You've learned how to:

✓ Set up Anvil for Python projects
✓ Configure multiple validators
✓ Install and use git hooks
✓ Track statistics and trends
✓ Create custom validators
✓ Integrate with CI/CD pipelines

Anvil helps maintain code quality consistently across your projects. Start with basic validation, then add advanced features as needed.

Happy coding with Anvil! 🔨
