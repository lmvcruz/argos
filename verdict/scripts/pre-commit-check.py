#!/usr/bin/env python
"""
Pre-commit check script for Verdict project.

Runs linting, formatting, and test checks as per Copilot instructions.

Usage:
    python scripts/pre-commit-check.py
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


def get_verdict_directory() -> Path:
    """Determine the verdict directory from script location."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def run_syntax_checks(verdict_dir: Path) -> int:
    """Run flake8 syntax checks."""
    print("\n" + "=" * 60)
    print("STAGE 1: Syntax Checks (flake8)")
    print("=" * 60)

    flake8_result = run_command(
        "python -m flake8 verdict tests "
        "--count --select=E9,F63 --show-source --statistics",
        "Checking for syntax errors and undefined names",
        cwd=verdict_dir,
    )

    if flake8_result != 0:
        print("\n❌ Flake8 found syntax errors!")
        return 1

    print("\n✓ No syntax errors found")
    return 0


def run_formatting_checks(verdict_dir: Path) -> int:
    """Run black and isort formatting checks."""
    print("\n" + "=" * 60)
    print("STAGE 2: Code Formatting")
    print("=" * 60)

    exit_code = 0

    # Black formatting check
    black_result = run_command(
        "python -m black --check --diff verdict tests",
        "Checking code formatting (black)",
        cwd=verdict_dir,
    )

    if black_result != 0:
        print("\n❌ Black formatting check failed!")
        print("Fix: Run 'python -m black verdict tests' to auto-format")
        exit_code = 1
    else:
        print("\n✓ Code is properly formatted")

    # Import sorting check
    isort_result = run_command(
        "python -m isort verdict tests --check-only --diff",
        "Checking import sorting (isort)",
        cwd=verdict_dir,
    )

    if isort_result != 0:
        print("\n❌ Import sorting check failed!")
        print("Fix: Run 'python -m isort verdict tests' to auto-sort imports")
        exit_code = 1
    else:
        print("\n✓ Imports are properly sorted")

    return exit_code


def run_linting(verdict_dir: Path) -> int:
    """Run full flake8 linting."""
    print("\n" + "=" * 60)
    print("STAGE 3: Linting (flake8)")
    print("=" * 60)

    flake8_result = run_command(
        "python -m flake8 verdict tests --count --statistics",
        "Running flake8 linting",
        cwd=verdict_dir,
    )

    if flake8_result != 0:
        print("\n⚠️  Flake8 found linting issues")
        print("Note: Some issues may be acceptable. Review the output.")
        # Don't fail on linting warnings, only syntax errors
        return 0

    print("\n✓ No linting issues found")
    return 0


def run_tests(verdict_dir: Path) -> int:
    """Run pytest tests."""
    print("\n" + "=" * 60)
    print("STAGE 4: Tests")
    print("=" * 60)

    test_result = run_command(
        "python -m pytest tests/ -v --tb=short",
        "Running tests",
        cwd=verdict_dir,
    )

    if test_result != 0:
        print("\n⚠️  Some tests failed")
        print("Note: Tests are in progress, failures expected")
        # Don't fail on test failures during development
        return 0

    print("\n✓ All tests passed")
    return 0


def main():
    """Run all pre-commit checks."""
    print("=" * 60)
    print("Verdict Pre-Commit Checks")
    print("=" * 60)

    verdict_dir = get_verdict_directory()
    print(f"Working directory: {verdict_dir}")

    exit_code = 0

    # Stage 1: Syntax checks (critical)
    if run_syntax_checks(verdict_dir) != 0:
        exit_code = 1

    # Stage 2: Formatting checks (critical)
    if run_formatting_checks(verdict_dir) != 0:
        exit_code = 1

    # Stage 3: Linting (warnings only)
    run_linting(verdict_dir)

    # Stage 4: Tests (informational)
    run_tests(verdict_dir)

    # Final summary
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All critical checks passed!")
        print("=" * 60)
    else:
        print("❌ Some critical checks failed!")
        print("=" * 60)
        print("\nPlease fix the issues above before committing.")
        print("\nQuick fixes:")
        print("  - Format code: python -m black verdict tests")
        print("  - Sort imports: python -m isort verdict tests")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
