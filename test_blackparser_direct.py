"""Test BlackParser.run_and_parse directly."""

from anvil.parsers.black_parser import BlackParser
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "anvil"))


# Test the parser
result = BlackParser.run_and_parse([Path("scout/scout/cli.py")], {})

print("=== ValidationResult ===")
print(f"Validator: {result.validator_name}")
print(f"Passed: {result.passed}")
print(f"Files checked: {result.files_checked}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")

if result.errors:
    error = result.errors[0]
    print(f"\nFirst error:")
    print(f"  File: {error.file_path}")
    print(f"  Message: {error.message}")
    print(f"  Severity: {error.severity}")
    print(f"  Has diff: {error.diff is not None}")

    if error.diff:
        print(f"  Diff length: {len(error.diff)} chars")
        print(f"  Diff preview:\n{error.diff[:300]}")
    else:
        print(f"  ERROR: Diff is None!")
        print(f"  Error attributes: {vars(error)}")
