"""
Tests for RuleEngine and StatisticsCalculator.

Following TDD principles: Tests written before full implementation.
"""

from datetime import datetime, timedelta

import pytest

from anvil.core.rule_engine import RuleEngine
from anvil.core.statistics_calculator import StatisticsCalculator
from anvil.storage.execution_schema import (
    ExecutionDatabase,
    ExecutionHistory,
    ExecutionRule,
)


class TestStatisticsCalculator:
    """Test suite for StatisticsCalculator."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def calculator(self, db):
        """Create StatisticsCalculator instance."""
        return StatisticsCalculator(db)

    @pytest.fixture
    def sample_history(self, db):
        """Insert sample execution history."""
        now = datetime.now()
        records = [
            # Test that always passes (10 runs)
            *[
                ExecutionHistory(
                    execution_id=f"local-{i}",
                    entity_id="tests/test_stable.py::test_always_passes",
                    entity_type="test",
                    timestamp=now - timedelta(hours=i),
                    status="PASSED",
                    duration=1.0 + (i * 0.1),
                )
                for i in range(10)
            ],
            # Test with 50% failure rate (10 runs, 5 fail)
            *[
                ExecutionHistory(
                    execution_id=f"local-{10 + i}",
                    entity_id="tests/test_flaky.py::test_sometimes_fails",
                    entity_type="test",
                    timestamp=now - timedelta(hours=i),
                    status="FAILED" if i % 2 == 0 else "PASSED",
                    duration=2.0,
                )
                for i in range(10)
            ],
            # Test with recent failures (last 3 failed)
            *[
                ExecutionHistory(
                    execution_id=f"local-{20 + i}",
                    entity_id="tests/test_recent_fail.py::test_recent_failures",
                    entity_type="test",
                    timestamp=now - timedelta(hours=i),
                    status="FAILED" if i < 3 else "PASSED",
                    duration=1.5,
                )
                for i in range(10)
            ],
        ]

        for record in records:
            db.insert_execution_history(record)

        return records

    def test_calculate_entity_stats_stable_test(self, calculator, sample_history):
        """Test statistics calculation for stable test (100% pass rate)."""
        stats = calculator.calculate_entity_stats("tests/test_stable.py::test_always_passes")

        assert stats is not None
        assert stats.entity_id == "tests/test_stable.py::test_always_passes"
        assert stats.entity_type == "test"
        assert stats.total_runs == 10
        assert stats.passed == 10
        assert stats.failed == 0
        assert stats.skipped == 0
        assert stats.failure_rate == 0.0
        assert stats.avg_duration == pytest.approx(1.45, rel=0.1)  # Average of 1.0-1.9
        assert stats.last_failure is None

    def test_calculate_entity_stats_flaky_test(self, calculator, sample_history):
        """Test statistics calculation for flaky test (50% failure rate)."""
        stats = calculator.calculate_entity_stats("tests/test_flaky.py::test_sometimes_fails")

        assert stats is not None
        assert stats.total_runs == 10
        assert stats.passed == 5
        assert stats.failed == 5
        assert stats.failure_rate == 0.5
        assert stats.avg_duration == pytest.approx(2.0)
        assert stats.last_failure is not None

    def test_calculate_entity_stats_with_window(self, calculator, sample_history):
        """Test statistics calculation with limited window."""
        # Only consider last 5 runs
        stats = calculator.calculate_entity_stats(
            "tests/test_recent_fail.py::test_recent_failures", window=5
        )

        assert stats is not None
        assert stats.total_runs == 5
        # Last 5 runs: 3 failed, 2 passed
        assert stats.failed == 3
        assert stats.passed == 2
        assert stats.failure_rate == 0.6

    def test_calculate_entity_stats_nonexistent(self, calculator):
        """Test statistics for nonexistent entity."""
        stats = calculator.calculate_entity_stats("tests/nonexistent.py::test_missing")
        assert stats is None

    def test_calculate_all_stats(self, calculator, sample_history):
        """Test calculation of all entity statistics."""
        all_stats = calculator.calculate_all_stats(entity_type="test")

        assert len(all_stats) == 3
        entity_ids = {stat.entity_id for stat in all_stats}
        assert "tests/test_stable.py::test_always_passes" in entity_ids
        assert "tests/test_flaky.py::test_sometimes_fails" in entity_ids
        assert "tests/test_recent_fail.py::test_recent_failures" in entity_ids

    def test_get_flaky_entities(self, calculator, sample_history):
        """Test identification of flaky entities."""
        # Threshold of 30% failure rate
        flaky = calculator.get_flaky_entities(threshold=0.3, window=None)

        # Should find test with 50% failure rate
        entity_ids = [stat.entity_id for stat in flaky]
        assert "tests/test_flaky.py::test_sometimes_fails" in entity_ids
        assert "tests/test_stable.py::test_always_passes" not in entity_ids

    def test_get_flaky_entities_with_window(self, calculator, sample_history):
        """Test flaky entity detection with window."""
        # Last 5 runs, threshold 50%
        flaky = calculator.get_flaky_entities(threshold=0.5, window=5)

        entity_ids = [stat.entity_id for stat in flaky]
        # test_recent_failures: 3/5 = 60% failure rate (flaky)
        assert "tests/test_recent_fail.py::test_recent_failures" in entity_ids

    def test_get_failed_in_last_n(self, calculator, sample_history):
        """Test retrieval of entities that failed in last N runs."""
        failed = calculator.get_failed_in_last_n(n=3)

        entity_ids = [eid for eid in failed]
        # test_recent_failures failed in last 3 runs
        assert "tests/test_recent_fail.py::test_recent_failures" in entity_ids
        # test_stable never failed
        assert "tests/test_stable.py::test_always_passes" not in entity_ids


class TestRuleEngine:
    """Test suite for RuleEngine."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def engine(self, db):
        """Create RuleEngine instance."""
        return RuleEngine(db)

    @pytest.fixture
    def sample_rules(self, db):
        """Insert sample execution rules."""
        rules = [
            ExecutionRule(
                name="baseline-all",
                criteria="all",
                enabled=True,
            ),
            ExecutionRule(
                name="quick-check",
                criteria="group",
                enabled=True,
                groups=[
                    "tests/test_models.py",
                    "tests/test_parser.py",
                    "tests/test_executor.py",
                ],
            ),
            ExecutionRule(
                name="failed-only",
                criteria="failed-in-last",
                enabled=True,
                window=1,
            ),
            ExecutionRule(
                name="flaky-tests",
                criteria="failure-rate",
                enabled=True,
                threshold=0.10,
                window=20,
            ),
            ExecutionRule(
                name="disabled-rule",
                criteria="all",
                enabled=False,
            ),
        ]

        for rule in rules:
            db.insert_execution_rule(rule)

        return rules

    @pytest.fixture
    def sample_history(self, db):
        """Insert sample execution history for rule engine tests."""
        now = datetime.now()
        records = [
            # test_models.py (in quick-check group, always passes)
            ExecutionHistory(
                execution_id="local-1",
                entity_id="tests/test_models.py::test_create_model",
                entity_type="test",
                timestamp=now - timedelta(hours=1),
                status="PASSED",
                duration=1.0,
            ),
            # test_parser.py (in quick-check group, failed last run)
            ExecutionHistory(
                execution_id="local-2",
                entity_id="tests/test_parser.py::test_parse_output",
                entity_type="test",
                timestamp=now,
                status="FAILED",
                duration=2.0,
            ),
            # test_other.py (not in any group, passed)
            ExecutionHistory(
                execution_id="local-3",
                entity_id="tests/test_other.py::test_something",
                entity_type="test",
                timestamp=now,
                status="PASSED",
                duration=0.5,
            ),
        ]

        for record in records:
            db.insert_execution_history(record)

        return records

    def test_select_all_entities(self, engine, sample_history):
        """Test selection of all entities."""
        rule = ExecutionRule(name="test-all", criteria="all")
        entities = engine.select_entities(rule)

        # Should select all unique entities from history
        assert len(entities) >= 3
        assert "tests/test_models.py::test_create_model" in entities
        assert "tests/test_parser.py::test_parse_output" in entities
        assert "tests/test_other.py::test_something" in entities

    def test_select_by_group(self, engine, sample_rules, sample_history):
        """Test selection by group patterns."""
        rule = engine.db.get_execution_rule("quick-check")
        entities = engine.select_entities(rule)

        # Should only select entities matching group patterns
        assert "tests/test_models.py" in str(entities) or any(
            "test_models.py" in e for e in entities
        )
        # test_other.py should not be selected
        assert not any("test_other.py" in e for e in entities)

    def test_select_failed_in_last(self, engine, sample_rules, sample_history):
        """Test selection of entities that failed in last run."""
        rule = engine.db.get_execution_rule("failed-only")
        entities = engine.select_entities(rule)

        # Should only select test_parser.py which failed
        assert "tests/test_parser.py::test_parse_output" in entities
        assert "tests/test_models.py::test_create_model" not in entities

    def test_select_by_failure_rate(self, engine, db, sample_rules):
        """Test selection by failure rate threshold."""
        # Insert test with high failure rate
        now = datetime.now()
        for i in range(10):
            db.insert_execution_history(
                ExecutionHistory(
                    execution_id=f"local-flaky-{i}",
                    entity_id="tests/test_flaky.py::test_unreliable",
                    entity_type="test",
                    timestamp=now - timedelta(hours=i),
                    status="FAILED" if i < 3 else "PASSED",  # 30% failure rate
                    duration=1.0,
                )
            )

        rule = engine.db.get_execution_rule("flaky-tests")
        entities = engine.select_entities(rule)

        # Should select test with 30% failure rate (threshold is 10%)
        assert "tests/test_flaky.py::test_unreliable" in entities

    def test_get_rule(self, engine, sample_rules):
        """Test retrieval of execution rule."""
        rule = engine.get_rule("quick-check")
        assert rule is not None
        assert rule.name == "quick-check"
        assert rule.criteria == "group"
        assert len(rule.groups) == 3

    def test_get_nonexistent_rule(self, engine):
        """Test retrieval of nonexistent rule."""
        rule = engine.get_rule("nonexistent")
        assert rule is None

    def test_list_rules(self, engine, sample_rules):
        """Test listing all rules."""
        rules = engine.list_rules()
        assert len(rules) >= 5
        rule_names = {rule.name for rule in rules}
        assert "baseline-all" in rule_names
        assert "quick-check" in rule_names

    def test_list_enabled_rules_only(self, engine, sample_rules):
        """Test listing only enabled rules."""
        rules = engine.list_rules(enabled_only=True)
        rule_names = {rule.name for rule in rules}
        assert "disabled-rule" not in rule_names
        assert "baseline-all" in rule_names


class TestRuleEngineIntegration:
    """Integration tests for RuleEngine with StatisticsCalculator."""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing."""
        database = ExecutionDatabase(":memory:")
        yield database
        database.close()

    @pytest.fixture
    def engine(self, db):
        """Create RuleEngine instance."""
        return RuleEngine(db)

    @pytest.fixture
    def calculator(self, db):
        """Create StatisticsCalculator instance."""
        return StatisticsCalculator(db)

    def test_selective_execution_workflow(self, db, engine, calculator):
        """Test complete selective execution workflow."""
        # 1. Insert execution history
        now = datetime.now()
        for i in range(20):
            db.insert_execution_history(
                ExecutionHistory(
                    execution_id=f"local-{i}",
                    entity_id="tests/test_example.py::test_func",
                    entity_type="test",
                    timestamp=now - timedelta(hours=i),
                    status="FAILED" if i < 2 else "PASSED",  # 10% failure rate
                    duration=1.0,
                )
            )

        # 2. Calculate statistics
        stats = calculator.calculate_entity_stats("tests/test_example.py::test_func")
        assert stats.failure_rate == 0.1

        # 3. Create and execute rule
        rule = ExecutionRule(
            name="test-flaky-check",
            criteria="failure-rate",
            threshold=0.05,
            window=20,
        )
        db.insert_execution_rule(rule)

        # 4. Select entities using rule
        entities = engine.select_entities(rule)
        assert "tests/test_example.py::test_func" in entities
