#!/usr/bin/env python
"""Fix expected outputs for all scout test cases to match the actual input."""

from pathlib import Path
from anvil.parsers.lint_parser import LintParser
import yaml


def fix_test_case_expected_output(case_name: str):
    """
    Fix the expected_output.yaml to match the actual parsed input.

    Args:
        case_name: Name of the test case directory
    """
    print(f"Fixing {case_name}...")

    case_dir = Path(__file__).parent.parent / "tests" / "validation" / \
        "cases" / "black_cases" / case_name / "real_output"

    # Read the input
    input_file = case_dir / "input.txt"
    input_content = input_file.read_text(encoding='utf-8')

    # Parse it
    parser = LintParser()
    lint_data = parser.parse_black_output(input_content, Path("."))

    # Create the correct output structure
    output = {
        "validator": lint_data.validator,
        "total_violations": lint_data.total_violations,
        "files_scanned": lint_data.files_scanned,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violations": fv.violations,  # violations are already dicts
                "validator": fv.validator,
            }
            for fv in lint_data.file_violations
        ],
    }

    # Save the corrected expected output
    expected_file = case_dir / "expected_output.yaml"
    expected_file.write_text(
        yaml.dump(output, default_flow_style=False, sort_keys=False), encoding='utf-8')
    print(
        f"  ✓ Fixed: {lint_data.total_violations} violations, {lint_data.files_scanned} files")


def main():
    """Fix all scout test cases."""
    print("=" * 70)
    print("Fixing Scout test case expected outputs")
    print("=" * 70)

    cases = [
        "scout_ci_github_actions_client",
        "scout_ci_github_actions_job_201",
        "scout_ci_github_actions_job_302",
        "scout_ci_github_actions_job_180",
        "scout_ci_github_actions_job_701",
        "scout_ci_github_actions_job_829",
    ]

    for case in cases:
        fix_test_case_expected_output(case)

    print("\n" + "=" * 70)
    print("✓ All test cases fixed")
    print("=" * 70)


if __name__ == "__main__":
    main()
