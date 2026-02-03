"""
Test script to verify quality comparison report functionality.

This script creates mock local and CI lint data to test the comparison
report generation.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import ExecutionDatabase, LintSummary, LintViolation
from generate_quality_report import generate_comparison_report


def create_test_data(db: ExecutionDatabase):
    """Create mock local and CI lint data for testing."""

    timestamp = datetime.now()

    # Local flake8 summary
    local_flake8_summary = LintSummary(
        execution_id="test-local-1-flake8",
        timestamp=timestamp,
        validator="flake8",
        files_scanned=10,
        total_violations=5,
        errors=2,
        warnings=3,
        info=0,
        by_code={"E501": 2, "W503": 3},
        space="local",
        metadata={}
    )
    db.insert_lint_summary(local_flake8_summary)

    # Local black summary
    local_black_summary = LintSummary(
        execution_id="test-local-1-black",
        timestamp=timestamp,
        validator="black",
        files_scanned=10,
        total_violations=8,
        errors=0,
        warnings=8,
        info=0,
        by_code={"would reformat": 8},
        space="local",
        metadata={}
    )
    db.insert_lint_summary(local_black_summary)

    # Local isort summary
    local_isort_summary = LintSummary(
        execution_id="test-local-1-isort",
        timestamp=timestamp,
        validator="isort",
        files_scanned=10,
        total_violations=3,
        errors=0,
        warnings=3,
        info=0,
        by_code={"imports incorrectly sorted": 3},
        space="local",
        metadata={}
    )
    db.insert_lint_summary(local_isort_summary)

    # CI flake8 summary
    ci_flake8_summary = LintSummary(
        execution_id="test-ci-1-flake8",
        timestamp=timestamp,
        validator="flake8",
        files_scanned=10,
        total_violations=15,
        errors=7,
        warnings=8,
        info=0,
        by_code={"E501": 5, "W503": 6, "E401": 4},
        space="ci",
        metadata={}
    )
    db.insert_lint_summary(ci_flake8_summary)

    # CI black summary
    ci_black_summary = LintSummary(
        execution_id="test-ci-1-black",
        timestamp=timestamp,
        validator="black",
        files_scanned=10,
        total_violations=12,
        errors=0,
        warnings=12,
        info=0,
        by_code={"would reformat": 12},
        space="ci",
        metadata={}
    )
    db.insert_lint_summary(ci_black_summary)

    # CI isort summary
    ci_isort_summary = LintSummary(
        execution_id="test-ci-1-isort",
        timestamp=timestamp,
        validator="isort",
        files_scanned=10,
        total_violations=7,
        errors=0,
        warnings=7,
        info=0,
        by_code={"imports incorrectly sorted": 7},
        space="ci",
        metadata={}
    )
    db.insert_lint_summary(ci_isort_summary)

    print("✅ Created test data:")
    print(f"   Local: 5 flake8 + 8 black + 3 isort = 16 total violations")
    print(f"   CI:   15 flake8 + 12 black + 7 isort = 34 total violations")
    print(f"   Diff: Local is better by 18 violations")


def main():
    """Test the comparison report generation."""
    test_db_path = ".anvil/test_comparison.db"

    # Remove test database if it exists
    if Path(test_db_path).exists():
        Path(test_db_path).unlink()

    # Create test database and data
    print("Creating test database...")
    db = ExecutionDatabase(test_db_path)
    create_test_data(db)

    # Generate comparison report
    print("\nGenerating comparison report...")
    html = generate_comparison_report(db)

    # Write to file
    output_path = "test-quality-comparison.html"
    Path(output_path).write_text(html, encoding="utf-8")

    print(f"\n✅ Test comparison report generated: {output_path}")
    print("\n📊 Expected results:")
    print("   • flake8: Local (5) vs CI (15) - Local better by 10 ✅")
    print("   • black:  Local (8) vs CI (12) - Local better by 4 ✅")
    print("   • isort:  Local (3) vs CI (7)  - Local better by 4 ✅")
    print("\n🌐 Open the HTML file in your browser to verify:")
    print(f"   file:///{Path(output_path).absolute()}")

    # Cleanup
    db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
