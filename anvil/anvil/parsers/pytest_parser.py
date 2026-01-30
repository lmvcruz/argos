"""
Parser for pytest JSON output with coverage data.

This module provides the PytestParser class that parses pytest JSON reports
to extract test results, failures, durations, and code coverage metrics.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from anvil.models.validator import Issue, ValidationResult


class PytestParser:
    """
    Parse pytest JSON output for test execution and coverage.

    Supports pytest with pytest-json-report and pytest-cov plugins to extract
    comprehensive test results including pass/fail status, durations, coverage
    percentages, and missing line numbers.
    """

    @staticmethod
    def parse_json(json_output: str, files: List[Path], config: Dict) -> ValidationResult:
        """
        Parse pytest JSON output and convert to ValidationResult.

        Args:
            json_output: JSON string from pytest --json-report
            files: List of test files that were executed
            config: Configuration dictionary with pytest options

        Returns:
            ValidationResult with test failures as errors and skips as warnings

        Raises:
            json.JSONDecodeError: If JSON output is malformed
        """
        data = json.loads(json_output)

        errors = []
        warnings = []

        # Extract test results
        if "report" in data:
            report = data["report"]
            tests = report.get("tests", [])

            for test in tests:
                nodeid = test.get("nodeid", "unknown")
                outcome = test.get("outcome", "unknown")
                test.get("duration", 0.0)

                if outcome == "failed":
                    longrepr = test.get("longrepr", "Test failed")
                    message = f"Test failed: {nodeid}"
                    if longrepr:
                        message += f" - {longrepr}"
                    errors.append(
                        Issue(
                            file_path=PytestParser._extract_file_from_nodeid(nodeid),
                            line_number=0,
                            column_number=None,
                            severity="error",
                            message=message,
                            rule_name="pytest-failure",
                        )
                    )
                elif outcome == "skipped":
                    longrepr = test.get("longrepr", "Test skipped")
                    message = f"Test skipped: {nodeid}"
                    if longrepr:
                        message += f" - {longrepr}"
                    warnings.append(
                        Issue(
                            file_path=PytestParser._extract_file_from_nodeid(nodeid),
                            line_number=0,
                            column_number=None,
                            severity="warning",
                            message=message,
                            rule_name="pytest-skip",
                        )
                    )

        # Check coverage threshold if specified
        if "coverage" in data and config.get("coverage_threshold"):
            threshold = config["coverage_threshold"]
            coverage_pct = data["coverage"]["totals"].get("percent_covered", 0)

            if coverage_pct < threshold:
                errors.append(
                    Issue(
                        file_path="overall",
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message=f"Coverage {coverage_pct:.1f}% below threshold {threshold}%",
                        rule_name="coverage-threshold",
                    )
                )

        passed = len(errors) == 0

        return ValidationResult(
            validator_name="pytest",
            passed=passed,
            errors=errors,
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def _extract_file_from_nodeid(nodeid: str) -> str:
        """
        Extract file path from pytest nodeid.

        Args:
            nodeid: Pytest node ID like "tests/test_example.py::test_func"

        Returns:
            File path portion of the nodeid
        """
        if "::" in nodeid:
            return nodeid.split("::")[0]
        return nodeid

    @staticmethod
    def extract_test_durations(json_output: str) -> Dict[str, float]:
        """
        Extract duration for each individual test.

        Args:
            json_output: JSON string from pytest

        Returns:
            Dictionary mapping test nodeid to duration in seconds
        """
        data = json.loads(json_output)
        durations = {}

        if "report" in data:
            tests = data["report"].get("tests", [])
            for test in tests:
                nodeid = test.get("nodeid", "")
                duration = test.get("duration", 0.0)
                durations[nodeid] = duration

        return durations

    @staticmethod
    def get_slowest_tests(json_output: str, n: int = 10) -> List[Tuple[str, float]]:
        """
        Get the n slowest tests by duration.

        Args:
            json_output: JSON string from pytest
            n: Number of slowest tests to return

        Returns:
            List of (nodeid, duration) tuples sorted by duration descending
        """
        durations = PytestParser.extract_test_durations(json_output)
        sorted_tests = sorted(durations.items(), key=lambda x: x[1], reverse=True)
        return sorted_tests[:n]

    @staticmethod
    def extract_coverage_percentage(json_output: str) -> Optional[float]:
        """
        Extract overall coverage percentage.

        Args:
            json_output: JSON string from pytest with coverage data

        Returns:
            Coverage percentage (0-100) or None if not available
        """
        try:
            data = json.loads(json_output)
            if "coverage" in data and "totals" in data["coverage"]:
                return data["coverage"]["totals"].get("percent_covered")
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    @staticmethod
    def extract_coverage_by_module(json_output: str) -> Dict[str, float]:
        """
        Extract coverage percentage per module.

        Args:
            json_output: JSON string from pytest with coverage data

        Returns:
            Dictionary mapping file path to coverage percentage
        """
        coverage_by_module = {}

        try:
            data = json.loads(json_output)
            if "coverage" in data and "files" in data["coverage"]:
                for filepath, file_data in data["coverage"]["files"].items():
                    coverage_pct = file_data.get("percent_covered", 0.0)
                    coverage_by_module[filepath] = coverage_pct
        except (json.JSONDecodeError, KeyError):
            pass

        return coverage_by_module

    @staticmethod
    def extract_missing_lines(json_output: str, filepath: str) -> List[int]:
        """
        Extract missing line numbers for a specific file.

        Args:
            json_output: JSON string from pytest with coverage data
            filepath: Path to the file to check

        Returns:
            List of line numbers with missing coverage
        """
        try:
            data = json.loads(json_output)
            if "coverage" in data and "files" in data["coverage"]:
                file_data = data["coverage"]["files"].get(filepath, {})
                return file_data.get("missing_lines", [])
        except (json.JSONDecodeError, KeyError):
            pass
        return []

    @staticmethod
    def get_modules_below_threshold(json_output: str, threshold: float) -> Dict[str, float]:
        """
        Identify modules with coverage below threshold.

        Args:
            json_output: JSON string from pytest with coverage data
            threshold: Minimum coverage percentage required

        Returns:
            Dictionary mapping file path to coverage percentage for files below threshold
        """
        coverage_by_module = PytestParser.extract_coverage_by_module(json_output)
        return {filepath: pct for filepath, pct in coverage_by_module.items() if pct < threshold}

    @staticmethod
    def extract_branch_coverage(json_output: str) -> Optional[float]:
        """
        Extract branch coverage percentage if available.

        Args:
            json_output: JSON string from pytest with coverage data

        Returns:
            Branch coverage percentage or None if not available
        """
        try:
            data = json.loads(json_output)
            if "coverage" in data and "totals" in data["coverage"]:
                return data["coverage"]["totals"].get("percent_covered_branches")
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    @staticmethod
    def build_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build pytest command with appropriate flags.

        Args:
            files: List of test files or directories to run
            config: Configuration with pytest options

        Returns:
            Command list suitable for subprocess.run
        """
        cmd = ["pytest"]

        # JSON report output
        cmd.append("--json-report")
        cmd.append("--json-report-file=-")  # Output to stdout

        # Coverage options
        if config.get("coverage"):
            cmd.append("--cov")
            if config.get("coverage_source"):
                cmd.append(f"--cov={config['coverage_source']}")
            cmd.append("--cov-report=json")

        # Test selection
        if config.get("markers"):
            markers = config["markers"]
            if isinstance(markers, list):
                markers = " and ".join(markers)
            cmd.extend(["-m", markers])

        if config.get("keywords"):
            cmd.extend(["-k", config["keywords"]])

        # Parallel execution
        if config.get("parallel"):
            workers = config.get("workers", "auto")
            cmd.extend(["-n", str(workers)])

        # Reruns on failure
        if config.get("reruns"):
            cmd.extend(["--reruns", str(config["reruns"])])
            if config.get("reruns_delay"):
                cmd.extend(["--reruns-delay", str(config["reruns_delay"])])

        # Verbosity
        if config.get("verbose"):
            cmd.append("-vv")

        # Add file paths
        for file in files:
            cmd.append(str(file))

        return cmd

    @staticmethod
    def run_pytest(files: List[Path], config: Dict, timeout: Optional[int] = None):
        """
        Execute pytest subprocess.

        Args:
            files: List of test files or directories
            config: Configuration dictionary
            timeout: Optional timeout in seconds

        Returns:
            CompletedProcess with stdout containing JSON report

        Raises:
            FileNotFoundError: If pytest is not installed
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        cmd = PytestParser.build_command(files, config)
        timeout = timeout or config.get("timeout", 300)  # Default 5 minutes

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Don't raise on non-zero exit
        )

        return result

    @staticmethod
    def run_and_parse(files: List[Path], config: Dict) -> ValidationResult:
        """
        Execute pytest and parse results.

        Args:
            files: List of test files or directories
            config: Configuration dictionary

        Returns:
            ValidationResult with test results and coverage data
        """
        result = PytestParser.run_pytest(files, config)

        if result.returncode != 0 and not result.stdout:
            # pytest failed before generating JSON
            return ValidationResult(
                validator_name="pytest",
                passed=False,
                errors=[
                    Issue(
                        file_path="pytest",
                        line_number=0,
                        column_number=None,
                        severity="error",
                        message="pytest execution failed",
                        rule_name="pytest-error",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

        return PytestParser.parse_json(result.stdout, files, config)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Detect installed pytest version.

        Returns:
            Version string or None if pytest not found
        """
        try:
            result = subprocess.run(
                ["pytest", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            # Parse version from output like "pytest 7.4.3"
            match = re.search(r"pytest\s+(\d+\.\d+\.\d+)", result.stdout)
            if match:
                return match.group(1)
        except FileNotFoundError:
            pass

        return None

    @staticmethod
    def detect_flaky_tests(json_output: str) -> List[str]:
        """
        Detect tests that passed after retry (flaky tests).

        Args:
            json_output: JSON string from pytest with rerun data

        Returns:
            List of test nodeids that were flaky
        """
        flaky_tests = []

        try:
            data = json.loads(json_output)
            if "report" in data:
                tests = data["report"].get("tests", [])

                # Track tests with rerun outcomes
                rerun_tests = {}
                for test in tests:
                    nodeid = test.get("nodeid", "")
                    outcome = test.get("outcome", "")

                    if outcome == "rerun":
                        rerun_tests[nodeid] = True
                    elif outcome == "passed" and nodeid in rerun_tests:
                        flaky_tests.append(nodeid)
        except (json.JSONDecodeError, KeyError):
            pass

        return flaky_tests

    @staticmethod
    def extract_summary(json_output: str) -> Dict:
        """
        Extract overall test summary statistics.

        Args:
            json_output: JSON string from pytest

        Returns:
            Dictionary with passed, failed, skipped, total, duration
        """
        summary = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "duration": 0.0,
        }

        try:
            data = json.loads(json_output)
            if "report" in data and "summary" in data["report"]:
                summary.update(data["report"]["summary"])
        except (json.JSONDecodeError, KeyError):
            pass

        return summary

    @staticmethod
    def calculate_pass_rate(json_output: str) -> float:
        """
        Calculate test pass rate percentage.

        Args:
            json_output: JSON string from pytest

        Returns:
            Pass rate as percentage (0-100)
        """
        summary = PytestParser.extract_summary(json_output)
        total = summary.get("total", 0)

        if total == 0:
            return 0.0

        passed = summary.get("passed", 0)
        return (passed / total) * 100.0

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find pytest configuration file in directory.

        Searches for pytest.ini, pyproject.toml, or setup.cfg with pytest config.

        Args:
            directory: Directory to search in

        Returns:
            Path to config file or None if not found
        """
        # Check pytest.ini
        pytest_ini = directory / "pytest.ini"
        if pytest_ini.exists():
            return pytest_ini

        # Check pyproject.toml with [tool.pytest.ini_options]
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.pytest.ini_options]" in content:
                return pyproject

        # Check setup.cfg with [tool:pytest]
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[tool:pytest]" in content:
                return setup_cfg

        return None
