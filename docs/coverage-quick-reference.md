# Phase 2 Coverage Tracking - Quick Reference

## 🚀 Quick Start

### Run Tests with Coverage Tracking

```bash
# Track coverage for a specific test file
python scripts/run_local_tests.py forge/tests/test_models.py --cov=forge --cov-report=xml

# Track coverage for all tests in a directory
python scripts/run_local_tests.py forge/tests/ --cov=forge --cov-report=xml

# Track coverage with verbose output
python scripts/run_local_tests.py forge/tests/ --cov=forge --cov-report=xml -v
```

**What happens**:
1. ✅ Runs pytest with coverage
2. ✅ Stores test results in database
3. ✅ Parses coverage.xml automatically
4. ✅ Stores coverage data in database
5. ✅ Links coverage to same execution ID as tests

### Generate Coverage Reports

```bash
# Generate HTML report (default)
python scripts/generate_coverage_report.py

# Generate Markdown report
python scripts/generate_coverage_report.py --format markdown

# Filter by space (local/ci/all)
python scripts/generate_coverage_report.py --space local

# Filter by time window (last N days)
python scripts/generate_coverage_report.py --window 30

# Custom output file
python scripts/generate_coverage_report.py --output my-coverage-report.html
```

## 📊 Database Queries

### Check Coverage Tables

```bash
python scripts/check_coverage_tables.py
```

**Expected output**:
```
✅ coverage_history
✅ coverage_summary
```

### Query Coverage Programmatically

```python
from anvil.storage.execution_schema import ExecutionDatabase

db = ExecutionDatabase(".anvil/history.db")

# Get recent coverage summaries
summaries = db.get_coverage_summary(space="local", limit=5)
for s in summaries:
    print(f"{s.execution_id}: {s.total_coverage:.2f}%")

# Get per-file coverage for specific execution
files = db.get_coverage_history(execution_id="local-20260202-170703", limit=100)
for f in files:
    print(f"{f.file_path}: {f.coverage_percentage:.1f}%")

db.close()
```

## 🔍 Coverage Analysis

### Find Coverage Regressions

```python
from anvil.parsers.coverage_parser import CoverageParser

parser = CoverageParser()

# Parse two coverage files
current = parser.parse_coverage_xml("coverage-current.xml")
baseline = parser.parse_coverage_xml("coverage-baseline.xml")

# Find files with coverage drop > 1%
regressions = parser.find_coverage_regressions(current, baseline, threshold=1.0)

for reg in regressions:
    print(f"{reg['file_path']}: {reg['coverage_drop']:.2f}% drop")
    print(f"  Was: {reg['baseline_coverage']:.2f}%")
    print(f"  Now: {reg['current_coverage']:.2f}%")
```

### Calculate Coverage Diff

```python
diff = parser.calculate_coverage_diff(current, baseline)

print(f"Overall: {diff['total_coverage_diff']:+.2f}%")
print(f"Improved files: {diff['files_improved']}")
print(f"Regressed files: {diff['files_regressed']}")
print(f"New files: {diff['new_files']}")
```

## 📈 Workflows

### Daily Development Workflow

```bash
# 1. Make changes to code

# 2. Run tests with coverage
python scripts/run_local_tests.py tests/ --cov=. --cov-report=xml

# 3. View coverage report
python scripts/generate_coverage_report.py
open coverage-report.html
```

### Pre-Commit Coverage Check

```bash
# Run tests with coverage
python scripts/run_local_tests.py tests/ --cov=. --cov-report=xml

# Check if coverage dropped
python -c "
from anvil.storage.execution_schema import ExecutionDatabase
db = ExecutionDatabase('.anvil/history.db')
summaries = db.get_coverage_summary(space='local', limit=2)
if len(summaries) >= 2:
    diff = summaries[0].total_coverage - summaries[1].total_coverage
    if diff < -1.0:
        print(f'❌ Coverage dropped by {-diff:.2f}%!')
        exit(1)
    print(f'✅ Coverage: {summaries[0].total_coverage:.2f}%')
db.close()
"
```

### Coverage Trend Analysis

```bash
# Generate report for last 30 days
python scripts/generate_coverage_report.py --window 30 --format markdown

# View trend in terminal
python -c "
from anvil.storage.execution_schema import ExecutionDatabase
from datetime import datetime, timedelta

db = ExecutionDatabase('.anvil/history.db')
summaries = db.get_coverage_summary(space='local', limit=10)

print('Coverage Trend (Last 10 Executions):')
print('-' * 60)
for s in summaries:
    date = s.timestamp.strftime('%Y-%m-%d %H:%M')
    print(f'{date}: {s.total_coverage:6.2f}% ({s.files_analyzed} files)')

db.close()
"
```

## 🛠️ Advanced Usage

### Parse Coverage Without Running Tests

```python
from anvil.parsers.coverage_parser import CoverageParser
from anvil.storage.execution_schema import (
    ExecutionDatabase,
    CoverageHistory,
    CoverageSummary,
)
from datetime import datetime

# Parse existing coverage file
parser = CoverageParser()
data = parser.parse_coverage_xml("path/to/coverage.xml")

# Store in database
db = ExecutionDatabase(".anvil/history.db")
execution_id = f"manual-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
timestamp = datetime.now()

# Store summary
summary = CoverageSummary(
    execution_id=execution_id,
    timestamp=timestamp,
    total_coverage=data.total_coverage,
    files_analyzed=data.files_analyzed,
    total_statements=data.total_statements,
    covered_statements=data.covered_statements,
    space="local",
)
db.insert_coverage_summary(summary)

# Store per-file coverage
for file_cov in data.file_coverage:
    history = CoverageHistory(
        execution_id=execution_id,
        file_path=file_cov.file_path,
        timestamp=timestamp,
        total_statements=file_cov.total_statements,
        covered_statements=file_cov.covered_statements,
        coverage_percentage=file_cov.coverage_percentage,
        missing_lines=file_cov.missing_lines,
        space="local",
    )
    db.insert_coverage_history(history)

db.close()
print(f"✅ Stored coverage: {data.total_coverage:.2f}%")
```

### Custom Coverage Report

```python
from anvil.storage.execution_schema import ExecutionDatabase

db = ExecutionDatabase(".anvil/history.db")

# Get latest coverage
summaries = db.get_coverage_summary(space="local", limit=1)
if not summaries:
    print("No coverage data found")
    exit(1)

latest = summaries[0]
files = db.get_coverage_history(execution_id=latest.execution_id, limit=1000)

# Find files below threshold
threshold = 80.0
low_coverage = [f for f in files if f.coverage_percentage < threshold]
low_coverage.sort(key=lambda x: x.coverage_percentage)

print(f"Files below {threshold}% coverage ({len(low_coverage)}):\n")
for f in low_coverage[:10]:
    missing = len(f.missing_lines) if f.missing_lines else 0
    print(f"{f.file_path:50} {f.coverage_percentage:6.2f}% (missing {missing} lines)")

db.close()
```

## 📚 File Locations

### Scripts
- `scripts/run_local_tests.py` - Run tests with coverage tracking
- `scripts/generate_coverage_report.py` - Generate coverage reports
- `scripts/check_coverage_tables.py` - Verify database schema
- `scripts/test_coverage_parser.py` - Test coverage parser
- `scripts/init_coverage_schema.py` - Initialize coverage tables

### Database
- `.anvil/history.db` - SQLite database with coverage data
  - `coverage_history` table: Per-file coverage records
  - `coverage_summary` table: Overall coverage summaries

### Coverage Files
- `coverage.xml` - pytest-cov XML output (Cobertura format)
- `coverage-report.html` - Generated HTML report
- `htmlcov/` - pytest-cov HTML report directory

### Documentation
- `docs/phase-2-complete.md` - Phase 2 completion summary
- `docs/local-coverage-report.md` - Sample Markdown report
- `docs/lens-implementation-plan.md` - Implementation plan (updated)

## ❓ Troubleshooting

### Coverage file not found

**Problem**: "Coverage requested but no coverage.xml found"

**Solution**: Make sure to include `--cov-report=xml` in pytest arguments:
```bash
python scripts/run_local_tests.py tests/ --cov=. --cov-report=xml
```

### Coverage tables missing

**Problem**: "No coverage tables found"

**Solution**: Initialize schema:
```bash
python scripts/init_coverage_schema.py
```

### Old coverage data

**Problem**: Coverage file is from previous run

**Solution**: Coverage auto-detection checks if file was modified within last 60 seconds. Either:
1. Delete old coverage.xml before running tests
2. Manually specify coverage file location

### Parser errors

**Problem**: "Failed to parse coverage: ..."

**Solution**: Ensure coverage.xml is valid Cobertura XML format:
```bash
# Validate XML
python -c "import xml.etree.ElementTree as ET; ET.parse('coverage.xml')"
```

## 🎯 Best Practices

1. **Always use --cov-report=xml**: Required for database storage
2. **Run coverage regularly**: Track trends over time
3. **Set coverage thresholds**: Prevent regressions
4. **Review low-coverage files**: Prioritize testing gaps
5. **Compare local vs CI**: Identify platform-specific gaps (future feature)

## 📞 Support

For issues or questions:
1. Check [Phase 2 Complete Documentation](docs/phase-2-complete.md)
2. Review inline docstrings in source files
3. Check database schema in `anvil/storage/execution_schema.py`
4. Review parser implementation in `anvil/parsers/coverage_parser.py`
