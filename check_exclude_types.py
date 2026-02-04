#!/usr/bin/env python
"""Analyze type matching between matrix and exclude in workflows."""

import yaml

workflows = {
    'anvil': '.github/workflows/anvil-tests.yml',
    'forge': '.github/workflows/forge-tests.yml',
    'scout': '.github/workflows/scout-tests.yml',
    'verdict': '.github/workflows/verdict-tests.yml'
}

print("\n" + "="*80)
print("DETAILED TYPE MATCHING ANALYSIS")
print("="*80)

for name, filepath in workflows.items():
    with open(filepath) as f:
        data = yaml.safe_load(f)

    for job_name, job_data in data.get('jobs', {}).items():
        if 'strategy' not in job_data or 'matrix' not in job_data['strategy']:
            continue

        matrix = job_data['strategy']['matrix']
        exclude = job_data['strategy'].get('exclude', [])

        if not exclude:
            continue

        print(f"\n{name.upper()} - Job: {job_name}")
        print("-" * 80)

        # Check types in matrix
        print("Matrix variable types:")
        for var_name, values in matrix.items():
            value_types = set()
            for v in values:
                value_types.add(type(v).__name__)
            print(f"  {var_name}: {values}")
            print(f"    Types: {', '.join(sorted(value_types))}")

        # Check types in exclude
        print("\nExclude rule types:")
        for i, exc_rule in enumerate(exclude):
            print(f"  Rule {i+1}: {exc_rule}")
            for var_name, var_value in exc_rule.items():
                print(
                    f"    {var_name}: {repr(var_value)} (type: {type(var_value).__name__})")

        # TYPE MATCHING CHECK
        print("\nTYPE MATCHING VERIFICATION:")
        for exc_rule in exclude:
            for var_name, exc_value in exc_rule.items():
                if var_name in matrix:
                    matrix_values = matrix[var_name]
                    # Check if the exclude value's type matches any matrix value's type
                    matrix_types = {type(v).__name__ for v in matrix_values}
                    exc_type = type(exc_value).__name__

                    if exc_type in matrix_types:
                        # Check if value actually exists
                        if exc_value in matrix_values:
                            print(
                                f"  ✓ {var_name}={repr(exc_value)} - MATCH FOUND")
                        else:
                            print(
                                f"  ✗ {var_name}={repr(exc_value)} - TYPE OK but VALUE NOT IN MATRIX!")
                    else:
                        print(
                            f"  ✗ {var_name}={repr(exc_value)} - TYPE MISMATCH! Expected {matrix_types}, got {exc_type}")

print("\n" + "="*80)
