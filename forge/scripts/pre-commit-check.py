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
import re
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


def get_forge_directory() -> Path:
    """Determine the forge directory from script location."""
    script_path = Path(__file__).resolve()

    # If running from .git/hooks/pre-commit, go up to repo root
    if script_path.parent.name == "hooks" and script_path.parent.parent.name == ".git":
        return script_path.parent.parent.parent

    # Running from scripts/ directory
    return script_path.parent.parent


def run_syntax_checks(forge_dir: Path) -> int:
    """Run flake8 syntax and Pyflakes checks."""
    flake8_result = run_command(
        "python -m flake8 . "
        "--count --select=E9,F --show-source --statistics "
        "--exclude=.git,__pycache__,.pytest_cache,.coverage,htmlcov,*.egg-info",
        "Checking for syntax errors and all Pyflakes issues (flake8)",
        cwd=forge_dir,
    )

    if flake8_result != 0:
        print("\n❌ Flake8 found syntax errors, undefined names, or other critical issues!")
        print("Please fix the errors above before committing.")
        return 1

    print("\n✓ No syntax errors or Pyflakes violations found")
    return 0


def run_formatting_checks(forge_dir: Path) -> int:
    """Run black and isort formatting checks."""
    exit_code = 0

    # Black formatting check
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

    # Import sorting check
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

    return exit_code


def run_complexity_checks(forge_dir: Path) -> int:
    """Run radon complexity and maintainability checks."""
    print("\nAnalyzing code complexity (radon)...")
    print("-" * 60)

    cc_result = run_command(
        "python -m radon cc . -nb --min C --exclude=tests,__pycache__,.pytest_cache",
        "Cyclomatic complexity check (B or better per function)",
        cwd=forge_dir,
    )

    mi_result = run_command(
        "python -m radon mi . -nb --min 50 --exclude=tests,__pycache__,.pytest_cache",
        "Maintainability index check (must be >= 50)",
        cwd=forge_dir,
    )

    if cc_result != 0 or mi_result != 0:
        print("\n✗ CODE COMPLEXITY CHECK FAILED!")
        print("  Fix functions with complexity C or worse, or maintainability < 50")
        return 1

    print("\n✓ Code complexity within acceptable limits (B or better per function)")
    return 0


def check_per_module_coverage(forge_dir: Path, min_coverage: float = 85.0) -> int:
    """
    Check that each module meets minimum coverage threshold.

    Args:
        forge_dir: Path to the forge directory
        min_coverage: Minimum coverage percentage required per module (default: 85%)

    Returns:
        0 if all modules meet threshold, 1 otherwise
    """
    print(f"\nChecking per-module coverage (minimum {min_coverage}%)...")
    print("-" * 60)

    # Run pytest with coverage to get detailed report
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "--cov=forge", "--cov-report=term"],
        cwd=forge_dir,
        capture_output=True,
        text=True,
    )

    # Parse coverage output to extract per-module coverage
    # Format: "module_name.py      statements   miss   cover   missing"
    coverage_pattern = r"^([\w/\\]+\.py)\s+(\d+)\s+(\d+)\s+([\d.]+)%"

    poorly_covered_modules = []
    for line in result.stdout.split("\n"):
        match = re.match(coverage_pattern, line.strip())
        if match:
            module_path = match.group(1)
            statements = int(match.group(2))
            coverage = float(match.group(4))

            # Skip empty modules (0 statements = 100% coverage is fine)
            if statements > 0 and coverage < min_coverage:
                poorly_covered_modules.append((module_path, coverage, statements))

    if poorly_covered_modules:
        print(f"\n❌ Found {len(poorly_covered_modules)} module(s) below {min_coverage}% coverage:")
        print(f"\n{'Module':<40} {'Coverage':>10} {'Statements':>12}")
        print("-" * 64)
        for module, coverage, statements in sorted(poorly_covered_modules, key=lambda x: x[1]):
            print(f"{module:<40} {coverage:>9.2f}% {statements:>12}")

        print(f"\n💡 Add tests for these modules to reach {min_coverage}% coverage per module")
        return 1

    print(f"\n✓ All modules meet {min_coverage}% coverage threshold")
    return 0


def main():
    """Run all pre-commit checks."""
    forge_dir = get_forge_directory()
    print(f"Running checks in: {forge_dir}")

    print("\n" + "=" * 60)
    print("RUNNING PRE-COMMIT CHECKS")
    print("=" * 60)

    exit_code = 0

    # Syntax checks
    exit_code |= run_syntax_checks(forge_dir)

    # Flake8 style check (warnings only)
    run_command(
        "python -m flake8 . "
        "--count --exit-zero --max-complexity=10 --max-line-length=127 "
        "--statistics --exclude=.git,__pycache__,.pytest_cache,.coverage,htmlcov,*.egg-info",
        "Checking code style (flake8 - warnings only)",
        cwd=forge_dir,
    )

    # Formatting checks
    exit_code |= run_formatting_checks(forge_dir)

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

    # Complexity checks
    exit_code |= run_complexity_checks(forge_dir)

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

    # Pylint check (respects pyproject.toml configuration)
    print("\nRunning pylint analysis...")
    print("-" * 60)
    run_command(
        "python -m pylint "
        "--max-line-length=100 --ignore=tests "
        "--exit-zero "
        "--recursive=y .",
        "Static analysis (pylint - respects pyproject.toml)",
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

    # Per-module coverage check
    module_coverage_result = check_per_module_coverage(forge_dir, min_coverage=85.0)
    if module_coverage_result != 0:
        exit_code = 1

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
