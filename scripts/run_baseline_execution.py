"""
Run baseline test execution to populate Anvil history database.

This script executes the full Argos test suite through PytestExecutorWithHistory
to establish baseline execution data for Phase 1.4 validation.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project roots to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import ExecutionDatabase
from anvil.executors.pytest_executor import PytestExecutorWithHistory


def main():
    """Run baseline test execution."""
    print("=" * 80)
    print("ARGOS BASELINE TEST EXECUTION - Phase 1.4")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project Root: {project_root}")

    # Database path
    db_path = project_root / ".anvil" / "history.db"
    print(f"Database: {db_path}")

    # Ensure .anvil directory exists
    db_path.parent.mkdir(exist_ok=True)

    # Initialize database and executor
    print("\n" + "-" * 80)
    print("Initializing database and executor...")
    db = ExecutionDatabase(str(db_path))
    executor = PytestExecutorWithHistory(db=db)

    # Test discovery patterns
    test_patterns = [
        "forge/tests",
        "anvil/tests",
        "scout/tests",
        # "lens/tests",  # Skip for now - no tests yet
    ]

    print(f"\nTest Patterns:")
    for pattern in test_patterns:
        print(f"  - {pattern}")

    # Run baseline execution
    print("\n" + "-" * 80)
    print("Running baseline test execution...")
    print("This may take several minutes...\n")

    start_time = time.time()
    execution_id = f"baseline-{int(start_time)}"

    try:
        result = executor.validate(
            test_patterns,
            config={
                'verbose': True,
                'capture': 'no',
                'color': 'yes',
                'timeout': 300,
                'space': 'local',
            },
            execution_id=execution_id
        )

        duration = time.time() - start_time

        # Get test counts from metadata
        metadata = result.metadata or {}
        total_tests = metadata.get('total', result.files_checked)
        passed = metadata.get('passed', 0)
        failed = len(result.errors)
        skipped = metadata.get('skipped', 0)

        # Print results
        print("\n" + "=" * 80)
        print("BASELINE EXECUTION RESULTS")
        print("=" * 80)
        print(f"\nExecution ID: {execution_id}")
        print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        print(f"\nTest Results:")
        print(f"  Total Tests: {total_tests}")
        if total_tests > 0:
            print(f"  Passed: {passed} ({passed/total_tests*100:.1f}%)")
        else:
            print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Skipped: {skipped}")
        print(f"\nValidation Success: {result.passed}")
        print(f"Files Checked: {result.files_checked}")

        # Database statistics
        print("\n" + "-" * 80)
        print("Database Statistics:")

        # Count total executions
        cursor = db.connection.execute(
            "SELECT COUNT(*) FROM execution_history"
        )
        total_executions = cursor.fetchone()[0]

        cursor = db.connection.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM execution_history"
        )
        unique_tests_db = cursor.fetchone()[0]

        cursor = db.connection.execute(
            "SELECT COUNT(*) FROM entity_statistics"
        )
        tracked_entities = cursor.fetchone()[0]

        print(f"  Total Executions Recorded: {total_executions}")
        print(f"  Unique Tests: {unique_tests_db}")
        print(f"  Tracked Entities: {tracked_entities}")

        # Save baseline report
        report_path = project_root / "docs" / "baseline-execution-phase-1.4.md"
        print(f"\n" + "-" * 80)
        print(f"Saving baseline report: {report_path}")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Baseline Test Execution - Phase 1.4\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Execution Summary\n\n")
            f.write(f"- **Execution ID**: `{execution_id}`\n")
            f.write(f"- **Duration**: {duration:.2f} seconds ({duration/60:.2f} minutes)\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            if total_tests > 0:
                f.write(f"- **Passed**: {passed} ({passed/total_tests*100:.1f}%)\n")
            else:
                f.write(f"- **Passed**: {passed}\n")
            f.write(f"- **Failed**: {failed}\n")
            f.write(f"- **Skipped**: {skipped}\n")
            f.write(f"- **Validation Success**: {result.passed}\n\n")
            f.write(f"## Database Statistics\n\n")
            f.write(f"- **Total Executions Recorded**: {total_executions}\n")
            f.write(f"- **Unique Tests**: {unique_tests_db}\n")
            f.write(f"- **Tracked Entities**: {tracked_entities}\n\n")
            f.write(f"## Test Patterns\n\n")
            for pattern in test_patterns:
                f.write(f"- `{pattern}`\n")
            f.write(f"\n## Purpose\n\n")
            f.write(f"This baseline execution establishes the initial dataset for:\n\n")
            f.write(f"1. Selective execution validation\n")
            f.write(f"2. Performance comparison\n")
            f.write(f"3. Flaky test detection\n")
            f.write(f"4. Statistics calculation\n")
            f.write(f"5. Report generation\n\n")
            f.write(f"## Next Steps\n\n")
            f.write(f"1. Run selective execution rules (argos-commit-check, etc.)\n")
            f.write(f"2. Compare execution times\n")
            f.write(f"3. Validate rule criteria\n")
            f.write(f"4. Generate execution reports\n")

        print("Baseline report saved")
        print("\n" + "=" * 80)
        print("BASELINE EXECUTION COMPLETE")
        print("=" * 80)

        return 0 if result.passed else 1

    except Exception as e:
        print(f"\nError during baseline execution: {e}")
        import traceback
        traceback.print_exc()
        return 2

    finally:
        # Clean up
        print("\nCleaning up...")
        executor.close()
        db.close()
        print("Database closed")


if __name__ == "__main__":
    sys.exit(main())
