#!/usr/bin/env python
"""Test black validator with diff extraction."""

from anvil.validators.black_validator import BlackValidator
from pathlib import Path

# Try to run validation
validator = BlackValidator()
files = [str(f)
         for f in Path(r'D:\playground\argos\scout\scout').rglob('*.py')][:2]
print(f'Files to validate: {files}')

try:
    result = validator.validate(files, {})
    print(f'Validation passed: {result.passed}')
    print(f'Errors: {len(result.errors)}')

    if result.errors:
        err = result.errors[0]
        print(f'\nFirst error:')
        print(f'  File: {err.file_path}')
        print(f'  Message: {err.message}')
        print(f'  Has diff: {err.diff is not None}')
        if err.diff:
            print(f'  Diff length: {len(err.diff)} chars')
            print(f'  Diff preview (first 300 chars):')
            print(f'  {repr(err.diff[:300])}')

except Exception as e:
    import traceback
    print(f'Error: {e}')
    traceback.print_exc()
