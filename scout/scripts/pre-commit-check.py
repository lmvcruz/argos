#!/usr/bin/env python
r"""
Pre-commit check script for Scout project.

Runs the same linting and formatting checks as the CI pipeline.
Can be used as a git pre-commit hook or run manually.

Usage:
    python scripts/pre-commit-check.py

To install as a git hook:
    python scripts/setup-git-hooks.py
"""

from pathlib import Path
import subprocess
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def run_command(cmd, description, cwd=None):
    """Run a command and return the exit code."""
    print(f"\n{description}...")
    print("-" * 60)
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def get_scout_directory() -> Path:
    """Determine the scout directory from script location."""
    script_path = Path(__file__).resolve()

    # If running from .git/hooks/pre-commit, go up to repo root then into scout
    if script_path.parent.name == "hooks" and script_path.parent.parent.name == ".git":
        return script_path.parent.parent.parent / "scout"

    # Running from scripts/ directory
    return script_path.parent.parent


def run_syntax_checks(scout_dir: Path) -> int:
    """Run flake8 syntax checks."""
    flake8_result = run_command(
        "python -m flake8 scout tests --count --select=E9,F63 --show-source --statistics",
        "Checking for syntax errors (flake8)",
        cwd=scout_dir,
    )

    if flake8_result != 0:
        print("\n❌ Flake8 found syntax errors!")
        print("Please fix the errors above before committing.")
        return 1

    print("\n✓ No syntax errors found")
    return 0


def run_formatting_checks(scout_dir: Path) -> int:
    """Run black and isort formatting checks."""
    exit_code = 0

    # Black formatting check
    black_result = run_command(
        "python -m black --check scout tests",
        "Checking code formatting (black)",
        cwd=scout_dir,
    )

    if black_result != 0:
        print("\n❌ Black formatting check failed!")
        print("Run 'python -m black scout tests' to auto-format your code.")
        exit_code = 1
    else:
        print("\n✓ Code is properly formatted")

    # Import sorting check
    isort_result = run_command(
        "python -m isort --check-only scout tests",
        "Checking import sorting (isort)",
        cwd=scout_dir,
    )

    if isort_result != 0:
        print("\n❌ Import sorting check failed!")
        print("Run 'python -m isort scout tests' to auto-sort imports.")
        exit_code = 1
    else:
        print("\n✓ Imports are properly sorted")

    return exit_code


def run_linting_checks(scout_dir: Path) -> int:
    """Run flake8 linting checks."""
    flake8_result = run_command(
        "python -m flake8 scout tests",
        "Running linting checks (flake8)",
        cwd=scout_dir,
    )

    if flake8_result != 0:
        print("\n❌ Flake8 linting check failed!")
        print("Please fix the linting errors above.")
        return 1

    print("\n✓ No linting errors found")
    return 0


def run_tests(scout_dir: Path) -> int:
    """Run pytest with coverage."""
    test_result = run_command(
        "python -m pytest tests/ -v --cov=scout --cov-report=term-missing",
        "Running tests with coverage",
        cwd=scout_dir,
    )

    if test_result != 0:
        print("\n❌ Tests failed!")
        print("Please fix the failing tests before committing.")
        return 1

    print("\n✓ All tests passed")
    return 0


def print_summary(results: dict):
    """Print a summary of all check results."""
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    all_passed = all(code == 0 for code in results.values())

    for check, code in results.items():
        status = "✓ PASS" if code == 0 else "✗ FAIL"
        print(f"{status}: {check}")

    print("-" * 70)

    if all_passed:
        print("✅ All checks passed!\n")
        return 0
    else:
        print("❌ Some checks failed. Please fix them before committing.\n")
        return 1


def main():
    """Run all pre-commit checks."""
    print("=" * 70)
    print("Scout Pre-Commit Checks")
    print("=" * 70)

    scout_dir = get_scout_directory()
    print(f"\nScout directory: {scout_dir}")

    # Run all checks
    results = {
        "Syntax errors (flake8)": run_syntax_checks(scout_dir),
        "Code formatting (black)": 0,  # Will be updated
        "Import sorting (isort)": 0,  # Will be updated
        "Linting (flake8)": run_linting_checks(scout_dir),
        "Tests and coverage": run_tests(scout_dir),
    }

    # Run formatting checks and update results
    formatting_code = run_formatting_checks(scout_dir)
    results["Code formatting (black)"] = formatting_code
    results["Import sorting (isort)"] = formatting_code

    # Print summary and exit
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
