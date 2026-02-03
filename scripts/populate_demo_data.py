"""
Quick demo script to populate Anvil database with test execution data.
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add anvil to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory, EntityStatistics


def populate_demo_data():
    """Populate database with demo test execution data."""
    print("=" * 80)
    print("POPULATING ANVIL DATABASE WITH DEMO DATA")
    print("=" * 80)

    db_path = project_root / ".anvil" / "history.db"
    print(f"\nDatabase: {db_path}")

    # Ensure .anvil directory exists
    db_path.parent.mkdir(exist_ok=True)

    # Initialize database
    db = ExecutionDatabase(str(db_path))

    # Sample test entities
    test_entities = [
        "anvil/tests/test_execution_schema.py::TestExecutionDatabase::test_create_schema",
        "anvil/tests/test_execution_schema.py::TestExecutionDatabase::test_insert_history",
        "anvil/tests/test_execution_schema.py::TestExecutionHistory::test_create_history",
        "anvil/tests/test_rule_engine.py::TestRuleEngine::test_select_all",
        "anvil/tests/test_rule_engine.py::TestRuleEngine::test_select_by_group",
        "anvil/tests/test_rule_engine.py::TestRuleEngine::test_select_failed_in_last",
        "anvil/tests/test_statistics_calculator.py::TestStatistics::test_calculate_stats",
        "anvil/tests/test_statistics_calculator.py::TestStatistics::test_flaky_detection",
        "forge/tests/test_argument_parser.py::TestParser::test_basic_parsing",
        "forge/tests/test_argument_parser.py::TestParser::test_error_handling",
        "forge/tests/test_models.py::TestModels::test_metadata_creation",
        "forge/tests/test_models.py::TestModels::test_validation",
        "scout/tests/test_parser.py::TestCIParser::test_parse_logs",
        "scout/tests/test_parser.py::TestCIParser::test_failure_detection",
        "scout/tests/test_models.py::TestModels::test_run_creation",
    ]

    # Create some flaky tests (intermittent failures)
    flaky_tests = [
        "anvil/tests/test_execution_schema.py::TestExecutionDatabase::test_insert_history",
        "forge/tests/test_argument_parser.py::TestParser::test_error_handling",
        "scout/tests/test_parser.py::TestCIParser::test_failure_detection",
    ]

    # Generate 30 days of execution history
    base_time = datetime.now() - timedelta(days=30)
    execution_count = 0

    print("\nGenerating execution history...")
    print(f"- Time range: Last 30 days")
    print(f"- Test entities: {len(test_entities)}")
    print(f"- Executions per day: ~3-5")

    for day in range(30):
        # 3-5 executions per day
        daily_executions = random.randint(3, 5)

        for exec_num in range(daily_executions):
            execution_id = f"local-{int((base_time + timedelta(days=day, hours=exec_num)).timestamp())}"
            timestamp = base_time + timedelta(days=day, hours=exec_num * 2)

            # Run each test entity
            for entity_id in test_entities:
                # Determine if this test passes or fails
                if entity_id in flaky_tests:
                    # Flaky tests fail 10% of the time
                    status = "FAILED" if random.random() < 0.10 else "PASSED"
                else:
                    # Normal tests fail 2% of the time
                    status = "FAILED" if random.random() < 0.02 else "PASSED"

                # Random duration between 0.1 and 3.0 seconds
                duration = random.uniform(0.1, 3.0)

                # Create execution history record
                history = ExecutionHistory(
                    execution_id=execution_id,
                    entity_id=entity_id,
                    entity_type="test",
                    timestamp=timestamp,
                    status=status,
                    duration=duration,
                    space="local",
                    metadata={"demo": True}
                )

                db.insert_execution_history(history)
                execution_count += 1

    print(f"\n✓ Created {execution_count} execution history records")

    # Calculate and update statistics
    print("\nCalculating entity statistics...")

    from anvil.core.statistics_calculator import StatisticsCalculator
    calculator = StatisticsCalculator(db)

    all_stats = calculator.calculate_all_stats(entity_type="test", window=None)

    for stats in all_stats:
        db.update_entity_statistics(stats)

    print(f"✓ Updated statistics for {len(all_stats)} entities")

    # Print summary
    print("\n" + "=" * 80)
    print("DATABASE POPULATED SUCCESSFULLY")
    print("=" * 80)

    # Query some stats
    cursor = db.connection.execute(
        "SELECT COUNT(*) FROM execution_history"
    )
    total_executions = cursor.fetchone()[0]

    cursor = db.connection.execute(
        "SELECT COUNT(DISTINCT entity_id) FROM execution_history"
    )
    unique_tests = cursor.fetchone()[0]

    cursor = db.connection.execute(
        "SELECT COUNT(*) FROM entity_statistics WHERE failure_rate >= 0.05"
    )
    flaky_count = cursor.fetchone()[0]

    print(f"\nDatabase Statistics:")
    print(f"  Total Executions: {total_executions}")
    print(f"  Unique Tests: {unique_tests}")
    print(f"  Flaky Tests (≥5% failure rate): {flaky_count}")

    # Close database
    db.close()

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. View test statistics:")
    print("   cd anvil")
    print("   anvil stats show --type test")
    print("\n2. Find flaky tests:")
    print("   anvil stats flaky-tests --threshold 0.05")
    print("\n3. Generate Lens report:")
    print("   cd ../lens")
    print("   lens report test-execution --format html --output demo-report.html")
    print("   start demo-report.html")
    print()


if __name__ == "__main__":
    populate_demo_data()
