"""
Statistics calculator for execution history analysis.

This module provides statistical analysis of test execution history,
including failure rates, average durations, and identification of
flaky tests.
"""

from datetime import datetime
from typing import List, Optional

from anvil.storage.execution_schema import EntityStatistics, ExecutionDatabase


class StatisticsCalculator:
    """
    Calculate execution statistics for entities.

    Analyzes execution history to compute metrics like failure rates,
    average durations, and identify flaky tests based on historical data.

    Examples:
        >>> db = ExecutionDatabase(".anvil/history.db")
        >>> calc = StatisticsCalculator(db)
        >>> stats = calc.calculate_entity_stats("tests/test_example.py::test_func")
        >>> print(f"Failure rate: {stats.failure_rate:.1%}")
        Failure rate: 15.0%
    """

    def __init__(self, db: ExecutionDatabase):
        """
        Initialize statistics calculator.

        Args:
            db: ExecutionDatabase instance for accessing execution history
        """
        self.db = db

    def calculate_entity_stats(
        self, entity_id: str, window: Optional[int] = None
    ) -> Optional[EntityStatistics]:
        """
        Calculate statistics for a single entity.

        Args:
            entity_id: Entity identifier (e.g., test nodeid)
            window: Number of recent executions to consider (None = all)

        Returns:
            EntityStatistics if entity has execution history, None otherwise
        """
        # Retrieve execution history for this entity
        history = self.db.get_execution_history(entity_id=entity_id, limit=window)

        if not history:
            return None

        # Calculate statistics
        total_runs = len(history)
        passed = sum(1 for h in history if h.status == "PASSED")
        failed = sum(1 for h in history if h.status == "FAILED")
        skipped = sum(1 for h in history if h.status == "SKIPPED")

        failure_rate = failed / total_runs if total_runs > 0 else 0.0

        # Calculate average duration (excluding None values)
        durations = [h.duration for h in history if h.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else None

        # Get most recent run timestamp
        last_run = history[0].timestamp if history else None

        # Get most recent failure timestamp
        failed_runs = [h for h in history if h.status == "FAILED"]
        last_failure = failed_runs[0].timestamp if failed_runs else None

        # Infer entity type from first record
        entity_type = history[0].entity_type if history else "test"

        return EntityStatistics(
            entity_id=entity_id,
            entity_type=entity_type,
            total_runs=total_runs,
            passed=passed,
            failed=failed,
            skipped=skipped,
            failure_rate=failure_rate,
            avg_duration=avg_duration,
            last_run=last_run,
            last_failure=last_failure,
            last_updated=datetime.now(),
        )

    def calculate_all_stats(
        self, entity_type: str = "test", window: Optional[int] = None
    ) -> List[EntityStatistics]:
        """
        Calculate statistics for all entities of a given type.

        Args:
            entity_type: Type of entities to analyze (test, coverage, lint)
            window: Number of recent executions per entity to consider

        Returns:
            List of EntityStatistics for all entities
        """
        # Get all execution history for this entity type
        all_history = self.db.get_execution_history(entity_type=entity_type)

        # Group by entity_id
        entity_ids = {h.entity_id for h in all_history}

        # Calculate stats for each entity
        stats_list = []
        for entity_id in entity_ids:
            stats = self.calculate_entity_stats(entity_id, window=window)
            if stats:
                stats_list.append(stats)

        return stats_list

    def get_flaky_entities(
        self, threshold: float = 0.10, window: Optional[int] = None
    ) -> List[EntityStatistics]:
        """
        Identify flaky entities based on failure rate threshold.

        Args:
            threshold: Failure rate threshold (0.0-1.0, e.g., 0.10 = 10%)
            window: Number of recent executions to consider

        Returns:
            List of EntityStatistics for entities exceeding threshold
        """
        all_stats = self.calculate_all_stats(window=window)

        # Filter by failure rate threshold
        flaky = [stats for stats in all_stats if stats.failure_rate >= threshold]

        # Sort by failure rate descending
        flaky.sort(key=lambda s: s.failure_rate, reverse=True)

        return flaky

    def get_failed_in_last_n(self, n: int = 1) -> List[str]:
        """
        Get entities that failed in their last N executions.

        Args:
            n: Number of recent executions to check

        Returns:
            List of entity IDs that failed in last N runs
        """
        all_history = self.db.get_execution_history()

        # Group by entity_id
        entity_ids = {h.entity_id for h in all_history}

        failed_entities = []
        for entity_id in entity_ids:
            # Get last N executions for this entity
            recent = self.db.get_execution_history(entity_id=entity_id, limit=n)

            # Check if any failed
            if any(h.status == "FAILED" for h in recent):
                failed_entities.append(entity_id)

        return failed_entities
