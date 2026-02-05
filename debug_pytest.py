#!/usr/bin/env python3
"""
Debug script to test pytest execution on Anvil tests
"""

import subprocess
import sys
from pathlib import Path

# Test running pytest on the anvil tests directory
test_path = Path("d:/playground/argos/anvil/tests")

if not test_path.exists():
    print(f"ERROR: Test path does not exist: {test_path}")
    sys.exit(1)

print(f"Testing pytest discovery on: {test_path}")
print(f"Test path exists: {test_path.exists()}")
print(f"Test path is dir: {test_path.is_dir()}")

# List some test files
test_files = list(test_path.glob("test_*.py"))[:5]
print(f"\nFound {len(test_files)} test files (showing first 5):")
for f in test_files:
    print(f"  - {f.name}")

# Try running pytest with collection only first
print("\n" + "="*60)
print("Running: pytest --collect-only")
print("="*60)

result = subprocess.run(
    [sys.executable, "-m", "pytest", str(test_path), "--collect-only", "-q"],
    capture_output=True,
    text=True,
    timeout=30
)

print(f"Return code: {result.returncode}")
print(f"Output length: {len(result.stdout)}")
if result.stdout:
    print(f"STDOUT (first 500 chars):\n{result.stdout[:500]}")
if result.stderr:
    print(f"STDERR (first 500 chars):\n{result.stderr[:500]}")

# Now try running actual tests with verbose output
print("\n" + "="*60)
print("Running: pytest -v (first 10 tests)")
print("="*60)

result = subprocess.run(
    [sys.executable, "-m", "pytest",
        str(test_path), "-v", "-x", "--maxfail=1"],
    capture_output=True,
    text=True,
    timeout=60
)

print(f"Return code: {result.returncode}")
print(f"Output length: {len(result.stdout)}")
if result.stdout:
    print(f"STDOUT (first 1000 chars):\n{result.stdout[:1000]}")
if result.stderr:
    print(f"STDERR (first 500 chars):\n{result.stderr[:500]}")

# Try with json report
print("\n" + "="*60)
print("Running: pytest --json-report")
print("="*60)

json_report = Path("/tmp/pytest_report.json")
result = subprocess.run(
    [sys.executable, "-m", "pytest",
        str(test_path), "--json-report", f"--json-report-file={json_report}", "-v", "--maxfail=1"],
    capture_output=True,
    text=True,
    timeout=60
)

print(f"Return code: {result.returncode}")
print(f"Output length: {len(result.stdout)}")
print(f"JSON report exists: {json_report.exists()}")

if result.stdout:
    # Count test results in output
    import re
    passed = len(re.findall(r'PASSED', result.stdout))
    failed = len(re.findall(r'FAILED', result.stdout))
    skipped = len(re.findall(r'SKIPPED', result.stdout))
    print(
        f"Test results in output: {passed} passed, {failed} failed, {skipped} skipped")
    print(f"STDOUT (first 1000 chars):\n{result.stdout[:1000]}")

if result.stderr:
    print(f"STDERR (first 500 chars):\n{result.stderr[:500]}")

if json_report.exists():
    import json
    with open(json_report) as f:
        data = json.load(f)
    print(f"JSON report tests: {len(data.get('tests', []))}")
    if 'summary' in data:
        print(f"Summary: {data['summary']}")
