#!/usr/bin/env python
r"""
Pre-commit check script for Forge project.

Runs the same linting and formatting checks as the CI pipeline.
Can be used as a git pre-commit hook or run manually.

Usage:
    python scripts/pre-commit-check.py

To install as a git hook:
    # On Windows (PowerShell):
    New-Item -ItemType SymbolicLink -Path .git\hooks\pre-commit -Target ..\..\scripts\pre-commit-check.py

    # On Unix/Linux/Mac:
    ln -s ../../scripts/pre-commit-check.py .git/hooks/pre-commit
    chmod +x scripts/pre-commit-check.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, cwd=None):
    """Run a command and return the exit code."""
    print(f"\n{description}...")
    print("-" * 60)
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode


def main():
    """Run all pre-commit checks."""
    # Get the forge directory (parent of scripts, or 2 levels up if running from .git/hooks)
    script_path = Path(__file__).resolve()

    # If running from .git/hooks/pre-commit, go up to repo root
    if script_path.parent.name == "hooks" and script_path.parent.parent.name == ".git":
        forge_dir = script_path.parent.parent.parent
    else:
        # Running from scripts/ directory
        forge_dir = script_path.parent.parent

    print(f"Running checks in: {forge_dir}")

    # Check for Python syntax errors and undefined names
    print("\n" + "=" * 60)
    print("RUNNING PRE-COMMIT CHECKS")
    print("=" * 60)

    exit_code = 0

    # Flake8 syntax check
    flake8_result = run_command(
        "python -m flake8 . "
        "--count --select=E9,F63,F7,F82 --show-source --statistics "
        "--exclude=.git,__pycache__,.pytest_cache,.coverage,htmlcov,*.egg-info",
        "Checking for syntax errors (flake8)",
        cwd=forge_dir,
    )

    if flake8_result != 0:
        print("\n❌ Flake8 found syntax errors or undefined names!")
        print("Please fix the errors above before committing.")
        exit_code = 1
    else:
        print("\n✓ No syntax errors found")

    # Flake8 style check (warnings only)
    run_command(
        "python -m flake8 . "
        "--count --exit-zero --max-complexity=10 --max-line-length=127 "
        "--statistics --exclude=.git,__pycache__,.pytest_cache,.coverage,htmlcov,*.egg-info",
        "Checking code style (flake8 - warnings only)",
        cwd=forge_dir,
    )

    # Black formatting check
    # Build exclude pattern without problematic shell characters
    black_result = run_command(
        "python -m black --check --diff .",
        "Checking code formatting (black)",
        cwd=forge_dir,
    )

    if black_result != 0:
        print("\n❌ Black formatting check failed!")
        print(
            "Run 'python -m black .' in the forge directory to auto-format your code."
        )
        exit_code = 1
    else:
        print("\n✓ Code is properly formatted")

    # Summary
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above before committing.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
