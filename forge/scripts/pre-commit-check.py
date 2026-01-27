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
        print("Run 'python -m black .' in the forge directory to auto-format your code.")
        exit_code = 1
    else:
        print("\n✓ Code is properly formatted")

    # Import sorting check (isort)
    isort_result = run_command(
        "python -m isort . --check-only --diff",
        "Checking import sorting (isort)",
        cwd=forge_dir,
    )

    if isort_result != 0:
        print("\n❌ Import sorting check failed!")
        print("Run 'python -m isort .' in the forge directory to auto-sort imports.")
        exit_code = 1
    else:
        print("\n✓ Imports are properly sorted")

    # Unused imports/variables check (autoflake)
    print("\nChecking for unused imports and variables (autoflake)...")
    print("-" * 60)
    autoflake_result = run_command(
        "python -m autoflake --check --recursive "
        "--remove-all-unused-imports --remove-unused-variables "
        "--ignore-init-module-imports .",
        "Checking for unused imports/variables (autoflake - warnings only)",
        cwd=forge_dir,
    )
    # Note: autoflake is informational only, doesn't fail the build
    if autoflake_result != 0:
        print("\n⚠ Autoflake found unused imports or variables (non-blocking)")
    else:
        print("\n✓ No unused imports or variables found")

    # Code complexity check (radon) - now enforced with min thresholds
    print("\nAnalyzing code complexity (radon)...")
    print("-" * 60)
    cc_result = run_command(
        "python -m radon cc . -a -nb --min B --exclude=tests,__pycache__,.pytest_cache",
        "Cyclomatic complexity check (must be B or better)",
        cwd=forge_dir,
    )

    mi_result = run_command(
        "python -m radon mi . -nb --min 20 --exclude=tests,__pycache__,.pytest_cache",
        "Maintainability index check (must be >= 20)",
        cwd=forge_dir,
    )

    if cc_result != 0 or mi_result != 0:
        print("\n✗ CODE COMPLEXITY CHECK FAILED!")
        print("  Fix functions with complexity C or worse, or maintainability < 20")
        exit_code = 1
    else:
        print("\n✓ Code complexity within acceptable limits (B or better)")

    # Dead code detection (vulture)
    print("\nScanning for dead code (vulture)...")
    print("-" * 60)
    vulture_result = run_command(
        "python -m vulture . --min-confidence 80 "
        "--exclude=tests,__pycache__,.pytest_cache,.venv,venv",
        "Dead code detection (vulture - warnings only)",
        cwd=forge_dir,
    )
    # Vulture is informational only
    if vulture_result != 0:
        print("\n⚠ Vulture found potential dead code (non-blocking)")
    else:
        print("\n✓ No dead code detected")

    # Pylint check (selected rules only)
    print("\nRunning pylint analysis...")
    print("-" * 60)
    run_command(
        "python -m pylint --disable=all "
        "--enable=unused-import,unused-variable,unused-argument,unreachable,"
        "dangerous-default-value,redefined-builtin,import-error "
        "--max-line-length=100 --ignore=tests "
        "--exit-zero "
        "--recursive=y .",
        "Static analysis (pylint - selected checks)",
        cwd=forge_dir,
    )
    # Pylint is informational only
    print("\n✓ Pylint analysis complete (informational)")

    # Run tests
    test_result = run_command(
        "python -m pytest tests/ -v --tb=short",
        "Running tests (pytest)",
        cwd=forge_dir,
    )

    if test_result != 0:
        print("\n❌ Tests failed!")
        print("Please fix the failing tests before committing.")
        exit_code = 1
    else:
        print("\n✓ All tests passed")

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
