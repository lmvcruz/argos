#!/usr/bin/env python
from pathlib import Path
from anvil.testing.verdict_runner import CaseDiscovery

root = Path('tests/validation/cases/black_cases')
discovery = CaseDiscovery(root)
cases = discovery.discover()
print(f'Found {len(cases)} cases:')
for case in cases:
    print(f"  - {case['name']} (type: {case['type']})")
