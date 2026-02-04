#!/usr/bin/env python
"""Extract and create multiple test cases from Scout CI logs."""

from scout.providers.github_actions import GitHubActionsProvider
from scout.log_retrieval import LogRetriever
from pathlib import Path
from anvil.parsers.lint_parser import LintParser
import yaml
import sys

# Add scout to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scout"))


def extract_and_create_test_case(run_id: str, job_id: str, case_name: str) -> bool:
    """
    Extract log from GitHub Actions and create test case.

    Args:
        run_id: GitHub Actions run ID
        job_id: GitHub Actions job ID
        case_name: Name for the test case directory

    Returns:
        True if successful, False otherwise
    """
    print(f"Processing {case_name}...")

    try:
        # Extract logs using Scout
        provider = GitHubActionsProvider(owner="lmvcruz", repo="argos")
        retriever = LogRetriever(provider)
        logs = retriever.get_logs(run_id, job_id, use_cache=True)

        if not logs:
            print(f"  ❌ No logs retrieved for {run_id}/{job_id}")
            return False

        print(f"  ✓ Extracted {len(logs)} bytes")

        # Create test case directory
        test_dir = Path(__file__).parent / "tests" / "validation" / \
            "cases" / "black_cases" / case_name / "real_output"
        test_dir.mkdir(parents=True, exist_ok=True)

        # Save input.txt
        input_file = test_dir / "input.txt"
        input_file.write_text(logs, encoding='utf-8')
        print(f"  ✓ Saved input.txt ({len(logs)} bytes)")

        # Parse the output
        parser = LintParser()
        lint_data = parser.parse_black_output(logs, Path("."))

        # Create expected output
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
                    "violations": [
                        {
                            "line_number": v.line_number,
                            "column_number": v.column_number,
                            "severity": v.severity,
                            "code": v.code,
                            "message": v.message,
                        }
                        for v in fv.violations
                    ],
                    "validator": fv.validator,
                }
                for fv in lint_data.file_violations
            ],
        }

        # Save expected_output.yaml
        expected_file = test_dir / "expected_output.yaml"
        expected_file.write_text(
            yaml.dump(output, default_flow_style=False, sort_keys=False), encoding='utf-8')
        print(f"  ✓ Saved expected_output.yaml")
        print(
            f"  ✓ Parsed: {lint_data.total_violations} violations in {lint_data.files_scanned} files")

        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Extract all test cases."""
    cases = [
        ("21606378341", "62333994201", "scout_ci_github_actions_job_201"),
        ("21606378341", "62333994302", "scout_ci_github_actions_job_302"),
        ("21606378341", "62333994180", "scout_ci_github_actions_job_180"),
        ("21668881266", "62471360701", "scout_ci_github_actions_job_701"),
        ("21668881266", "62471360829", "scout_ci_github_actions_job_829"),
    ]

    print("=" * 70)
    print("Extracting Scout CI logs and creating test cases")
    print("=" * 70)

    results = []
    for run_id, job_id, case_name in cases:
        success = extract_and_create_test_case(run_id, job_id, case_name)
        results.append((case_name, success))
        print()

    # Summary
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    for case_name, success in results:
        status = "✓ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {case_name}")

    success_count = sum(1 for _, s in results if s)
    print(f"\nTotal: {success_count}/{len(results)} successful")

    return 0 if success_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
