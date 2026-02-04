"""
Test orchestration and execution management.

This module coordinates test execution, manages parallelism, and aggregates results.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from verdict.executor import TargetExecutor
from verdict.loader import ConfigLoader, TestCaseLoader
from verdict.validator import OutputValidator


class TestResult:
    """Represents the result of a single test case execution."""

    def __init__(
        self,
        test_name: str,
        suite_name: str,
        passed: bool,
        differences: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize test result.

        Args:
            test_name: Name of the test case
            suite_name: Name of the test suite
            passed: Whether the test passed
            differences: List of differences (if validation failed)
            error: Error message (if execution failed)
        """
        self.test_name = test_name
        self.suite_name = suite_name
        self.passed = passed
        self.differences = differences or []
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "test_name": self.test_name,
            "suite_name": self.suite_name,
            "passed": self.passed,
            "differences": self.differences,
            "error": self.error,
        }


class TestRunner:
    """
    Orchestrates test execution across test suites.

    Loads configuration, executes tests with parallelism, and aggregates results.
    """

    def __init__(self, config_path: Path):
        """
        Initialize test runner.

        Args:
            config_path: Path to configuration YAML file
        """
        self.config_path = Path(config_path)
        self.config_loader = ConfigLoader(self.config_path)
        self.test_case_loader = TestCaseLoader(base_path=self.config_path.parent)
        self.executor = TargetExecutor()
        self.validator = OutputValidator()

        # Load configuration
        self.config = self.config_loader.load()

    def run_all(self, max_workers: Optional[int] = None) -> List[TestResult]:
        """
        Run all test suites.

        Args:
            max_workers: Maximum number of parallel workers (None = from config or auto)

        Returns:
            List of test results
        """
        # Determine max_workers
        if max_workers is None:
            settings = self.config.get("settings", {})
            max_workers = settings.get("max_workers")

        if max_workers is None:
            max_workers = os.cpu_count()

        # Run all test suites
        results = []
        test_suites = self.config["test_suites"]

        for suite_config in test_suites:
            suite_results = self.run_suite(suite_config, max_workers)
            results.extend(suite_results)

        return results

    def run_suite(
        self,
        suite_config: Dict[str, Any],
        max_workers: int,
    ) -> List[TestResult]:
        """
        Run a single test suite.

        Args:
            suite_config: Test suite configuration
            max_workers: Maximum number of parallel workers

        Returns:
            List of test results for this suite
        """
        suite_name = suite_config["name"]
        target_id = suite_config["target"]
        suite_type = suite_config["type"]

        # Get target callable path
        targets = self.config["targets"]
        if target_id not in targets:
            raise ValueError(f"Target '{target_id}' not found in configuration")

        target_config = targets[target_id]
        callable_path = target_config["callable"]

        # Load test cases
        if suite_type == "single_file":
            # Handle both 'file' and 'cases' fields
            if "file" in suite_config:
                file_path = Path(suite_config["file"])
                test_cases = self.test_case_loader.load_single_file(file_path)
            elif "cases" in suite_config:
                # Load multiple case files
                test_cases = []
                for case_file in suite_config["cases"]:
                    case_path = Path(case_file)
                    cases = self.test_case_loader.load_single_file(case_path)
                    test_cases.extend(cases)
            else:
                raise ValueError(f"Test suite '{suite_name}' must have 'file' or 'cases' field")
        elif suite_type == "cases_in_folder":
            folder_path = Path(suite_config["folder"])
            test_cases = self.test_case_loader.load_cases_from_folder(folder_path)
        else:
            raise ValueError(f"Unknown test suite type: {suite_type}")

        # Execute test cases
        if max_workers == 1:
            # Sequential execution
            results = [
                self._execute_test_case(test_case, suite_name, callable_path)
                for test_case in test_cases
            ]
        else:
            # Parallel execution
            results = self._execute_parallel(test_cases, suite_name, callable_path, max_workers)

        return results

    def _execute_parallel(
        self,
        test_cases: List[Dict[str, Any]],
        suite_name: str,
        callable_path: str,
        max_workers: int,
    ) -> List[TestResult]:
        """
        Execute test cases in parallel.

        Args:
            test_cases: List of test case dictionaries
            suite_name: Name of the test suite
            callable_path: Dotted path to target callable
            max_workers: Maximum number of parallel workers

        Returns:
            List of test results
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_test = {
                executor.submit(
                    self._execute_test_case, test_case, suite_name, callable_path
                ): test_case
                for test_case in test_cases
            }

            # Collect results as they complete
            for future in as_completed(future_to_test):
                result = future.result()
                results.append(result)

        return results

    def _execute_test_case(
        self,
        test_case: Dict[str, Any],
        suite_name: str,
        callable_path: str,
    ) -> TestResult:
        """
        Execute a single test case.

        Args:
            test_case: Test case dictionary with input and expected fields
            suite_name: Name of the test suite
            callable_path: Dotted path to target callable

        Returns:
            Test result
        """
        test_name = test_case["name"]
        test_input = test_case["input"]
        expected_output = test_case["expected"]

        # Extract input text from input specification
        # If input is a dict with 'type' and 'content', extract the content
        if isinstance(test_input, dict) and "type" in test_input and "content" in test_input:
            input_text = test_input["content"]
        else:
            # Use input as-is (should be a string)
            input_text = test_input

        try:
            # Execute target callable
            actual_output = self.executor.execute(callable_path, input_text)

            # Validate output
            is_valid, differences = self.validator.validate(actual_output, expected_output)

            return TestResult(
                test_name=test_name,
                suite_name=suite_name,
                passed=is_valid,
                differences=differences if not is_valid else None,
            )

        except Exception as e:
            # Test execution failed
            return TestResult(
                test_name=test_name,
                suite_name=suite_name,
                passed=False,
                error=str(e),
            )
