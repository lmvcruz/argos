"""Debug what the validator returns."""

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

print("=== ValidationResult Details ===")
print(f"Validator class: {result.__class__}")
print(f"Validator module: {result.__class__.__module__}")
print(f"Errors: {len(result.errors)}")

if result.errors:
    error = result.errors[0]
    print(f"\nFirst error class: {error.__class__}")
    print(f"First error module: {error.__class__.__module__}")
    print(
        f"First error __dataclass_fields__: {error.__dataclass_fields__ if hasattr(error, '__dataclass_fields__') else 'N/A'}")
    print(f"First error __dict__: {error.__dict__}")
    print(f"First error vars(): {vars(error)}")
