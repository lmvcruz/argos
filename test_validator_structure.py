"""Test validator return structure."""

from anvil.validators.black_validator import BlackValidator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "lens"))
sys.path.insert(0, str(Path(__file__).parent / "anvil"))


# Test the validator
validator = BlackValidator()

# Test with absolute path
test_file = Path(__file__).parent / "scout" / "scout" / "cli.py"

result = validator.validate([str(test_file)], {})

print(f"Result type: {type(result)}")
print(f"Result.errors type: {type(result.errors)}")
print(f"Result.warnings type: {type(result.warnings)}")
print(f"Result.errors: {len(result.errors)}")
print(f"Result.warnings: {len(result.warnings)}")

if result.errors:
    error = result.errors[0]
    print(f"\nError type: {type(error)}")
    print(f"Error as dict: {error.to_dict()}")
