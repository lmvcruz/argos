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
    python scripts/pre-commit-check.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """
    Run a shell command and return success status.

    Args:
        command: Command to run as list of strings
        description: Human-readable description of what's being checked

    Returns:
        True if command succeeded, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('=' * 70)

    result = subprocess.run(command, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print(f"✓ {description} passed")
        return True
    else:
        print(f"✗ {description} failed")
        return False


def main():
    """Run all pre-commit checks."""
    print("=" * 70)
    print("ANVIL PRE-COMMIT CHECKS")
    print("=" * 70)

    checks = [
        (
            ["python", "-m", "flake8", "anvil/", "tests/", "--count", "--statistics"],
            "Syntax errors (flake8)",
        ),
        (
            ["python", "-m", "black", "anvil/", "tests/", "--check"],
            "Code formatting (black)",
        ),
        (
            ["python", "-m", "isort", "anvil/", "tests/", "--check-only"],
            "Import sorting (isort)",
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
                "anvil/",
                "tests/",
            ],
            "Unused code (autoflake)",
        ),
        (
            ["python", "-m", "pytest", "--cov=anvil", "--cov-fail-under=90"],
            "Tests and coverage",
        ),
    ]

    results = []
    for command, description in checks:
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

    print("=" * 70)

    if all_passed:
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
