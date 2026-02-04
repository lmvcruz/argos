#!/usr/bin/env python
"""Validate GitHub Actions workflow files for correct syntax and exclude rules."""

import yaml
import sys

workflows = [
    '.github/workflows/anvil-tests.yml',
    '.github/workflows/forge-tests.yml',
    '.github/workflows/scout-tests.yml',
    '.github/workflows/verdict-tests.yml'
]

print("\n" + "="*70)
print("WORKFLOW VALIDATION REPORT")
print("="*70)

for wf_file in workflows:
    try:
        with open(wf_file) as f:
            data = yaml.safe_load(f)

        print(f"\n{'FILE:':<10} {wf_file}")
        print(f"{'STATUS:':<10} ✓ VALID YAML")

        # Check for jobs with matrix strategy
        for job_name, job_data in data.get('jobs', {}).items():
            if 'strategy' in job_data and 'matrix' in job_data['strategy']:
                matrix = job_data['strategy']['matrix']
                excludes = job_data['strategy'].get('exclude', [])

                print(f"\n  JOB: {job_name}")
                print(f"    Matrix dimensions:")
                for key, values in matrix.items():
                    print(f"      - {key}: {values}")

                if excludes:
                    print(f"    Exclude rules ({len(excludes)}):")
                    for exc in excludes:
                        print(f"      - {exc}")
                    # Analyze what gets excluded
                    if len(excludes) == 1:
                        exc = excludes[0]
                        total_combos = 1
                        for key, values in matrix.items():
                            total_combos *= len(values)
                        print(
                            f"    Effect: Excludes 1 combination from {total_combos} total")
                        print(
                            f"            Remaining: {total_combos - 1} combinations")
                else:
                    print(f"    Exclude rules: (none)")

    except FileNotFoundError:
        print(f"\n{'FILE:':<10} {wf_file}")
        print(f"{'STATUS:':<10} ✗ FILE NOT FOUND")
    except yaml.YAMLError as e:
        print(f"\n{'FILE:':<10} {wf_file}")
        print(f"{'STATUS:':<10} ✗ INVALID YAML")
        print(f"{'ERROR:':<10} {e}")
    except Exception as e:
        print(f"\n{'FILE:':<10} {wf_file}")
        print(f"{'STATUS:':<10} ✗ ERROR")
        print(f"{'ERROR:':<10} {type(e).__name__}: {e}")

print("\n" + "="*70)
print("MATRIX COMPOSITION ANALYSIS")
print("="*70)

# Detailed breakdown for one workflow as example
example_file = '.github/workflows/anvil-tests.yml'
with open(example_file) as f:
    data = yaml.safe_load(f)

test_job = data['jobs']['test']
matrix = test_job['strategy']['matrix']
excludes = test_job['strategy'].get('exclude', [])

os_values = matrix['os']
py_values = matrix['python-version']

print(f"\nFile: {example_file}")
print(f"Job: test")
print(f"\nMatrix combinations (before exclude):")
all_combos = []
for os_val in os_values:
    for py_val in py_values:
        all_combos.append({'os': os_val, 'python-version': py_val})
        print(f"  - os: {os_val}, python-version: {py_val}")

print(f"\nTotal combinations: {len(all_combos)}")

print(f"\nExcluded combinations:")
for exc in excludes:
    print(f"  - os: {exc['os']}, python-version: {exc['python-version']}")

# Calculate remaining
remaining = [c for c in all_combos if c not in excludes]
print(f"\nRemaining combinations: {len(remaining)}")
print(
    f"  Windows (3 Python versions): {sum(1 for c in remaining if 'windows' in c['os'])}")
print(
    f"  macOS (3 Python versions): {sum(1 for c in remaining if 'macos' in c['os'])}")
print(
    f"  Ubuntu (non-3.11): {sum(1 for c in remaining if 'ubuntu' in c['os'])}")

print("\n" + "="*70)
