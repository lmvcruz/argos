"""Test diffs end-to-end with black validator."""

from anvil.validators.black_validator import BlackValidator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "anvil"))


# Create black validator
validator = BlackValidator()

# Validate a file
results = validator.validate([str(Path("scout/scout/cli.py"))], {})

print("=== VALIDATION RESULTS ===")
print(f"File: scout/scout/cli.py")
print(f"Type: {type(results)}")
print(f"Passed: {results.passed if hasattr(results, 'passed') else 'N/A'}")
print(f"Errors: {len(results.errors) if hasattr(results, 'errors') else 0}")

if hasattr(results, "errors") and results.errors:
    error = results.errors[0]
    print(f"\nFirst error:")
    print(f"  Message: {error.message}")
    if hasattr(error, "diff") and error.diff:
        print(f"  Diff exists: YES")
        print(f"  Diff length: {len(error.diff)} chars")
        print(f"\n  Diff preview (first 300 chars):")
        print(f"{error.diff[:300]}")
    else:
        print(f"  Diff exists: NO")
        print(f"  Error attributes: {dir(error)}")
