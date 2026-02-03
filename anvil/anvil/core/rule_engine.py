"""
Rule engine for selective execution.

This module implements the rule evaluation engine that determines which
entities (tests, coverage, lint) should be executed based on defined rules
and historical execution data.
"""

import fnmatch
from typing import List, Optional

from anvil.core.statistics_calculator import StatisticsCalculator
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionRule


class RuleEngine:
    """
    Engine for evaluating and executing selective execution rules.

    Evaluates rules based on criteria (all, group, failed-in-last, failure-rate)
    and selects entities for execution using historical data and statistics.

    Examples:
        >>> db = ExecutionDatabase(".anvil/history.db")
        >>> engine = RuleEngine(db)
        >>> rule = engine.get_rule("quick-check")
        >>> entities = engine.select_entities(rule)
        >>> print(f"Selected {len(entities)} entities to execute")
        Selected 15 entities to execute
    """

    def __init__(self, db: ExecutionDatabase):
        """
        Initialize rule engine.

        Args:
            db: ExecutionDatabase instance for accessing rules and history
        """
        self.db = db
        self.statistics = StatisticsCalculator(db)

    def select_entities(self, rule: ExecutionRule) -> List[str]:
        """
        Select entities to execute based on rule criteria.

        Args:
            rule: ExecutionRule defining selection criteria

        Returns:
            List of entity IDs to execute
        """
        if rule.criteria == "all":
            return self._select_all_entities(rule)
        elif rule.criteria == "group":
            return self._select_by_group(rule)
        elif rule.criteria == "failed-in-last":
            return self._select_failed_in_last(rule)
        elif rule.criteria == "failure-rate":
            return self._select_by_failure_rate(rule)
        elif rule.criteria == "changed-files":
            # TODO: Implement changed-files criteria (requires git integration)
            return []
        else:
            raise ValueError(f"Unknown criteria: {rule.criteria}")

    def _select_all_entities(self, rule: ExecutionRule) -> List[str]:
        """
        Select all entities (optionally filtered by groups).

        Args:
            rule: ExecutionRule (may have groups filter)

        Returns:
            List of all entity IDs
        """
        # Get all unique entity IDs from execution history
        all_history = self.db.get_execution_history()
        entity_ids = {h.entity_id for h in all_history}

        # If groups are specified, filter by them
        if rule.groups:
            filtered = []
            for entity_id in entity_ids:
                if self._matches_any_pattern(entity_id, rule.groups):
                    filtered.append(entity_id)
            return filtered

        return list(entity_ids)

    def _select_by_group(self, rule: ExecutionRule) -> List[str]:
        """
        Select entities matching group patterns.

        Args:
            rule: ExecutionRule with groups patterns

        Returns:
            List of entity IDs matching group patterns
        """
        if not rule.groups:
            return []

        # Get all unique entity IDs
        all_history = self.db.get_execution_history()
        entity_ids = {h.entity_id for h in all_history}

        # Filter by group patterns
        selected = []
        for entity_id in entity_ids:
            if self._matches_any_pattern(entity_id, rule.groups):
                selected.append(entity_id)

        return selected

    def _select_failed_in_last(self, rule: ExecutionRule) -> List[str]:
        """
        Select entities that failed in last N executions.

        Args:
            rule: ExecutionRule with window parameter

        Returns:
            List of entity IDs that failed recently
        """
        window = rule.window if rule.window else 1
        return self.statistics.get_failed_in_last_n(n=window)

    def _select_by_failure_rate(self, rule: ExecutionRule) -> List[str]:
        """
        Select entities with failure rate above threshold.

        Args:
            rule: ExecutionRule with threshold and window parameters

        Returns:
            List of entity IDs exceeding failure rate threshold
        """
        threshold = rule.threshold if rule.threshold else 0.10
        window = rule.window

        flaky_stats = self.statistics.get_flaky_entities(
            threshold=threshold, window=window
        )

        return [stats.entity_id for stats in flaky_stats]

    def _matches_any_pattern(self, entity_id: str, patterns: List[str]) -> bool:
        """
        Check if entity ID matches any of the given patterns.

        Args:
            entity_id: Entity identifier to check
            patterns: List of glob patterns

        Returns:
            True if entity matches any pattern
        """
        for pattern in patterns:
            # Support both file patterns and full nodeids
            if fnmatch.fnmatch(entity_id, pattern) or fnmatch.fnmatch(
                entity_id, f"{pattern}*"
            ):
                return True
        return False

    def get_rule(self, name: str) -> Optional[ExecutionRule]:
        """
        Retrieve an execution rule by name.

        Args:
            name: Rule name

        Returns:
            ExecutionRule if found, None otherwise
        """
        return self.db.get_execution_rule(name)

    def list_rules(self, enabled_only: bool = False) -> List[ExecutionRule]:
        """
        List all execution rules.

        Args:
            enabled_only: If True, only return enabled rules

        Returns:
            List of ExecutionRule instances
        """
        # Query all rules from database
        cursor = self.db.connection.cursor()
        cursor.execute("SELECT * FROM execution_rules ORDER BY name")

        import json

        rules = []
        for row in cursor.fetchall():
            from datetime import datetime

            groups = json.loads(row[6]) if row[6] else None
            config = json.loads(row[7]) if row[7] else None
            enabled = bool(row[3])

            if enabled_only and not enabled:
                continue

            rule = ExecutionRule(
                id=row[0],
                name=row[1],
                criteria=row[2],
                enabled=enabled,
                threshold=row[4],
                window=row[5],
                groups=groups,
                executor_config=config,
                created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                updated_at=datetime.fromisoformat(row[9]) if row[9] else None,
            )
            rules.append(rule)

        return rules
