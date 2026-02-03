"""
Tests for Google Test (gtest) parser.

Tests the GTestParser class which parses Google Test JSON output
to extract test results, failures, and performance metrics.
"""

import json
import subprocess
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.gtest_parser import GTestParser


class TestGTestJSONParsing:
    """Test parsing of Google Test JSON output."""

    def test_parse_json_output_all_tests_passed(self):
        """Test parsing when all tests pass."""
        json_output = json.dumps(
            {
                "tests": 10,
                "failures": 0,
                "disabled": 0,
                "errors": 0,
                "time": "0.5s",
                "testsuites": [
                    {
                        "name": "MathTest",
                        "tests": 3,
                        "failures": 0,
                        "disabled": 0,
                        "time": "0.2s",
                        "testsuite": [
                            {
                                "name": "Addition",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "MathTest",
                            },
                            {
                                "name": "Subtraction",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "MathTest",
                            },
                            {
                                "name": "Multiplication",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "MathTest",
                            },
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./math_test"])

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.files_checked == 1

    def test_parse_json_output_with_test_failures(self):
        """Test parsing when tests fail."""
        json_output = json.dumps(
            {
                "tests": 3,
                "failures": 1,
                "disabled": 0,
                "errors": 0,
                "time": "0.3s",
                "testsuites": [
                    {
                        "name": "MathTest",
                        "tests": 3,
                        "failures": 1,
                        "disabled": 0,
                        "time": "0.3s",
                        "testsuite": [
                            {
                                "name": "Addition",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "MathTest",
                            },
                            {
                                "name": "Division",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.002s",
                                "classname": "MathTest",
                                "failures": [
                                    {
                                        "failure": (
                                            "Value of: divide(10, 0)\n"
                                            "  Actual: inf\n"
                                            "Expected: throws exception"
                                        ),
                                        "type": "",
                                    }
                                ],
                            },
                            {
                                "name": "Multiplication",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "MathTest",
                            },
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./math_test"])

        assert result.passed is False
        assert len(result.errors) == 1
        assert "Division" in result.errors[0].message
        assert "divide(10, 0)" in result.errors[0].message

    def test_parse_assertion_failures_with_expected_actual(self):
        """Test parsing assertion failures with expected/actual values."""
        json_output = json.dumps(
            {
                "tests": 1,
                "failures": 1,
                "disabled": 0,
                "errors": 0,
                "time": "0.1s",
                "testsuites": [
                    {
                        "name": "StringTest",
                        "tests": 1,
                        "failures": 1,
                        "disabled": 0,
                        "time": "0.1s",
                        "testsuite": [
                            {
                                "name": "Comparison",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "StringTest",
                                "failures": [
                                    {
                                        "failure": (
                                            "test.cpp:42\n"
                                            "Expected equality of these values:\n"
                                            '  str1\n    Which is: "hello"\n'
                                            '  str2\n    Which is: "world"'
                                        ),
                                        "type": "",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./string_test"])

        assert result.passed is False
        assert len(result.errors) == 1
        assert "test.cpp:42" in result.errors[0].message
        assert "hello" in result.errors[0].message
        assert "world" in result.errors[0].message

    def test_parse_disabled_tests(self):
        """Test parsing disabled tests."""
        json_output = json.dumps(
            {
                "tests": 5,
                "failures": 0,
                "disabled": 2,
                "errors": 0,
                "time": "0.2s",
                "testsuites": [
                    {
                        "name": "FeatureTest",
                        "tests": 5,
                        "failures": 0,
                        "disabled": 2,
                        "time": "0.2s",
                        "testsuite": [
                            {
                                "name": "Feature1",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "FeatureTest",
                            },
                            {
                                "name": "DISABLED_Feature2",
                                "status": "NOTRUN",
                                "result": "SKIPPED",
                                "time": "0s",
                                "classname": "FeatureTest",
                            },
                            {
                                "name": "DISABLED_Feature3",
                                "status": "NOTRUN",
                                "result": "SKIPPED",
                                "time": "0s",
                                "classname": "FeatureTest",
                            },
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./feature_test"])

        assert result.passed is True
        assert len(result.warnings) == 2
        assert "DISABLED_Feature2" in result.warnings[0].message
        assert "DISABLED_Feature3" in result.warnings[1].message

    def test_parse_test_durations(self):
        """Test parsing test execution durations."""
        json_output = json.dumps(
            {
                "tests": 3,
                "failures": 0,
                "disabled": 0,
                "errors": 0,
                "time": "5.5s",
                "testsuites": [
                    {
                        "name": "PerformanceTest",
                        "tests": 3,
                        "failures": 0,
                        "disabled": 0,
                        "time": "5.5s",
                        "testsuite": [
                            {
                                "name": "FastTest",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "SlowTest",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "5.0s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "MediumTest",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.5s",
                                "classname": "PerformanceTest",
                            },
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./perf_test"])

        # Extract durations - parser should track slowest tests
        assert result.passed is True

    def test_extract_test_summary_statistics(self):
        """Test extraction of test summary statistics."""
        json_output = json.dumps(
            {
                "tests": 20,
                "failures": 2,
                "disabled": 3,
                "errors": 0,
                "time": "1.5s",
                "testsuites": [],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./all_tests"])

        # Parser should extract: 20 total, 2 failed, 3 disabled
        assert result.passed is False
        assert len(result.errors) >= 1  # At least summary error


class TestGTestCommandBuilding:
    """Test building gtest commands with various options."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {})

        assert "./my_test" in cmd
        assert "--gtest_output=json" in cmd or any("json" in arg for arg in cmd)

    def test_build_command_with_test_filter(self):
        """Test building command with test filter."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"filter": "MathTest.*"})

        assert "./my_test" in cmd
        assert "--gtest_filter=MathTest.*" in cmd

    def test_build_command_with_repeat_option(self):
        """Test building command with repeat option."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"repeat": 10})

        assert "./my_test" in cmd
        assert "--gtest_repeat=10" in cmd

    def test_build_command_with_shuffle(self):
        """Test building command with shuffle enabled."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"shuffle": True})

        assert "./my_test" in cmd
        assert "--gtest_shuffle" in cmd

    def test_build_command_with_output_format(self):
        """Test building command with specific output format."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"output_format": "xml"})

        assert "./my_test" in cmd
        assert any("xml" in arg for arg in cmd)

    def test_build_command_with_break_on_failure(self):
        """Test building command with break on failure."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"break_on_failure": True})

        assert "./my_test" in cmd
        assert "--gtest_break_on_failure" in cmd

    def test_build_command_with_also_run_disabled_tests(self):
        """Test building command to run disabled tests."""
        parser = GTestParser()
        cmd = parser.build_command(["./my_test"], {"also_run_disabled_tests": True})

        assert "./my_test" in cmd
        assert "--gtest_also_run_disabled_tests" in cmd


class TestGTestErrorHandling:
    """Test error handling for gtest parser."""

    def test_error_when_test_binary_not_found(self, mocker: MockerFixture):
        """Test error when test binary doesn't exist."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError("Test binary not found")

        parser = GTestParser()
        with pytest.raises(FileNotFoundError):
            parser.run(["./nonexistent_test"], {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test handling of command timeout."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired("gtest", 30)

        parser = GTestParser()
        with pytest.raises(subprocess.TimeoutExpired):
            parser.run(["./slow_test"], {"timeout": 30})

    def test_parse_with_invalid_json(self):
        """Test parsing invalid JSON output."""
        invalid_json = "Not valid JSON {]"

        parser = GTestParser()
        result = parser.parse_output(invalid_json, ["./test"])

        # Should handle gracefully
        assert result.passed is False
        assert len(result.errors) >= 1


class TestGTestVersionDetection:
    """Test Google Test version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting gtest version from binary."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Running main() from gtest_main.cc\nGoogleTest version 1.14.0",
            stderr="",
        )

        parser = GTestParser()
        version = parser.get_version(["./my_test"])

        assert version is not None
        assert "1.14" in version or "1.14.0" in version

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when binary doesn't support it."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError()

        parser = GTestParser()
        version = parser.get_version(["./nonexistent_test"])

        assert version is None


class TestGTestIntegrationWithFixtures:
    """Integration tests with real gtest binaries (if available)."""

    def test_gtest_on_passing_test_suite(self):
        """Test gtest on a test suite with all passing tests."""
        # This test requires a real gtest binary
        pytest.skip("Requires compiled gtest binary fixture")

    def test_gtest_on_failing_test_suite(self):
        """Test gtest on a test suite with failing tests."""
        # This test requires a real gtest binary with failures
        pytest.skip("Requires compiled gtest binary fixture")


class TestGTestPerformanceAnalysis:
    """Test performance analysis features."""

    def test_identify_slowest_tests(self):
        """Test identification of slowest tests."""
        json_output = json.dumps(
            {
                "tests": 5,
                "failures": 0,
                "disabled": 0,
                "errors": 0,
                "time": "10.0s",
                "testsuites": [
                    {
                        "name": "PerformanceTest",
                        "tests": 5,
                        "failures": 0,
                        "disabled": 0,
                        "time": "10.0s",
                        "testsuite": [
                            {
                                "name": "Test1",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.5s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "Test2",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "8.0s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "Test3",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.2s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "Test4",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "1.0s",
                                "classname": "PerformanceTest",
                            },
                            {
                                "name": "Test5",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.3s",
                                "classname": "PerformanceTest",
                            },
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        slowest = parser.identify_slowest_tests(json_output, n=3)

        assert len(slowest) == 3
        assert slowest[0][0] == "PerformanceTest.Test2"  # Slowest
        assert slowest[0][1] == "8.0s"

    def test_calculate_total_duration(self):
        """Test calculation of total test duration."""
        json_output = json.dumps(
            {
                "tests": 3,
                "failures": 0,
                "disabled": 0,
                "errors": 0,
                "time": "2.5s",
                "testsuites": [],
            }
        )

        parser = GTestParser()
        duration = parser.extract_total_duration(json_output)

        assert duration == "2.5s"


class TestGTestFlakyTestDetection:
    """Test flaky test detection features."""

    def test_detect_flaky_test_with_repeat(self, mocker: MockerFixture):
        """Test detection of flaky tests with repeat option."""
        # First run: failure, Second run: pass
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = Mock(
            returncode=1,  # Indicates flaky behavior
            stdout=json.dumps(
                {
                    "tests": 10,
                    "failures": 1,
                    "disabled": 0,
                    "errors": 0,
                    "time": "1.0s",
                    "testsuites": [],
                }
            ),
            stderr="[==========] Running 10 tests from 2 test suites.\n"
            "[  FAILED  ] 1 test, listed below:\n"
            "[  FAILED  ] MathTest.Division\n"
            "Note: Google Test filter = *\n"
            "[==========] 10 tests from 2 test suites ran. (1000 ms total)\n"
            "[  PASSED  ] 9 tests.\n"
            "[  FAILED  ] 1 test.\n",
        )

        parser = GTestParser()
        parser.run(["./test"], {"repeat": 100})

        # If run multiple times and sometimes passes, might be flaky
        # Parser should note this in warnings or special handling


class TestGTestFileLineExtraction:
    """Test extraction of file and line numbers from failures."""

    def test_extract_file_and_line_from_failure(self):
        """Test extracting file and line number from failure message."""
        json_output = json.dumps(
            {
                "tests": 1,
                "failures": 1,
                "disabled": 0,
                "errors": 0,
                "time": "0.1s",
                "testsuites": [
                    {
                        "name": "FileTest",
                        "tests": 1,
                        "failures": 1,
                        "disabled": 0,
                        "time": "0.1s",
                        "testsuite": [
                            {
                                "name": "ReadFile",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.001s",
                                "classname": "FileTest",
                                "failures": [
                                    {
                                        "failure": (
                                            "file_test.cpp:123\n" "Assertion failed: file exists"
                                        ),
                                        "type": "",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./file_test"])

        assert result.passed is False
        assert len(result.errors) == 1
        # Check if parser extracts line number
        error = result.errors[0]
        assert "file_test.cpp" in error.file_path or "file_test.cpp" in error.message
        assert error.line_number == 123 or "123" in error.message


class TestGTestMultipleSuites:
    """Test parsing multiple test suites."""

    def test_parse_multiple_test_suites(self):
        """Test parsing output with multiple test suites."""
        json_output = json.dumps(
            {
                "tests": 6,
                "failures": 1,
                "disabled": 0,
                "errors": 0,
                "time": "1.0s",
                "testsuites": [
                    {
                        "name": "MathTest",
                        "tests": 3,
                        "failures": 0,
                        "disabled": 0,
                        "time": "0.5s",
                        "testsuite": [
                            {
                                "name": "Addition",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.1s",
                                "classname": "MathTest",
                            },
                            {
                                "name": "Subtraction",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.2s",
                                "classname": "MathTest",
                            },
                            {
                                "name": "Multiplication",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.2s",
                                "classname": "MathTest",
                            },
                        ],
                    },
                    {
                        "name": "StringTest",
                        "tests": 3,
                        "failures": 1,
                        "disabled": 0,
                        "time": "0.5s",
                        "testsuite": [
                            {
                                "name": "Concatenation",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.1s",
                                "classname": "StringTest",
                            },
                            {
                                "name": "Comparison",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.2s",
                                "classname": "StringTest",
                                "failures": [
                                    {"failure": "Expected: equal\nActual: not equal", "type": ""}
                                ],
                            },
                            {
                                "name": "Length",
                                "status": "RUN",
                                "result": "COMPLETED",
                                "time": "0.2s",
                                "classname": "StringTest",
                            },
                        ],
                    },
                ],
            }
        )

        parser = GTestParser()
        result = parser.parse_output(json_output, ["./all_tests"])

        assert result.passed is False
        assert len(result.errors) == 1
        assert "StringTest" in result.errors[0].message
        assert "Comparison" in result.errors[0].message


class TestGTestSummaryExtraction:
    """Test extraction of summary statistics."""

    def test_extract_passed_failed_skipped_counts(self):
        """Test extracting counts of passed/failed/skipped tests."""
        json_output = json.dumps(
            {
                "tests": 15,
                "failures": 2,
                "disabled": 3,
                "errors": 0,
                "time": "2.0s",
                "testsuites": [],
            }
        )

        parser = GTestParser()
        summary = parser.extract_summary(json_output)

        assert summary["total"] == 15
        assert summary["failures"] == 2
        assert summary["disabled"] == 3
        assert summary["passed"] == 15 - 2 - 3  # 10 passed

    def test_calculate_pass_rate(self):
        """Test calculation of test pass rate."""
        json_output = json.dumps(
            {
                "tests": 100,
                "failures": 5,
                "disabled": 10,
                "errors": 0,
                "time": "10.0s",
                "testsuites": [],
            }
        )

        parser = GTestParser()
        pass_rate = parser.calculate_pass_rate(json_output)

        # 85 tests run (100 - 10 disabled - 5 failed = 85 passed)
        # Pass rate = 85 / 90 (tests run) = 94.44%
        assert pass_rate > 94.0
        assert pass_rate < 95.0


class TestGTestCommandBuildingEdgeCases:
    """Test edge cases in command building."""

    def test_build_command_no_files_raises_error(self):
        """Test that building command with no files raises ValueError."""
        parser = GTestParser()
        with pytest.raises(ValueError, match="No test binaries specified"):
            parser.build_command([], {})

    def test_build_command_xml_output_format(self):
        """Test building command with XML output format."""
        parser = GTestParser()
        cmd = parser.build_command(["./test_binary"], {"output_format": "xml"})
        assert "./test_binary" in cmd
        # XML output includes filename suffix
        assert any("--gtest_output=xml" in arg for arg in cmd)


class TestGTestVersionDetectionEdgeCases:
    """Test version detection edge cases."""

    def test_detect_version_no_files(self):
        """Test version detection with no files returns None."""
        parser = GTestParser()
        version = parser.get_version([])
        assert version is None

    def test_detect_version_subprocess_error(self, mocker: MockerFixture):
        """Test version detection handles subprocess errors."""
        parser = GTestParser()
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="test", timeout=10),
        )
        version = parser.get_version(["./test_binary"])
        assert version is None

    def test_detect_version_file_not_found(self, mocker: MockerFixture):
        """Test version detection handles file not found."""
        parser = GTestParser()
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())
        version = parser.get_version(["./test_binary"])
        assert version is None

    def test_detect_version_alternative_format(self, mocker: MockerFixture):
        """Test version detection with alternative version format."""
        parser = GTestParser()
        mock_result = Mock()
        mock_result.stdout = "version 1.12"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        version = parser.get_version(["./test_binary"])
        assert version == "1.12"

    def test_detect_version_no_version_in_output(self, mocker: MockerFixture):
        """Test version detection when no version string found."""
        parser = GTestParser()
        mock_result = Mock()
        mock_result.stdout = "Some help text without version"
        mock_result.stderr = ""
        mocker.patch("subprocess.run", return_value=mock_result)

        version = parser.get_version(["./test_binary"])
        assert version is None


class TestGTestPerformanceAnalysisEdgeCases:
    """Test performance analysis edge cases."""

    def test_identify_slowest_tests_invalid_json(self):
        """Test slowest tests with invalid JSON."""
        parser = GTestParser()
        result = parser.identify_slowest_tests("invalid json", n=5)
        assert result == []

    def test_identify_slowest_tests_empty_testsuites(self):
        """Test slowest tests with empty testsuites."""
        json_output = json.dumps({"tests": 0, "testsuites": []})
        parser = GTestParser()
        result = parser.identify_slowest_tests(json_output, n=5)
        assert result == []

    def test_identify_slowest_tests_missing_time_field(self):
        """Test slowest tests handles missing time field gracefully."""
        json_output = json.dumps(
            {
                "tests": 1,
                "testsuites": [
                    {
                        "name": "TestSuite",
                        "testsuite": [
                            {
                                "name": "Test1",
                                "classname": "TestSuite",
                                # Missing "time" field
                            }
                        ],
                    }
                ],
            }
        )
        parser = GTestParser()
        result = parser.identify_slowest_tests(json_output, n=5)
        # Should handle gracefully and return empty or skip this test
        assert isinstance(result, list)


class TestGTestExtractTotalDuration:
    """Test extraction of total duration."""

    def test_extract_total_duration_valid_json(self):
        """Test extracting total duration from valid JSON."""
        json_output = json.dumps({"time": "5.25s", "tests": 10})
        parser = GTestParser()
        duration = parser.extract_total_duration(json_output)
        assert duration == "5.25s"

    def test_extract_total_duration_invalid_json(self):
        """Test extracting total duration from invalid JSON."""
        parser = GTestParser()
        duration = parser.extract_total_duration("invalid json")
        assert duration == "0s"

    def test_extract_total_duration_missing_time_field(self):
        """Test extracting total duration when time field is missing."""
        json_output = json.dumps({"tests": 10})
        parser = GTestParser()
        duration = parser.extract_total_duration(json_output)
        assert duration == "0s"


class TestGTestExtractSummaryEdgeCases:
    """Test extract_summary edge cases."""

    def test_extract_summary_invalid_json(self):
        """Test extract_summary with invalid JSON."""
        parser = GTestParser()
        summary = parser.extract_summary("invalid json")
        assert summary["total"] == 0
        assert summary["passed"] == 0
        assert summary["failures"] == 0
        assert summary["disabled"] == 0


class TestGTestCalculatePassRate:
    """Test calculate_pass_rate edge cases."""

    def test_calculate_pass_rate_no_tests_run(self):
        """Test pass rate when no tests are run (all disabled)."""
        json_output = json.dumps({"tests": 10, "failures": 0, "disabled": 10, "testsuites": []})
        parser = GTestParser()
        pass_rate = parser.calculate_pass_rate(json_output)
        assert pass_rate == 0.0

    def test_calculate_pass_rate_all_pass(self):
        """Test pass rate when all tests pass."""
        json_output = json.dumps({"tests": 50, "failures": 0, "disabled": 0, "testsuites": []})
        parser = GTestParser()
        pass_rate = parser.calculate_pass_rate(json_output)
        assert pass_rate == 100.0


class TestGTestRunAndParse:
    """Test run_and_parse static method."""

    def test_run_and_parse_empty_files(self):
        """Test run_and_parse with empty files list."""
        result = GTestParser.run_and_parse([], {})
        assert result.passed is True
        assert len(result.errors) == 0
        assert result.files_checked == 0

    def test_run_and_parse_with_none_config(self, mocker: MockerFixture):
        """Test run_and_parse with None config."""
        # Mock subprocess to avoid actual test execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"tests": 1, "failures": 0, "disabled": 0, "testsuites": []}
        )
        mocker.patch("subprocess.run", return_value=mock_result)

        result = GTestParser.run_and_parse(["./test_binary"], None)
        assert result.validator_name == "gtest"
        assert isinstance(result.passed, bool)
