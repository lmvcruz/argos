#!/usr/bin/env python3
"""
Pre-commit validation script for Anvil.

This script runs all quality checks before allowing a commit:
- Syntax errors (flake8)
- Code formatting (black)
- Import sorting (isort)
- Unused code (autoflake)
- Tests (pytest)
- Coverage threshold (90%)

Usage:
    python scripts/pre-commit-check.py [--verbose]

Options:
    --verbose    Show detailed output including skipped tests
"""

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(command, description, capture_output=False):
    """
    Run a shell command and return success status.

    Args:
        command: Command to run as list of strings
        description: Human-readable description of what's being checked
        capture_output: If True, capture and return output

    Returns:
        Tuple of (success, output) if capture_output=True, else just success boolean
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('=' * 70)

    if capture_output:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        # Print output
        print(output)

        success = result.returncode == 0
        if success:
            print(f"✓ {description} passed")
        else:
            print(f"✗ {description} failed")
        return success, output
    else:
        result = subprocess.run(command, cwd=Path(__file__).parent.parent)

        if result.returncode == 0:
            print(f"✓ {description} passed")
            return True
        else:
            print(f"✗ {description} failed")
            return False


def parse_test_output(output):
    """
    Parse pytest output to extract test statistics and coverage details.

    Args:
        output: Pytest output text

    Returns:
        Dict with passed, failed, skipped counts, skipped test names, and untested files
    """
    import re

    stats = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'skipped_tests': [],
        'untested_files': []
    }

    # Find final test summary line (e.g., "85 passed, 2 skipped in 15.15s")
    summary_pattern = r'(\d+) passed(?:, (\d+) failed)?(?:, (\d+) skipped)?'
    match = re.search(summary_pattern, output)
    if match:
        stats['passed'] = int(match.group(1))
        if match.group(2):
            stats['failed'] = int(match.group(2))
        if match.group(3):
            stats['skipped'] = int(match.group(3))

    # Find skipped test names
    skipped_pattern = r'tests/\S+::\S+ SKIPPED'
    for match in re.finditer(skipped_pattern, output):
        stats['skipped_tests'].append(match.group(0).replace(' SKIPPED', ''))

    # Find files with 0% coverage (untested files)
    # Pattern: "anvil\__main__.py                     3      3     0%   6-9"
    untested_pattern = r'(anvil[/\\]\S+\.py)\s+\d+\s+\d+\s+0%'
    for match in re.finditer(untested_pattern, output):
        file_path = match.group(1).replace('\\', '/')
        stats['untested_files'].append(file_path)

    return stats


def main():
    """Run all pre-commit checks."""
    parser = argparse.ArgumentParser(description='Run pre-commit validation checks')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Show detailed output including skipped tests')
    args = parser.parse_args()

    print("=" * 70)
    print("ANVIL PRE-COMMIT CHECKS")
    print("=" * 70)
    print(f"Platform: {platform.system()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    print("=" * 70)

    checks = [
        (
            ["python", "-m", "flake8", "anvil/", "tests/", "--count", "--statistics"],
            "Syntax errors (flake8)",
            False,
        ),
        (
            ["python", "-m", "black", "anvil/", "tests/", "--check"],
            "Code formatting (black)",
            False,
        ),
        (
            ["python", "-m", "isort", "anvil/", "tests/", "--check-only"],
            "Import sorting (isort)",
            False,
        ),
        (
            [
                "python",
                "-m",
                "autoflake",
                "--check",
                "--recursive",
                "--remove-all-unused-imports",
                "--remove-unused-variables",
                "--ignore-init-module-imports",
                "--exclude=tests/fixtures",  # Exclude test fixtures (intentionally malformed code)
                "anvil/",
                "tests/",
            ],
            "Unused code (autoflake)",
            False,
        ),
        (
            ["python", "-m", "pytest", "--cov=anvil", "--cov-fail-under=90", "-v" if args.verbose else ""],
            "Tests and coverage",
            True,  # Capture output to parse test stats
        ),
    ]

    results = []
    test_stats = None

    for command, description, capture in checks:
        # Remove empty strings from command
        command = [c for c in command if c]

        if capture:
            success, output = run_command(command, description, capture_output=True)
            results.append((description, success))

            # Parse test output
            if "Tests and coverage" in description:
                test_stats = parse_test_output(output)
        else:
            success = run_command(command, description)
            results.append((description, success))

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = True
    for description, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {description}")
        if not success:
            all_passed = False

    # Show test statistics
    if test_stats:
        print("\n" + "-" * 70)
        print("TEST STATISTICS")
        print("-" * 70)
        print(f"  Passed:  {test_stats['passed']}")
        print(f"  Failed:  {test_stats['failed']}")
        print(f"  Skipped: {test_stats['skipped']}")

        # Check for untested files (0% coverage)
        if test_stats['untested_files']:
            print(f"\n  ⚠️  WARNING: {len(test_stats['untested_files'])} file(s) with 0% coverage:")
            for file_path in test_stats['untested_files']:
                print(f"    - {file_path}")
            print("\n  Note: These files have no test coverage. Consider:")
            print("  - Adding tests for these files, or")
            print("  - Excluding them from coverage if they're entry points (e.g., __main__.py)")

        if test_stats['skipped'] > 0:
            print(f"\n  ⚠️  WARNING: {test_stats['skipped']} test(s) skipped on {platform.system()}")
            print("  These tests WILL run on GitHub Actions CI (Linux/macOS/Windows)")

            if args.verbose and test_stats['skipped_tests']:
                print("\n  Skipped tests:")
                for test in test_stats['skipped_tests']:
                    print(f"    - {test}")
            elif not args.verbose:
                print("  (Use --verbose to see which tests are skipped)")

            # Show platform-specific notes
            if platform.system() == "Windows":
                print("\n  Note: Symlink tests require elevated privileges on Windows")
                print("  and are skipped here, but will run on Linux/macOS CI")

    print("=" * 70)

    if all_passed:
        warnings = []
        if test_stats and test_stats['skipped'] > 0:
            warnings.append(f"{test_stats['skipped']} test(s) were skipped and will run on CI")
        if test_stats and test_stats['untested_files']:
            warnings.append(f"{len(test_stats['untested_files'])} file(s) have 0% coverage")

        if warnings:
            print("\n✅ All checks passed locally!")
            for warning in warnings:
                print(f"⚠️  Note: {warning}")
            print("   Make sure to check CI results after pushing")
        else:
            print("\n🎉 All checks passed! Ready to commit.")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues before committing.")
        print("\nQuick fixes:")
        print("  - Format code: python -m black anvil/ tests/")
        print("  - Sort imports: python -m isort anvil/ tests/")
        print("  - Remove unused: python -m autoflake --in-place --recursive "
              "--remove-all-unused-imports --remove-unused-variables "
              "--ignore-init-module-imports anvil/ tests/")
        return 1


if __name__ == "__main__":
    sys.exit(main())
