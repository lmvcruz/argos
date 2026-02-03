# Code Quality Quick Reference

**Quick Guide for Using Phase 3 Code Quality Features**

---

## 🚀 Quick Start

### Run Quality Checks with Tests

```bash
cd d:\playground\argos

# Run tests with automatic quality checks
python scripts\run_local_tests.py forge/tests/

# The system automatically runs:
# 1. pytest tests
# 2. Coverage analysis (if --cov specified)
# 3. flake8 linting
# 4. black formatting check
# 5. isort import check
```

### Generate Quality Report

```bash
# HTML report (opens in browser)
python scripts\generate_quality_report.py --format html
start quality-report.html

# Markdown report (for docs)
python scripts\generate_quality_report.py --format markdown

# Both formats
python scripts\generate_quality_report.py --format both
```

---

## 📊 Common Commands

### Filter by Space

```bash
# Local development only
python scripts\generate_quality_report.py --space local --format html

# CI results only
python scripts\generate_quality_report.py --space ci --format html
```

### Filter by Validator

```bash
# flake8 only
python scripts\generate_quality_report.py --validator flake8 --format html

# black only
python scripts\generate_quality_report.py --validator black --format html

# isort only
python scripts\generate_quality_report.py --validator isort --format html
```

### Time Windows

```bash
# Last 7 days
python scripts\generate_quality_report.py --window 7 --format html

# Last 30 days
python scripts\generate_quality_report.py --window 30 --format html

# All time (default)
python scripts\generate_quality_report.py --format html
```

---

## 🗄️ Database Queries

### Python API

```python
from anvil.storage.execution_schema import ExecutionDatabase

# Open database
db = ExecutionDatabase(".anvil/history.db")

# Get recent violations
violations = db.get_lint_violations(
    validator="flake8",
    severity="ERROR",
    limit=20
)

for v in violations:
    print(f"{v.file_path}:{v.line_number} [{v.code}] {v.message}")

# Get quality summaries
summaries = db.get_lint_summary(space="local", limit=10)

for s in summaries:
    print(f"{s.timestamp}: {s.validator} found {s.total_violations} violations")

db.close()
```

### Direct SQL

```bash
# Connect to database
sqlite3 .anvil/history.db

# Show all tables
.tables

# Get violation counts by code
SELECT code, COUNT(*) as count
FROM lint_violations
GROUP BY code
ORDER BY count DESC
LIMIT 10;

# Get files with most violations
SELECT file_path, COUNT(*) as count
FROM lint_violations
GROUP BY file_path
ORDER BY count DESC
LIMIT 10;

# Get quality trend
SELECT timestamp, total_violations, validator
FROM lint_summary
ORDER BY timestamp DESC
LIMIT 20;
```

---

## 🎯 Common Workflows

### Daily Development

```bash
# 1. Run tests with quality checks
python scripts\run_local_tests.py forge/tests/ --cov=forge --cov-report=xml

# 2. Review quality summary in terminal output

# 3. Generate detailed report if issues found
python scripts\generate_quality_report.py --format html
```

### Fix Quality Issues

```bash
# 1. Generate report to identify issues
python scripts\generate_quality_report.py --validator black --format html

# 2. Auto-fix black formatting
black forge/ anvil/ scout/

# 3. Auto-fix isort import order
isort forge/ anvil/ scout/

# 4. Run tests again to verify fixes
python scripts\run_local_tests.py forge/tests/

# 5. Confirm improvement in report
python scripts\generate_quality_report.py --format html
```

### Quality Trend Analysis

```bash
# 1. Generate 30-day trend report
python scripts\generate_quality_report.py --window 30 --format both

# 2. Review markdown report
cat quality-report.md

# 3. Compare with baseline
cat docs/phase-3-baseline-quality.md
```

---

## 🔍 Analyzing Results

### Understanding Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| **ERROR** | Critical issues (E-codes, F-codes) | Fix immediately |
| **WARNING** | Style/best practice violations (W-codes, BLACK, ISORT) | Fix before commit |
| **INFO** | Documentation, type hints (D-codes, I-codes) | Optional improvement |

### Common Violation Codes

#### flake8

| Code | Description | Fix |
|------|-------------|-----|
| E501 | Line too long | Break line or adjust line length limit |
| W503 | Line break before operator | Reformat or disable rule |
| F401 | Unused import | Remove import |
| E722 | Bare except | Specify exception type |
| C901 | Too complex | Refactor function |

#### black

| Code | Description | Fix |
|------|-------------|-----|
| BLACK001 | Would reformat | Run `black file.py` |

#### isort

| Code | Description | Fix |
|------|-------------|-----|
| ISORT001 | Imports incorrectly sorted | Run `isort file.py` |

---

## 📈 Tracking Progress

### Baseline Comparison

```python
from anvil.storage.execution_schema import ExecutionDatabase

db = ExecutionDatabase(".anvil/history.db")

# Get first and latest summaries
all_summaries = db.get_lint_summary(validator="flake8", limit=100)

if len(all_summaries) >= 2:
    latest = all_summaries[0]
    baseline = all_summaries[-1]

    improvement = baseline.total_violations - latest.total_violations
    print(f"Improvement: {improvement} fewer violations")
    print(f"  Baseline: {baseline.total_violations}")
    print(f"  Current: {latest.total_violations}")
    print(f"  Reduction: {improvement / baseline.total_violations * 100:.1f}%")

db.close()
```

### Set Quality Goals

```python
# Target: 0 errors, <100 warnings

from anvil.storage.execution_schema import ExecutionDatabase

db = ExecutionDatabase(".anvil/history.db")
summaries = db.get_lint_summary(space="local", limit=1)

if summaries:
    s = summaries[0]
    print(f"Current: {s.errors} errors, {s.warnings} warnings")

    if s.errors > 0:
        print(f"❌ Goal not met: {s.errors} errors remaining")
    elif s.warnings > 100:
        print(f"⚠️  Warning threshold exceeded: {s.warnings} > 100")
    else:
        print("✅ Quality goals met!")

db.close()
```

---

## 🛠️ Troubleshooting

### No Violations Found

**Issue**: Report shows 0 violations but code has issues

**Solutions**:
1. Check if validators are installed:
   ```bash
   flake8 --version
   black --version
   isort --version
   ```

2. Install missing validators:
   ```bash
   pip install flake8 black isort
   ```

3. Run manual scan to verify:
   ```bash
   flake8 forge/
   black --check forge/
   isort --check forge/
   ```

### Database Empty

**Issue**: `generate_quality_report.py` shows "No quality data found"

**Solutions**:
1. Run tests first:
   ```bash
   python scripts\run_local_tests.py forge/tests/
   ```

2. Check database exists:
   ```bash
   ls .anvil/history.db
   ```

3. Verify database has lint tables:
   ```bash
   python scripts\test_lint_schema.py
   ```

### Report Generation Fails

**Issue**: Error when generating reports

**Solutions**:
1. Check database path:
   ```bash
   python scripts\generate_quality_report.py --db .anvil/history.db --format html
   ```

2. Verify database not corrupted:
   ```bash
   sqlite3 .anvil/history.db "SELECT COUNT(*) FROM lint_violations;"
   ```

3. Regenerate database if needed:
   ```bash
   rm .anvil/history.db
   python scripts\run_local_tests.py forge/tests/
   ```

---

## ⚙️ Configuration

### Customize Validators

Edit `scripts/run_local_tests.py` to modify validator paths:

```python
def run_flake8_scan(project_paths=None):
    if project_paths is None:
        project_paths = ['forge', 'anvil', 'scout']  # Modify here
    # ...
```

### Adjust Severity Mapping

Edit `anvil/parsers/lint_parser.py` to change severity levels:

```python
FLAKE8_SEVERITY_MAP = {
    "E": "ERROR",    # Change to "WARNING" to downgrade
    "W": "WARNING",
    "F": "ERROR",
    # ...
}
```

### Set Quality Thresholds

Create `.quality-thresholds.json`:

```json
{
  "max_errors": 0,
  "max_warnings": 100,
  "max_violations_per_file": 10,
  "target_quality_score": 90
}
```

---

## 📚 Best Practices

### 1. Run Quality Checks Regularly

```bash
# Daily: Before pushing code
python scripts\run_local_tests.py forge/tests/ --cov=forge --cov-report=xml
```

### 2. Fix Issues Incrementally

```bash
# Week 1: Fix all black formatting
black forge/ anvil/ scout/

# Week 2: Fix all isort issues
isort forge/ anvil/ scout/

# Week 3: Fix flake8 errors
# (manual fixes based on report)

# Week 4: Fix flake8 warnings
# (manual fixes based on report)
```

### 3. Track Trends

```bash
# Monthly: Generate trend report
python scripts\generate_quality_report.py --window 30 --format markdown \
  --output docs/quality-report-$(date +%Y-%m).md
```

### 4. Set Up Pre-Commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python scripts/run_local_tests.py forge/tests/
if [ $? -ne 0 ]; then
    echo "❌ Quality checks failed!"
    exit 1
fi
```

### 5. Document Quality Goals

In `README.md`:

```markdown
## Code Quality

**Current Status**:
- Errors: 0
- Warnings: 45
- Quality Score: 95/100

**Goals**:
- Maintain 0 errors
- Reduce warnings to <20
- Achieve 98+ quality score
```

---

## 🎓 Learning Resources

### Understanding Violation Codes

- **flake8**: https://flake8.pycqa.org/en/latest/user/error-codes.html
- **PEP8**: https://pep8.org/
- **black**: https://black.readthedocs.io/

### Code Quality Guides

- **Google Python Style Guide**: https://google.github.io/styleguide/pyguide.html
- **PEP8 Style Guide**: https://www.python.org/dev/peps/pep-0008/
- **Clean Code Principles**: https://gist.github.com/wojteklu/73c6914cc446146b8b533c0988cf8d29

---

## 💡 Tips & Tricks

### Ignore Specific Violations

```python
# Inline ignore (use sparingly)
result = very_long_function_name(arg1, arg2, arg3)  # noqa: E501

# File-level ignore
# flake8: noqa: F401

# Configuration file (.flake8)
[flake8]
ignore = E203, W503
max-line-length = 100
```

### Batch Fix Common Issues

```bash
# Remove unused imports
autoflake --remove-all-unused-imports --in-place --recursive forge/

# Sort imports
isort forge/ anvil/ scout/

# Format code
black forge/ anvil/ scout/
```

### Generate Quality Badge

```python
# Add to README.md
violations = 45
if violations == 0:
    badge = "![Quality](https://img.shields.io/badge/quality-excellent-brightgreen)"
elif violations < 50:
    badge = "![Quality](https://img.shields.io/badge/quality-good-green)"
elif violations < 100:
    badge = "![Quality](https://img.shields.io/badge/quality-fair-yellow)"
else:
    badge = "![Quality](https://img.shields.io/badge/quality-needs%20work-red)"
```

---

**For detailed documentation, see**: [Phase 3 Complete Report](phase-3-complete.md)
