#!/usr/bin/env python
"""Test Issue dataclass directly."""

import inspect
from anvil.models.validator import Issue
import sys
from pathlib import Path

# Add local anvil to path FIRST (before site-packages)
anvil_path = Path(__file__).parent / 'anvil'
sys.path.insert(0, str(anvil_path))


print(f"Issue module: {Issue.__module__}")
print(f"Issue file: {inspect.getfile(Issue)}")

# Check the annotations
print(f"Issue annotations: {Issue.__annotations__}")

# Create an issue WITH diff
try:
    issue_with_diff = Issue(
        file_path="test.py",
        line_number=1,
        message="Test error",
        severity="error",
        rule_name="TEST",
        error_code="TEST_CODE",
        diff="This is a diff"
    )

    print("Issue with diff:")
    print(f"  Object: {issue_with_diff}")
    print(f"  Has diff attr: {hasattr(issue_with_diff, 'diff')}")
    print(f"  Diff value: {issue_with_diff.diff}")
except TypeError as e:
    print(f"ERROR creating issue with diff: {e}")
