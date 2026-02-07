"""Test full validator flow through BlackValidator."""

from anvil.validators.black_validator import BlackValidator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "anvil"))


# Test the validator
validator = BlackValidator()

# Test with absolute path
test_file = Path(__file__).parent / "scout" / "scout" / "cli.py"

result = validator.validate([str(test_file)], {})

print("=== ValidationResult from BlackValidator ===")
print(f"Validator: {result.validator_name}")
print(f"Passed: {result.passed}")
print(f"Files checked: {result.files_checked}")
print(f"Errors: {len(result.errors)}")

if result.errors:
    error = result.errors[0]
    print(f"\nFirst error:")
    print(f"  File: {error.file_path}")
    print(f"  Message: {error.message}")
    print(f"  Diff exists: {error.diff is not None}")

    if error.diff:
        print(f"  Diff length: {len(error.diff)} chars")
    else:
        print(f"  ERROR: Diff is None!")
