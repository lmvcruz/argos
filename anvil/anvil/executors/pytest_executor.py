"""
Enhanced pytest executor with execution history tracking.

This module extends the pytest validator to automatically record test execution
results in the ExecutionDatabase for selective execution and historical analysis.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from anvil.core.statistics_calculator import StatisticsCalculator
from anvil.models.validator import ValidationResult
from anvil.parsers.pytest_parser import PytestParser
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory
from anvil.validators.pytest_validator import PytestValidator


class PytestExecutorWithHistory(PytestValidator):
    """
    Enhanced pytest executor that records execution history.

    Extends PytestValidator to automatically track test execution results
    in the ExecutionDatabase, enabling selective execution based on
    historical data and failure patterns.

    Examples:
        >>> db = ExecutionDatabase(".anvil/history.db")
        >>> executor = PytestExecutorWithHistory(db=db)
        >>> result = executor.validate(["tests/test_example.py"], {})
        >>> # Execution history automatically recorded
    """

    def __init__(self, db: Optional[ExecutionDatabase] = None, config_path: Optional[str] = None):
        """
        Initialize enhanced pytest executor.

        Args:
            db: ExecutionDatabase instance (creates default if None)
            config_path: Path to Anvil configuration file for database path
        """
        super().__init__()
        self.db = db
        self.config_path = config_path
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database is initialized."""
        if self.db is None:
            # Try to get database path from config
            db_path = ".anvil/history.db"
            if self.config_path:
                try:
                    import yaml

                    with open(self.config_path) as f:
                        config = yaml.safe_load(f)
                    db_path = config.get("history", {}).get("database", db_path)
                except Exception:
                    # Fall back to default
                    pass

            self.db = ExecutionDatabase(db_path, auto_recover=True)

    def validate(
        self, files: List[str], config: Dict[str, Any], execution_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Run pytest validation and record execution history.

        Args:
            files: List of Python test file paths to validate
            config: Configuration dictionary for pytest
            execution_id: Optional execution ID (auto-generated if None)

        Returns:
            ValidationResult containing validation outcome and issues
        """
        # Generate execution ID if not provided
        if execution_id is None:
            timestamp = int(datetime.now().timestamp())
            space = config.get("space", "local")
            execution_id = f"{space}-{timestamp}"

        # Run pytest and get results
        result = super().validate(files, config)

        # Extract and record individual test results
        if files and result.passed is not None:
            self._record_execution_history(files, config, execution_id)

        return result

    def _record_execution_history(
        self, files: List[str], config: Dict[str, Any], execution_id: str
    ):
        """
        Record execution history for all tests.

        Args:
            files: Test files that were executed
            config: pytest configuration
            execution_id: Unique execution identifier
        """
        # Ensure JSON report is enabled in config
        history_config = config.copy()
        if "json_report" not in history_config:
            history_config["json_report"] = True

        # Run pytest with JSON output to get detailed results
        file_paths = [Path(f) for f in files]

        try:
            result = PytestParser.run_pytest(file_paths, history_config)
        except Exception as e:
            print(f"Warning: Failed to run pytest for history recording: {e}")
            return

        if not result.stdout:
            return

        try:
            data = json.loads(result.stdout)
            space = config.get("space", "local")
            timestamp = datetime.now()

            # Extract test results
            if "report" in data:
                tests = data["report"].get("tests", [])

                for test in tests:
                    nodeid = test.get("nodeid", "")
                    if not nodeid:
                        continue

                    outcome = test.get("outcome", "unknown").upper()
                    duration = test.get("duration", None)

                    # Map pytest outcomes to our status
                    status_map = {
                        "PASSED": "PASSED",
                        "FAILED": "FAILED",
                        "SKIPPED": "SKIPPED",
                        "ERROR": "ERROR",
                        "XFAIL": "SKIPPED",  # Expected failure
                        "XPASS": "PASSED",  # Unexpected pass
                    }
                    status = status_map.get(outcome, "ERROR")

                    # Extract metadata
                    metadata = {
                        "outcome": outcome,
                        "call_duration": test.get("call", {}).get("duration"),
                        "setup_duration": test.get("setup", {}).get("duration"),
                        "teardown_duration": test.get("teardown", {}).get("duration"),
                    }

                    if outcome == "FAILED":
                        metadata["longrepr"] = test.get("longrepr", "")[:500]  # Truncate

                    # Record execution history
                    history = ExecutionHistory(
                        execution_id=execution_id,
                        entity_id=nodeid,
                        entity_type="test",
                        timestamp=timestamp,
                        status=status,
                        duration=duration,
                        space=space,
                        metadata=metadata,
                    )

                    self.db.insert_execution_history(history)

            # Update entity statistics
            self._update_statistics(config.get("statistics_window"))

        except (json.JSONDecodeError, KeyError) as e:
            # Log error but don't fail the validation
            print(f"Warning: Failed to record execution history: {e}")

    def _update_statistics(self, window: Optional[int] = None):
        """
        Update entity statistics after execution.

        Args:
            window: Number of recent executions to consider for statistics
        """
        calculator = StatisticsCalculator(self.db)

        # Calculate statistics for all tests
        all_stats = calculator.calculate_all_stats(entity_type="test", window=window)

        # Update statistics table
        for stats in all_stats:
            self.db.update_entity_statistics(stats)

    def execute_with_rule(
        self, rule_name: str, config: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Execute tests selected by a rule.

        Args:
            rule_name: Name of the execution rule to use
            config: Optional pytest configuration (uses rule config if None)

        Returns:
            ValidationResult for selected tests
        """
        from anvil.core.rule_engine import RuleEngine

        engine = RuleEngine(self.db)

        # Get rule
        rule = engine.get_rule(rule_name)
        if not rule:
            raise ValueError(f"Rule not found: {rule_name}")

        if not rule.enabled:
            raise ValueError(f"Rule is disabled: {rule_name}")

        # Select entities using rule
        entity_ids = engine.select_entities(rule)

        if not entity_ids:
            # No tests to run
            return ValidationResult(
                validator_name=self.name,
                passed=True,
                errors=[],
                warnings=[],
                files_checked=0,
            )

        # Merge rule config with provided config
        merged_config = {}
        if rule.executor_config:
            merged_config.update(rule.executor_config)
        if config:
            merged_config.update(config)

        # Execute selected tests
        execution_id = f"rule-{rule_name}-{int(datetime.now().timestamp())}"
        return self.validate(entity_ids, merged_config, execution_id=execution_id)

    def get_flaky_tests(
        self, threshold: float = 0.10, window: Optional[int] = 20
    ) -> List[str]:
        """
        Get list of flaky tests based on failure rate.

        Args:
            threshold: Failure rate threshold (0.0-1.0)
            window: Number of recent executions to consider

        Returns:
            List of test nodeids with high failure rates
        """
        calculator = StatisticsCalculator(self.db)
        flaky_stats = calculator.get_flaky_entities(threshold=threshold, window=window)
        return [stats.entity_id for stats in flaky_stats]

    def get_failed_tests(self, n: int = 1) -> List[str]:
        """
        Get tests that failed in their last N executions.

        Args:
            n: Number of recent executions to check

        Returns:
            List of test nodeids that failed recently
        """
        calculator = StatisticsCalculator(self.db)
        return calculator.get_failed_in_last_n(n=n)

    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()
