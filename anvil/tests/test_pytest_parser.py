"""
Tests for pytest parser - test execution and coverage measurement.

This module tests the PytestParser class which parses pytest JSON output with
coverage data to track test results, failures, durations, and code coverage.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.pytest_parser import PytestParser


class TestPytestResultParsing:
    """Test parsing pytest JSON output for test results."""

    def test_parse_output_all_tests_passed(self, mocker: MockerFixture):
        """Test parsing when all tests pass."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "tests/test_example.py::test_pass", "outcome": "passed", "duration": 0.01}
                ],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            }
        }
        """

        result = PytestParser.parse_json(json_output, [Path("tests/test_example.py")], {})

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_output_with_test_failures(self, mocker: MockerFixture):
        """Test parsing when tests fail."""
        json_output = """
        {
            "report": {
                "tests": [
                    {
                        "nodeid": "tests/test_example.py::test_fail",
                        "outcome": "failed",
                        "duration": 0.02,
                        "longrepr": "AssertionError: expected 2, got 3"
                    }
                ],
                "summary": {"passed": 0, "failed": 1, "skipped": 0, "total": 1}
            }
        }
        """

        result = PytestParser.parse_json(json_output, [Path("tests/test_example.py")], {})

        assert result.passed is False
        assert len(result.errors) == 1
        assert "test_fail" in result.errors[0].message

    def test_parse_output_with_skipped_tests(self, mocker: MockerFixture):
        """Test parsing when tests are skipped."""
        json_output = """
        {
            "report": {
                "tests": [
                    {
                        "nodeid": "tests/test_example.py::test_skip",
                        "outcome": "skipped",
                        "duration": 0.0,
                        "longrepr": "Skipped: requires special setup"
                    }
                ],
                "summary": {"passed": 0, "failed": 0, "skipped": 1, "total": 1}
            }
        }
        """

        result = PytestParser.parse_json(json_output, [Path("tests/test_example.py")], {})

        assert result.passed is True
        assert len(result.warnings) == 1
        assert "skipped" in result.warnings[0].message.lower()

    def test_parse_parametrized_tests(self, mocker: MockerFixture):
        """Test parsing parametrized tests with multiple instances."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "tests/test_example.py::test_add[1-2-3]", "outcome": "passed", "duration": 0.01},
                    {"nodeid": "tests/test_example.py::test_add[2-3-5]", "outcome": "passed", "duration": 0.01},
                    {"nodeid": "tests/test_example.py::test_add[3-4-8]", "outcome": "failed", "duration": 0.01}
                ],
                "summary": {"passed": 2, "failed": 1, "skipped": 0, "total": 3}
            }
        }
        """

        result = PytestParser.parse_json(json_output, [Path("tests/test_example.py")], {})

        assert result.passed is False
        assert len(result.errors) == 1

    def test_parse_test_durations(self, mocker: MockerFixture):
        """Test extracting individual test durations."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "tests/test_slow.py::test_slow", "outcome": "passed", "duration": 5.2},
                    {"nodeid": "tests/test_fast.py::test_fast", "outcome": "passed", "duration": 0.01}
                ],
                "summary": {"passed": 2, "failed": 0, "skipped": 0, "total": 2}
            }
        }
        """

        durations = PytestParser.extract_test_durations(json_output)

        assert durations["tests/test_slow.py::test_slow"] == 5.2
        assert durations["tests/test_fast.py::test_fast"] == 0.01

    def test_identify_slowest_tests(self, mocker: MockerFixture):
        """Test identifying slowest tests."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "test_a.py::test_1", "outcome": "passed", "duration": 1.0},
                    {"nodeid": "test_b.py::test_2", "outcome": "passed", "duration": 5.0},
                    {"nodeid": "test_c.py::test_3", "outcome": "passed", "duration": 3.0}
                ],
                "summary": {"passed": 3, "failed": 0, "skipped": 0, "total": 3}
            }
        }
        """

        slowest = PytestParser.get_slowest_tests(json_output, n=2)

        assert len(slowest) == 2
        assert slowest[0][0] == "test_b.py::test_2"
        assert slowest[0][1] == 5.0
        assert slowest[1][0] == "test_c.py::test_3"


class TestPytestCoverageIntegration:
    """Test parsing coverage data from pytest-cov."""

    def test_parse_coverage_percentage(self, mocker: MockerFixture):
        """Test extracting overall coverage percentage."""
        json_output = """
        {
            "report": {
                "tests": [{"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.01}],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            },
            "coverage": {
                "totals": {"percent_covered": 85.5}
            }
        }
        """

        coverage = PytestParser.extract_coverage_percentage(json_output)

        assert coverage == 85.5

    def test_parse_coverage_per_module(self, mocker: MockerFixture):
        """Test extracting coverage per module."""
        json_output = """
        {
            "report": {
                "tests": [{"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.01}],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            },
            "coverage": {
                "files": {
                    "src/module_a.py": {"percent_covered": 90.0, "missing_lines": [10, 15]},
                    "src/module_b.py": {"percent_covered": 75.0, "missing_lines": [20, 21, 22]}
                }
            }
        }
        """

        coverage_by_module = PytestParser.extract_coverage_by_module(json_output)

        assert coverage_by_module["src/module_a.py"] == 90.0
        assert coverage_by_module["src/module_b.py"] == 75.0

    def test_parse_missing_lines(self, mocker: MockerFixture):
        """Test extracting missing line numbers for coverage."""
        json_output = """
        {
            "report": {
                "tests": [{"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.01}],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            },
            "coverage": {
                "files": {
                    "src/module.py": {"percent_covered": 80.0, "missing_lines": [10, 15, 20]}
                }
            }
        }
        """

        missing = PytestParser.extract_missing_lines(json_output, "src/module.py")

        assert missing == [10, 15, 20]

    def test_identify_modules_below_threshold(self, mocker: MockerFixture):
        """Test identifying modules below coverage threshold."""
        json_output = """
        {
            "report": {
                "tests": [{"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.01}],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            },
            "coverage": {
                "files": {
                    "src/good.py": {"percent_covered": 95.0, "missing_lines": []},
                    "src/bad.py": {"percent_covered": 60.0, "missing_lines": [1, 2, 3]}
                }
            }
        }
        """

        below_threshold = PytestParser.get_modules_below_threshold(json_output, threshold=80.0)

        assert len(below_threshold) == 1
        assert "src/bad.py" in below_threshold
        assert below_threshold["src/bad.py"] == 60.0

    def test_parse_branch_coverage(self, mocker: MockerFixture):
        """Test extracting branch coverage when enabled."""
        json_output = """
        {
            "report": {
                "tests": [{"nodeid": "test.py::test_1", "outcome": "passed", "duration": 0.01}],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            },
            "coverage": {
                "totals": {
                    "percent_covered": 85.0,
                    "percent_covered_branches": 75.0
                }
            }
        }
        """

        branch_coverage = PytestParser.extract_branch_coverage(json_output)

        assert branch_coverage == 75.0


class TestPytestCommandBuilding:
    """Test building pytest command with various options."""

    def test_build_command_default_options(self):
        """Test building pytest command with default options."""
        files = [Path("tests/test_example.py")]
        config = {}

        cmd = PytestParser.build_command(files, config)

        assert cmd[0] == "pytest"
        assert "--json-report" in cmd
        assert str(files[0]) in cmd

    def test_build_command_with_coverage(self):
        """Test building command with coverage enabled."""
        files = [Path("tests/test_example.py")]
        config = {"coverage": True, "coverage_threshold": 90}

        cmd = PytestParser.build_command(files, config)

        assert "--cov" in cmd
        assert "--cov-report=json" in cmd

    def test_build_command_with_markers(self):
        """Test building command with test markers."""
        files = [Path("tests/")]
        config = {"markers": ["unit", "not slow"]}

        cmd = PytestParser.build_command(files, config)

        assert "-m" in cmd
        assert "unit and not slow" in cmd

    def test_build_command_with_keywords(self):
        """Test building command with keyword filter."""
        files = [Path("tests/")]
        config = {"keywords": "test_integration"}

        cmd = PytestParser.build_command(files, config)

        assert "-k" in cmd
        assert "test_integration" in cmd

    def test_build_command_with_parallel_workers(self):
        """Test building command with parallel execution."""
        files = [Path("tests/")]
        config = {"parallel": True, "workers": 4}

        cmd = PytestParser.build_command(files, config)

        assert "-n" in cmd
        assert "4" in cmd

    def test_build_command_with_reruns(self):
        """Test building command with reruns on failure."""
        files = [Path("tests/")]
        config = {"reruns": 3, "reruns_delay": 1}

        cmd = PytestParser.build_command(files, config)

        assert "--reruns" in cmd
        assert "3" in cmd
        assert "--reruns-delay" in cmd
        assert "1" in cmd

    def test_build_command_with_verbose(self):
        """Test building command with verbose output."""
        files = [Path("tests/")]
        config = {"verbose": True}

        cmd = PytestParser.build_command(files, config)

        assert "-vv" in cmd

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple test files."""
        files = [Path("tests/test_a.py"), Path("tests/test_b.py")]
        config = {}

        cmd = PytestParser.build_command(files, config)

        assert str(files[0]) in cmd
        assert str(files[1]) in cmd


class TestPytestErrorHandling:
    """Test error handling for pytest execution."""

    def test_error_when_pytest_not_installed(self, mocker: MockerFixture):
        """Test error handling when pytest is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("pytest not found"))

        files = [Path("tests/test_example.py")]

        with pytest.raises(FileNotFoundError):
            PytestParser.run_pytest(files, {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running tests."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 30))

        files = [Path("tests/test_slow.py")]
        config = {"timeout": 30}

        with pytest.raises(subprocess.TimeoutExpired):
            PytestParser.run_pytest(files, config)

    def test_parse_with_invalid_json(self, mocker: MockerFixture):
        """Test parsing with malformed JSON output."""
        invalid_json = "Not valid JSON {"

        with pytest.raises(Exception):  # JSON decode error
            PytestParser.parse_json(invalid_json, [Path("test.py")], {})

    def test_error_when_coverage_plugin_missing(self, mocker: MockerFixture):
        """Test error when pytest-cov is not installed but coverage requested."""
        mocker.patch(
            "subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="ERROR: unknown option: --cov"),
        )

        files = [Path("tests/")]
        config = {"coverage": True}

        result = PytestParser.run_pytest(files, config)
        assert result.returncode == 1


class TestPytestVersionDetection:
    """Test pytest version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting pytest version."""
        mocker.patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="pytest 7.4.3", stderr="")
        )

        version = PytestParser.get_version()

        assert version == "7.4.3"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling version detection failure."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("pytest not found"))

        version = PytestParser.get_version()

        assert version is None


class TestPytestIntegrationWithFixtures:
    """Integration tests with real pytest execution (skipped if pytest not available)."""

    @pytest.mark.skipif(not Path("pytest").exists(), reason="pytest not installed")
    def test_pytest_on_passing_test_suite(self):
        """Test running pytest on a passing test suite."""
        # This would run on actual fixture files

    @pytest.mark.skipif(not Path("pytest").exists(), reason="pytest not installed")
    def test_pytest_on_failing_test_suite(self):
        """Test running pytest on a failing test suite."""
        # This would run on actual fixture files with failures

    @pytest.mark.skipif(not Path("pytest").exists(), reason="pytest not installed")
    def test_coverage_measurement(self):
        """Test coverage measurement on sample code."""
        # This would measure coverage on fixture code


class TestPytestFlakyTestDetection:
    """Test detection of flaky tests (pass after retry)."""

    def test_detect_flaky_test(self, mocker: MockerFixture):
        """Test identifying tests that pass after retry."""
        json_output = """
        {
            "report": {
                "tests": [
                    {
                        "nodeid": "tests/test_flaky.py::test_unstable",
                        "outcome": "rerun",
                        "duration": 0.02,
                        "longrepr": "First attempt failed",
                        "wasxfail": false
                    },
                    {
                        "nodeid": "tests/test_flaky.py::test_unstable",
                        "outcome": "passed",
                        "duration": 0.02
                    }
                ],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1, "rerun": 1}
            }
        }
        """

        flaky_tests = PytestParser.detect_flaky_tests(json_output)

        assert len(flaky_tests) == 1
        assert "test_unstable" in flaky_tests[0]

    def test_no_flaky_tests(self, mocker: MockerFixture):
        """Test when no flaky tests detected."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "tests/test_stable.py::test_reliable", "outcome": "passed", "duration": 0.01}
                ],
                "summary": {"passed": 1, "failed": 0, "skipped": 0, "total": 1}
            }
        }
        """

        flaky_tests = PytestParser.detect_flaky_tests(json_output)

        assert len(flaky_tests) == 0


class TestPytestSummaryStatistics:
    """Test extracting summary statistics from pytest output."""

    def test_extract_summary_statistics(self, mocker: MockerFixture):
        """Test extracting overall test summary."""
        json_output = """
        {
            "report": {
                "tests": [
                    {"nodeid": "test1.py::test_a", "outcome": "passed", "duration": 0.01},
                    {"nodeid": "test2.py::test_b", "outcome": "failed", "duration": 0.02},
                    {"nodeid": "test3.py::test_c", "outcome": "skipped", "duration": 0.0}
                ],
                "summary": {
                    "passed": 1,
                    "failed": 1,
                    "skipped": 1,
                    "total": 3,
                    "duration": 0.03
                }
            }
        }
        """

        summary = PytestParser.extract_summary(json_output)

        assert summary["passed"] == 1
        assert summary["failed"] == 1
        assert summary["skipped"] == 1
        assert summary["total"] == 3
        assert summary["duration"] == 0.03

    def test_calculate_pass_rate(self, mocker: MockerFixture):
        """Test calculating test pass rate."""
        json_output = """
        {
            "report": {
                "tests": [],
                "summary": {"passed": 85, "failed": 10, "skipped": 5, "total": 100}
            }
        }
        """

        pass_rate = PytestParser.calculate_pass_rate(json_output)

        assert pass_rate == 85.0


class TestPytestConfigurationHandling:
    """Test pytest configuration file detection."""

    def test_detect_pytest_ini(self, tmp_path: Path):
        """Test detecting pytest.ini configuration."""
        config_file = tmp_path / "pytest.ini"
        config_file.write_text("[pytest]\nminversion = 7.0")

        found_config = PytestParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_pyproject_toml(self, tmp_path: Path):
        """Test detecting pytest config in pyproject.toml."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text('[tool.pytest.ini_options]\nminversion = "7.0"')

        found_config = PytestParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_setup_cfg(self, tmp_path: Path):
        """Test detecting pytest config in setup.cfg."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("[tool:pytest]\nminversion = 7.0")

        found_config = PytestParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_no_config_file_returns_none(self, tmp_path: Path):
        """Test returns None when no config file found."""
        found_config = PytestParser.find_config_file(tmp_path)

        assert found_config is None
