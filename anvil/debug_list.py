#!/usr/bin/env python
from anvil.testing.verdict_runner import VerdictRunner
from pathlib import Path

runner = VerdictRunner(Path('tests/validation/config.yaml'))
try:
    cases = runner.list_cases('black')
    print(f'Found {len(cases)} cases:')
    for case in cases:
        print(f"  - {case['name']}")
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
