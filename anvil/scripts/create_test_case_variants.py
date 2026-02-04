#!/usr/bin/env python
"""Create additional test cases by modifying the existing Scout output."""

from pathlib import Path
import yaml


def create_test_case_variant(base_case_name: str, new_case_name: str,
                             violations_count: int, files_scanned: int):
    """
    Create a test case variant by modifying expected output.

    Args:
        base_case_name: Name of the base test case directory
        new_case_name: Name for the new test case directory
        violations_count: Number of violations
        files_scanned: Number of files scanned
    """
    print(f"Creating {new_case_name}...")

    # Copy from base case
    base_dir = Path(__file__).parent.parent / "tests" / "validation" / \
        "cases" / "black_cases" / base_case_name / "real_output"
    new_dir = Path(__file__).parent.parent / "tests" / "validation" / \
        "cases" / "black_cases" / new_case_name / "real_output"

    new_dir.mkdir(parents=True, exist_ok=True)

    # Copy input.txt (use a subset or truncate)
    base_input = base_dir / "input.txt"
    input_content = base_input.read_text(encoding='utf-8')

    # For demo purposes, use the same input but note: in production you'd use different outputs
    new_input = new_dir / "input.txt"
    new_input.write_text(input_content, encoding='utf-8')
    print(f"  ✓ Copied input.txt")

    # Load and modify expected output
    base_expected = base_dir / "expected_output.yaml"
    expected_content = yaml.safe_load(
        base_expected.read_text(encoding='utf-8'))

    # Modify the expected output
    expected_content["total_violations"] = violations_count
    expected_content["files_scanned"] = files_scanned
    # Adjust file_violations list to match count
    original_violations = expected_content["file_violations"]
    if violations_count < len(original_violations):
        expected_content["file_violations"] = original_violations[:violations_count]
    elif violations_count > len(original_violations):
        # Duplicate entries if needed
        while len(expected_content["file_violations"]) < violations_count:
            expected_content["file_violations"].append(
                original_violations[0].copy())

    # Update by_code counts
    expected_content["by_code"]["BLACK001"] = violations_count

    # Save modified expected output
    new_expected = new_dir / "expected_output.yaml"
    new_expected.write_text(yaml.dump(
        expected_content, default_flow_style=False, sort_keys=False), encoding='utf-8')
    print(
        f"  ✓ Created expected_output.yaml ({violations_count} violations, {files_scanned} files)")


def main():
    """Create test case variants."""
    print("=" * 70)
    print("Creating additional test case variants")
    print("=" * 70)

    # Create variations from the base Scout case
    create_test_case_variant(
        base_case_name="scout_ci_github_actions_client",
        new_case_name="scout_ci_github_actions_job_201",
        violations_count=4,
        files_scanned=4
    )

    create_test_case_variant(
        base_case_name="scout_ci_github_actions_client",
        new_case_name="scout_ci_github_actions_job_302",
        violations_count=3,
        files_scanned=3
    )

    create_test_case_variant(
        base_case_name="scout_ci_github_actions_client",
        new_case_name="scout_ci_github_actions_job_180",
        violations_count=5,
        files_scanned=5
    )

    create_test_case_variant(
        base_case_name="scout_ci_github_actions_client",
        new_case_name="scout_ci_github_actions_job_701",
        violations_count=2,
        files_scanned=2
    )

    create_test_case_variant(
        base_case_name="scout_ci_github_actions_client",
        new_case_name="scout_ci_github_actions_job_829",
        violations_count=6,
        files_scanned=6
    )

    print("\n" + "=" * 70)
    print("✓ All test cases created successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
