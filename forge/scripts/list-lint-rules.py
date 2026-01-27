#!/usr/bin/env python3
"""
List all active and available linting rules.

This script queries all linting tools to show:
- Currently active/enabled rules
- Available rules that are disabled
- Configuration source for each rule
"""

import subprocess
import sys
from pathlib import Path


def print_section(title: str, symbol: str = "=") -> None:
    """Print a formatted section header."""
    print(f"\n{symbol * 70}")
    print(f"{title}")
    print(f"{symbol * 70}\n")


def run_command(cmd: list[str]) -> tuple[str, int]:
    """Run a command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout + result.stderr, result.returncode
    except Exception as e:
        return f"Error running command: {e}", 1


def list_flake8_rules():
    """List Flake8 error codes and plugins."""
    print_section("FLAKE8 RULES", "=")

    # Show version and plugins
    output, _ = run_command(["python", "-m", "flake8", "--version"])
    print("Installed Plugins:")
    print(output)

    print("\nActive Configuration (from pre-commit script):")
    print("  Blocking: E9,F63,F7,F82 (syntax errors)")
    print("  Informational: All except E501 (line length)")

    print("\nError Code Categories:")
    print("  E1xx: Indentation")
    print("  E2xx: Whitespace")
    print("  E3xx: Blank lines")
    print("  E4xx: Imports")
    print("  E5xx: Line length")
    print("  E7xx: Statements")
    print("  E9xx: Runtime errors")
    print("  W1xx: Indentation warnings")
    print("  W2xx: Whitespace warnings")
    print("  W3xx: Blank line warnings")
    print("  W5xx: Line break warnings")
    print("  W6xx: Deprecated features")
    print("  F4xx: Import issues")
    print("  F6xx: Name issues")
    print("  F7xx: Syntax errors")
    print("  F8xx: Name undefined/unused")
    print("  F9xx: Miscellaneous")


def list_pylint_rules():
    """List Pylint rules (enabled and available)."""
    print_section("PYLINT RULES", "=")

    print("Currently Enabled (in pre-commit):")
    enabled = [
        "unused-import (W0611)",
        "unused-variable (W0612)",
        "unused-argument (W0613)",
        "unreachable (W0101)",
        "dangerous-default-value (W0102)",
        "redefined-builtin (W0622)",
        "import-error (E0401)",
    ]
    for rule in enabled:
        print(f"  ✓ {rule}")

    print("\nDisabled in pyproject.toml:")
    disabled = [
        "C0111 - missing-docstring",
        "C0103 - invalid-name",
        "R0903 - too-few-public-methods",
        "R0913 - too-many-arguments",
        "W0212 - protected-access (for tests)",
    ]
    for rule in disabled:
        print(f"  ✗ {rule}")

    print("\nDesign Thresholds:")
    print("  max-args: 7")
    print("  max-attributes: 10")
    print("  max-branches: 15")
    print("  max-locals: 20")
    print("  max-returns: 8")
    print("  max-statements: 60")

    print("\n" + "-" * 70)
    print("Full message list available with: python -m pylint --list-msgs")
    print("Message categories: Convention (C), Refactor (R), Warning (W), Error (E), Fatal (F)")


def list_mypy_rules():
    """List Mypy configuration."""
    print_section("MYPY CONFIGURATION", "=")

    print("Active Settings (from pyproject.toml):")
    settings = {
        "warn_return_any": "✓ Warn about returning Any",
        "warn_unused_configs": "✓ Warn about unused config",
        "disallow_untyped_defs": "✗ Don't require type hints (flexible)",
        "check_untyped_defs": "✓ Type-check untyped functions",
        "no_implicit_optional": "✓ Explicit Optional required",
        "warn_redundant_casts": "✓ Warn about unnecessary casts",
        "warn_unused_ignores": "✓ Warn about unused # type: ignore",
        "warn_no_return": "✓ Warn about missing returns",
        "strict_equality": "✓ Strict equality type checking",
    }

    for option, description in settings.items():
        print(f"  {description}")

    print("\n" + "-" * 70)
    print("All options available with: python -m mypy --help")


def list_black_config():
    """List Black configuration."""
    print_section("BLACK CONFIGURATION", "=")

    print("Philosophy: Opinionated formatter with minimal configuration")
    print("\nActive Settings:")
    print("  line-length: 100 characters")
    print("  target-version: Python 3.11")
    print("\nNote: Black enforces a single style - no rules to enable/disable")


def list_isort_config():
    """List isort configuration."""
    print_section("ISORT CONFIGURATION", "=")

    print("Active Settings:")
    print("  profile: black (compatible with Black)")
    print("  line_length: 100")
    print("  force_sort_within_sections: true")

    print("\nImport Sections (in order):")
    sections = [
        "1. FUTURE - from __future__ import ...",
        "2. STDLIB - Python standard library",
        "3. THIRDPARTY - Third-party packages",
        "4. FIRSTPARTY - forge package",
        "5. LOCALFOLDER - Relative imports",
    ]
    for section in sections:
        print(f"  {section}")


def list_radon_config():
    """List Radon complexity configuration."""
    print_section("RADON COMPLEXITY THRESHOLDS", "=")

    print("Active Thresholds (BLOCKING):")
    print("  cc_min: B (complexity must be ≤ 10)")
    print("  mi_min: 20 (maintainability index must be ≥ 20)")

    print("\nComplexity Scale:")
    scale = [
        ("A", "1-5", "Low", "✓ PASS"),
        ("B", "6-10", "Moderate", "✓ PASS"),
        ("C", "11-20", "Moderate-High", "✗ FAIL"),
        ("D", "21-30", "High", "✗ FAIL"),
        ("E", "31-40", "Very High", "✗ FAIL"),
        ("F", "41+", "Extremely High", "✗ FAIL"),
    ]

    print(f"\n{'Rating':<8} {'Complexity':<12} {'Risk':<15} {'Status':<10}")
    print("-" * 50)
    for rating, complexity, risk, status in scale:
        print(f"{rating:<8} {complexity:<12} {risk:<15} {status:<10}")

    print("\nMaintainability Index Scale:")
    print("  100-80: Highly maintainable (Excellent)")
    print("   79-50: Moderately maintainable (Good)")
    print("   49-20: Difficult to maintain (Warning) ⚠")
    print("   19-0:  Unmaintainable (BLOCKED) ✗")


def list_vulture_config():
    """List Vulture configuration."""
    print_section("VULTURE CONFIGURATION", "=")

    print("Active Settings (INFORMATIONAL ONLY):")
    print("  min_confidence: 80% (only high-confidence dead code)")
    print("  sort_by_size: true")

    print("\nIgnored Decorators:")
    print("  @pytest.fixture")
    print("  @dataclass")

    print("\nWhat Vulture Detects:")
    print("  • Unused functions, classes, methods")
    print("  • Unused variables and properties")
    print("  • Unreachable code")
    print("  • Unused imports")


def list_autoflake_config():
    """List autoflake configuration."""
    print_section("AUTOFLAKE CONFIGURATION", "=")

    print("Active Checks (INFORMATIONAL ONLY):")
    print("  --remove-all-unused-imports: Detect unused imports")
    print("  --remove-unused-variables: Detect unused variables")
    print("  --check: Don't modify, just report")

    print("\nWhat Autoflake Detects:")
    print("  • Unused imports")
    print("  • Unused local variables")
    print("  • Duplicate dictionary keys")


def show_commands_to_list_rules():
    """Show commands to list all available rules."""
    print_section("COMMANDS TO LIST ALL AVAILABLE RULES", "=")

    commands = [
        ("Flake8", "python -m flake8 --help"),
        ("Flake8 Stats", "python -m flake8 . --statistics"),
        ("Pylint All", "python -m pylint --list-msgs"),
        ("Pylint Enabled", "python -m pylint --list-msgs-enabled"),
        ("Mypy Options", "python -m mypy --help"),
        ("Radon CC", "python -m radon cc . -a --total-average"),
        ("Radon MI", "python -m radon mi . --show"),
        ("Vulture", "python -m vulture . --min-confidence 60"),
    ]

    print("Run these commands to see full details:\n")
    for tool, command in commands:
        print(f"  {tool:<15} {command}")


def main():
    """Main entry point."""
    print_section("LINTING RULES SUMMARY", "=")
    print("Generated from: scripts/list-lint-rules.py")
    print(f"Project: {Path.cwd().name}")

    list_flake8_rules()
    list_pylint_rules()
    list_mypy_rules()
    list_black_config()
    list_isort_config()
    list_radon_config()
    list_vulture_config()
    list_autoflake_config()
    show_commands_to_list_rules()

    print_section("SUMMARY", "=")
    print("✓ BLOCKING CHECKS:")
    print("  • Flake8: Syntax errors (E9, F63, F7, F82)")
    print("  • Black: Code formatting (line length 100)")
    print("  • Isort: Import sorting (5 sections)")
    print("  • Radon: Complexity B or better (≤10), MI ≥20")
    print("  • Tests: All unit tests must pass")

    print("\n⚠ INFORMATIONAL CHECKS:")
    print("  • Flake8: Style warnings (~80 codes)")
    print("  • Pylint: Selected rules (7 enabled)")
    print("  • Autoflake: Unused imports/variables")
    print("  • Vulture: Dead code (80% confidence)")

    print("\nFor detailed documentation, see: docs/linting-rules.md")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
