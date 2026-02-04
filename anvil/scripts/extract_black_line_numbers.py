#!/usr/bin/env python3
"""
Extract actual line numbers from black diff output for test case validation.

This script updates all expected_output.yaml files in black_cases to use
actual line numbers extracted from diff hunk headers instead of the placeholder
value of 1.
"""

import re
from pathlib import Path
from typing import List, Dict

import yaml


def extract_line_numbers_from_diff(input_text: str) -> Dict[str, List[int]]:
    """
    Extract the line numbers where violations occur from unified diff format.

    Black output format:
    @@ -47,13 +47,11 @@
    would reformat /path/to/file.py

    Args:
        input_text: Raw black output with unified diff

    Returns:
        Dictionary mapping file paths to list of line numbers
    """
    violations_by_file: Dict[str, List[int]] = {}

    hunk_pattern = r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@"
    reformat_pattern = r"would reformat (.+)"

    current_hunk_line = None

    for line in input_text.split('\n'):
        # Check for hunk header
        hunk_match = re.match(hunk_pattern, line)
        if hunk_match:
            current_hunk_line = int(hunk_match.group(1))
            continue

        # Check for "would reformat" message
        match = re.search(reformat_pattern, line)
        if match:
            file_path = match.group(1).strip()
            line_number = current_hunk_line if current_hunk_line else 1

            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(line_number)

    return violations_by_file


def update_expected_output(yaml_path: Path, line_numbers: Dict[str, List[int]]) -> None:
    """
    Update expected_output.yaml file with actual line numbers.

    Removes redundant fields: column_number, severity, code, message
    Keeps only: line_number

    Args:
        yaml_path: Path to expected_output.yaml
        line_numbers: Dictionary of file_path -> list of line numbers
    """
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not data or 'file_violations' not in data:
        return

    # Update each file violation
    for file_violation in data['file_violations']:
        file_path = file_violation['file_path']

        # Get the line numbers for this file
        if file_path in line_numbers:
            line_nums = line_numbers[file_path]

            # Update violations with extracted line numbers
            violations = []
            for line_num in line_nums:
                violations.append({'line_number': line_num})

            file_violation['violations'] = violations

    # Recalculate counts
    total_violations = sum(
        len(fv['violations']) for fv in data['file_violations']
    )
    data['total_violations'] = total_violations
    data['warnings'] = total_violations
    data['by_code']['BLACK001'] = total_violations

    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def main():
    """Update all black_cases expected_output.yaml files."""
    cases_dir = Path(__file__).parent.parent / 'tests' / \
        'validation' / 'cases' / 'black_cases'

    if not cases_dir.exists():
        print(f"Cases directory not found: {cases_dir}")
        return

    # Find all test cases
    test_cases = sorted([d for d in cases_dir.iterdir() if d.is_dir()])

    for test_case in test_cases:
        input_file = test_case / 'real_output' / 'input.txt'
        expected_file = test_case / 'real_output' / 'expected_output.yaml'

        if not input_file.exists() or not expected_file.exists():
            continue

        print(f"Processing: {test_case.name}")

        # Extract line numbers from input
        with open(input_file) as f:
            input_text = f.read()

        line_numbers = extract_line_numbers_from_diff(input_text)

        if line_numbers:
            print(
                f"  Found {sum(len(v) for v in line_numbers.values())} violations")
            print(
                f"  Files: {', '.join(Path(p).name for p in line_numbers.keys())}")
            update_expected_output(expected_file, line_numbers)
            print(f"  Updated: {expected_file.name}")
        else:
            print(f"  No violations found in: {input_file.name}")


if __name__ == '__main__':
    main()
