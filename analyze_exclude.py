#!/usr/bin/env python
"""
Deep investigation of GitHub Actions matrix exclude syntax.

The exclude field in GitHub Actions has specific requirements that might not be obvious.
This script tests various exclude configurations.
"""

import yaml

test_cases = {
    "current_anvil": """
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
      exclude:
        - os: ubuntu-latest
          python-version: '3.11'
""",
    "exclude_with_include": """
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
      exclude:
        - os: ubuntu-latest
          python-version: '3.11'
      include:
        - os: ubuntu-latest
          python-version: '3.11'
          special: true
""",
    "exclude_string_version": """
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: [3.8, 3.9, 3.10, 3.11, 3.12]
      exclude:
        - os: ubuntu-latest
          python-version: 3.11
""",
    "exclude_multiple": """
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
      exclude:
        - os: ubuntu-latest
          python-version: '3.11'
        - os: windows-latest
          python-version: '3.12'
""",
}

print("\n" + "="*80)
print("GITHUB ACTIONS MATRIX EXCLUDE SYNTAX ANALYSIS")
print("="*80)

for name, yaml_content in test_cases.items():
    print(f"\n{'TEST CASE:':<20} {name}")
    print("-" * 80)

    try:
        data = yaml.safe_load(yaml_content)
        strategy = data['jobs']['test']['strategy']
        matrix = strategy['matrix']
        exclude = strategy.get('exclude', [])

        print(f"{'Matrix keys:':<20} {list(matrix.keys())}")
        print(f"{'Exclude rules:':<20} {len(exclude)}")

        # Calculate combinations
        total = 1
        for key, values in matrix.items():
            print(f"  {key}: {values}")
            total *= len(values)

        excluded_count = len(exclude)
        remaining = total - excluded_count

        print(f"\nTotal combinations: {total}")
        print(f"Excluded: {excluded_count}")
        print(f"Remaining: {remaining}")

        if exclude:
            print(f"\nExclude rules:")
            for exc in exclude:
                print(f"  {exc}")

        print(f"\n✓ VALID")

    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {e}")

print("\n" + "="*80)
print("KEY FINDINGS FOR GITHUB ACTIONS")
print("="*80)
print("""
1. EXCLUDE SYNTAX REQUIREMENTS:
   - Must be a list of objects (dictionaries)
   - Each object must have keys that match matrix variables
   - String values in exclude MUST match string values in matrix exactly
   - Integer/number values in exclude must match number values in matrix

2. COMMON ISSUES:
   - Using quoted numbers ('3.11') in matrix but unquoted in exclude (3.11)
   - Using unquoted numbers in matrix but quoted in exclude
   - Having wrong indentation level for exclude

3. MATRIX vs EXCLUDE TYPE MATCHING:
   - If matrix: ['3.8', '3.9'] (strings)
      Then exclude must use: python-version: '3.8' (strings)

   - If matrix: [3.8, 3.9] (numbers)
      Then exclude must use: python-version: 3.8 (numbers, no quotes)

4. WORKFLOW_DISPATCH TRIGGER:
   - The "workflow_dispatch event trigger" error usually means:
     a) The workflow file has YAML syntax errors
     b) The workflow file failed to parse
     c) Matrix exclude created an invalid job definition

   - This is NOT about the presence of workflow_dispatch
""")
