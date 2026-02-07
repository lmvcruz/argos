#!/usr/bin/env python
"""Test the complete Black validation flow."""

from anvil.parsers.black_parser import BlackParser
from anvil.validators.black_validator import BlackValidator
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'anvil'))
sys.path.insert(0, str(Path(__file__).parent / 'lens'))


# Test file
test_file = Path(__file__).parent / 'anvil' / 'anvil' / \
    'validators' / 'black_validator.py'

print(f"Test file: {test_file}")
print(f"File exists: {test_file.exists()}")
print()

# Test the validator
validator = BlackValidator()
print(f"Validator available: {validator.is_available()}")
print()

# Run validation
result = validator.validate([str(test_file)], {})

print(f"Validation result:")
print(f"  Passed: {result.passed}")
print(f"  Files checked: {result.files_checked}")
print(f"  Errors: {len(result.errors)}")
print(f"  Warnings: {len(result.warnings)}")
print()

# Check first error
if result.errors:
    error = result.errors[0]
    print(f"First error:")
    print(f"  Error object: {error}")
    print(f"  Error dir: {[x for x in dir(error) if not x.startswith('_')]}")
    print(f"  File: {error.file_path}")
    print(f"  Message: {error.message}")
    print(f"  Has diff attr: {hasattr(error, 'diff')}")
    print(f"  Diff value: {error.diff if hasattr(error, 'diff') else 'N/A'}")
    print(
        f"  Diff is None: {error.diff is None if hasattr(error, 'diff') else 'N/A'}")
    if hasattr(error, 'diff') and error.diff:
        print(f"  Diff length: {len(error.diff)}")
        print(f"  First 100 chars of diff:\n{error.diff[:100]}")
