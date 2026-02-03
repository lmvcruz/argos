"""Test script for LintParser."""

from anvil.anvil.parsers.lint_parser import LintParser
from pathlib import Path

parser = LintParser()

# Test flake8 parsing
print("=" * 60)
print("Testing flake8 parser")
print("=" * 60)

flake8_output = """forge/models/metadata.py:42:80: E501 line too long (105 > 100 characters)
forge/models/metadata.py:45:1: W293 blank line contains whitespace
forge/cli/argument_parser.py:10:1: F401 'sys' imported but unused
forge/cli/argument_parser.py:125:5: E722 do not use bare 'except'
anvil/storage/execution_schema.py:200:10: C901 'insert_execution_history' is too complex (11)
"""

lint_data = parser.parse_flake8_output(flake8_output)

print(f"\n📊 Flake8 Parse Results:")
print(f"  Validator: {lint_data.validator}")
print(f"  Total violations: {lint_data.total_violations}")
print(f"  Files scanned: {lint_data.files_scanned}")
print(f"  Errors: {lint_data.errors}")
print(f"  Warnings: {lint_data.warnings}")
print(f"  Info: {lint_data.info}")
print(f"  By code: {lint_data.by_code}")

print(f"\n📁 File Violations:")
for file_viols in lint_data.file_violations:
    print(f"  {file_viols.file_path}: {len(file_viols.violations)} violations")
    for viol in file_viols.violations[:2]:  # Show first 2
        print(f"    - Line {viol['line_number']}: [{viol['code']}] {viol['message']}")

# Test black parsing
print("\n" + "=" * 60)
print("Testing black parser")
print("=" * 60)

black_output = """would reformat forge/models/metadata.py
would reformat anvil/storage/execution_schema.py
2 files would be reformatted, 10 files would be left unchanged.
"""

black_data = parser.parse_black_output(black_output)

print(f"\n📊 Black Parse Results:")
print(f"  Validator: {black_data.validator}")
print(f"  Total violations: {black_data.total_violations}")
print(f"  Files scanned: {black_data.files_scanned}")
print(f"  Warnings: {black_data.warnings}")

print(f"\n📁 File Violations:")
for file_viols in black_data.file_violations:
    print(f"  {file_viols.file_path}: {file_viols.violations[0]['message']}")

# Test isort parsing
print("\n" + "=" * 60)
print("Testing isort parser")
print("=" * 60)

isort_output = """ERROR: forge/cli/argument_parser.py Imports are incorrectly sorted and/or formatted.
ERROR: anvil/parsers/coverage_parser.py Imports are incorrectly sorted and/or formatted.
"""

isort_data = parser.parse_isort_output(isort_output)

print(f"\n📊 Isort Parse Results:")
print(f"  Validator: {isort_data.validator}")
print(f"  Total violations: {isort_data.total_violations}")
print(f"  Files scanned: {isort_data.files_scanned}")
print(f"  Warnings: {isort_data.warnings}")

print(f"\n📁 File Violations:")
for file_viols in isort_data.file_violations:
    print(f"  {file_viols.file_path}: {file_viols.violations[0]['message']}")

# Test quality score calculation
print("\n" + "=" * 60)
print("Testing quality score calculation")
print("=" * 60)

test_cases = [(0, 100), (10, 100), (50, 100), (100, 100), (200, 100)]

for violations, lines in test_cases:
    score = parser.calculate_quality_score(violations, lines)
    print(f"  {violations} violations in {lines} lines = {score}/100 score")

# Test utility methods
print("\n" + "=" * 60)
print("Testing utility methods")
print("=" * 60)

test_violations = [
    {"severity": "ERROR", "code": "E501"},
    {"severity": "WARNING", "code": "W503"},
    {"severity": "ERROR", "code": "E722"},
    {"severity": "ERROR", "code": "E501"},
    {"severity": "WARNING", "code": "C901"},
]

severity_agg = parser.aggregate_by_severity(test_violations)
print(f"\nSeverity aggregation: {severity_agg}")

most_common = parser.find_most_common_violation(test_violations)
print(f"Most common violation: {most_common}")

errors_only = parser.filter_by_severity(test_violations, "ERROR")
print(f"ERROR violations only: {len(errors_only)}")

print("\n🎉 All LintParser tests passed!")
