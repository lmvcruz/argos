"""
Tests for CI log parser.

This module tests the CILogParser that extracts test results,
coverage data, and failure patterns from CI logs.
"""

import pytest
from datetime import datetime
from scout.parsers.ci_log_parser import CILogParser


class TestPytestLogParsing:
    """Test parsing pytest output from CI logs."""

    @pytest.fixture
    def parser(self):
        """Create a CILogParser instance."""
        return CILogParser()

    def test_parse_pytest_log_all_passed(self, parser):
        """Test parsing pytest log with all tests passing."""
        log_content = """
============================= test session starts ==============================
platform linux -- Python 3.10.5, pytest-7.4.0
collected 5 items

tests/test_example.py::test_function_one PASSED                          [ 20%]
tests/test_example.py::test_function_two PASSED                          [ 40%]
tests/test_example.py::test_function_three PASSED                        [ 60%]
tests/test_another.py::test_feature_a PASSED                             [ 80%]
tests/test_another.py::test_feature_b PASSED                             [100%]

============================== 5 passed in 0.25s ===============================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 5
        assert all(r["outcome"] == "passed" for r in results)
        assert results[0]["test_nodeid"] == "tests/test_example.py::test_function_one"
        assert results[4]["test_nodeid"] == "tests/test_another.py::test_feature_b"

    def test_parse_pytest_log_with_failures(self, parser):
        """Test parsing pytest log with failures."""
        log_content = """
============================= test session starts ==============================
platform linux -- Python 3.10.5, pytest-7.4.0
collected 3 items

tests/test_math.py::test_addition PASSED                                 [ 33%]
tests/test_math.py::test_division FAILED                                 [ 66%]
tests/test_math.py::test_multiplication PASSED                           [100%]

=================================== FAILURES ===================================
_______________________________ test_division __________________________________

    def test_division():
        result = divide(10, 0)
>       assert result == 5
E       ZeroDivisionError: division by zero

tests/test_math.py:15: ZeroDivisionError
=========================== short test summary info ============================
FAILED tests/test_math.py::test_division - ZeroDivisionError: division by zero
========================= 1 failed, 2 passed in 0.18s ==========================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 3
        assert results[0]["outcome"] == "passed"
        assert results[1]["outcome"] == "failed"
        assert results[2]["outcome"] == "passed"

        # Check failure details
        failed_test = results[1]
        assert failed_test["test_nodeid"] == "tests/test_math.py::test_division"
        assert "ZeroDivisionError" in failed_test["error_message"]
        assert "division by zero" in failed_test["error_message"]

    def test_parse_pytest_log_with_skipped_tests(self, parser):
        """Test parsing pytest log with skipped tests."""
        log_content = """
============================= test session starts ==============================
collected 4 items

tests/test_platform.py::test_linux_only SKIPPED (Windows only)           [ 25%]
tests/test_platform.py::test_cross_platform PASSED                       [ 50%]
tests/test_platform.py::test_windows_only SKIPPED (requires Windows)     [ 75%]
tests/test_platform.py::test_another PASSED                              [100%]

========================= 2 passed, 2 skipped in 0.15s =========================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 4
        assert results[0]["outcome"] == "skipped"
        assert results[1]["outcome"] == "passed"
        assert results[2]["outcome"] == "skipped"
        assert results[3]["outcome"] == "passed"

    def test_parse_pytest_log_with_errors(self, parser):
        """Test parsing pytest log with test errors."""
        log_content = """
============================= test session starts ==============================
collected 2 items

tests/test_setup.py::test_with_fixture ERROR                             [ 50%]
tests/test_setup.py::test_normal PASSED                                  [100%]

==================================== ERRORS ====================================
________________________ ERROR at setup of test_with_fixture _______________

@pytest.fixture
def broken_fixture():
>   raise RuntimeError("Fixture setup failed")
E   RuntimeError: Fixture setup failed

tests/test_setup.py:8: RuntimeError
=========================== short test summary info ============================
ERROR tests/test_setup.py::test_with_fixture - RuntimeError: Fixture setup failed
========================== 1 passed, 1 error in 0.12s ==========================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 2
        assert results[0]["outcome"] == "error"
        assert results[1]["outcome"] == "passed"

        error_test = results[0]
        assert error_test["test_nodeid"] == "tests/test_setup.py::test_with_fixture"
        assert "RuntimeError" in error_test["error_message"]
        assert "Fixture setup failed" in error_test["error_message"]

    def test_parse_pytest_log_with_durations(self, parser):
        """Test parsing pytest log with test durations."""
        log_content = """
============================= test session starts ==============================
collected 3 items

tests/test_slow.py::test_fast PASSED                                     [ 33%]
tests/test_slow.py::test_medium PASSED                                   [ 66%]
tests/test_slow.py::test_very_slow PASSED                                [100%]

================================ slowest durations ================================
2.50s call     tests/test_slow.py::test_very_slow
0.75s call     tests/test_slow.py::test_medium
0.05s call     tests/test_slow.py::test_fast

============================== 3 passed in 3.30s ===============================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 3
        # Check durations extracted
        assert results[0]["test_nodeid"] == "tests/test_slow.py::test_fast"
        assert results[1]["test_nodeid"] == "tests/test_slow.py::test_medium"
        assert results[2]["test_nodeid"] == "tests/test_slow.py::test_very_slow"

    def test_parse_pytest_log_extract_traceback(self, parser):
        """Test extraction of full error traceback."""
        log_content = """
============================= test session starts ==============================
collected 1 items

tests/test_complex.py::test_nested_call FAILED                           [100%]

=================================== FAILURES ===================================
_____________________________ test_nested_call _________________________________

    def test_nested_call():
        result = outer_function()
>       assert result == "expected"
E       AssertionError: assert 'actual' == 'expected'
E         - expected
E         + actual

tests/test_complex.py:25: AssertionError

During handling of the above exception, another exception occurred:

    def outer_function():
        return inner_function()

    def inner_function():
>       return "actual"

tests/test_complex.py:10: AssertionError
=========================== short test summary info ============================
FAILED tests/test_complex.py::test_nested_call - AssertionError: assert 'actual' == 'expected'
========================= 1 failed in 0.08s ============================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 1
        failed_test = results[0]
        assert failed_test["outcome"] == "failed"
        assert "AssertionError" in failed_test["error_message"]
        assert failed_test["error_traceback"] is not None
        assert "assert 'actual' == 'expected'" in failed_test["error_traceback"]

    def test_parse_pytest_log_with_parametrized_tests(self, parser):
        """Test parsing parametrized tests."""
        log_content = """
============================= test session starts ==============================
collected 6 items

tests/test_param.py::test_values[1-2-3] PASSED                           [ 16%]
tests/test_param.py::test_values[4-5-9] PASSED                           [ 33%]
tests/test_param.py::test_values[10-20-30] PASSED                        [ 50%]
tests/test_param.py::test_edge[zero] FAILED                              [ 66%]
tests/test_param.py::test_edge[negative] PASSED                          [ 83%]
tests/test_param.py::test_edge[large] PASSED                             [100%]

=================================== FAILURES ===================================
______________________________ test_edge[zero] _________________________________

param = 'zero'

    @pytest.mark.parametrize('param', ['zero', 'negative', 'large'])
    def test_edge(param):
>       assert param != 'zero'
E       AssertionError

tests/test_param.py:12: AssertionError
========================= 1 failed, 5 passed in 0.22s ==========================
"""
        results = parser.parse_pytest_log(log_content)

        assert len(results) == 6
        assert results[0]["test_nodeid"] == "tests/test_param.py::test_values[1-2-3]"
        assert results[3]["test_nodeid"] == "tests/test_param.py::test_edge[zero]"
        assert results[3]["outcome"] == "failed"

    def test_parse_pytest_empty_log(self, parser):
        """Test parsing empty pytest log."""
        results = parser.parse_pytest_log("")
        assert results == []

    def test_parse_pytest_log_no_collection(self, parser):
        """Test parsing pytest log with no tests collected."""
        log_content = """
============================= test session starts ==============================
collected 0 items

============================ no tests ran in 0.01s =============================
"""
        results = parser.parse_pytest_log(log_content)
        assert results == []


class TestCoverageLogParsing:
    """Test parsing coverage output from CI logs."""

    @pytest.fixture
    def parser(self):
        """Create a CILogParser instance."""
        return CILogParser()

    def test_parse_coverage_log_basic(self, parser):
        """Test parsing basic coverage output."""
        log_content = """
---------- coverage: platform linux, python 3.10.5 -----------
Name                     Stmts   Miss  Cover
--------------------------------------------
src/module_a.py             45      3    93%
src/module_b.py             78      0   100%
src/module_c.py            120     15    88%
--------------------------------------------
TOTAL                      243     18    93%
"""
        coverage_data = parser.parse_coverage_log(log_content)

        assert coverage_data["total_coverage"] == 93.0
        assert coverage_data["total_statements"] == 243
        assert coverage_data["total_missing"] == 18
        assert len(coverage_data["modules"]) == 3

        assert coverage_data["modules"][0]["name"] == "src/module_a.py"
        assert coverage_data["modules"][0]["coverage"] == 93.0
        assert coverage_data["modules"][1]["coverage"] == 100.0

    def test_parse_coverage_log_with_missing_lines(self, parser):
        """Test parsing coverage with missing line numbers."""
        log_content = """
---------- coverage: platform linux, python 3.10.5 -----------
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
src/module_a.py             45      3    93%   12, 25-27
src/module_b.py             78      0   100%
------------------------------------------------------
TOTAL                      123      3    98%
"""
        coverage_data = parser.parse_coverage_log(log_content)

        assert coverage_data["modules"][0]["missing_lines"] == "12, 25-27"
        assert coverage_data["modules"][1]["missing_lines"] == ""

    def test_parse_coverage_log_empty(self, parser):
        """Test parsing empty coverage log."""
        coverage_data = parser.parse_coverage_log("")
        assert coverage_data is None


class TestFlake8LogParsing:
    """Test parsing flake8 output from CI logs."""

    @pytest.fixture
    def parser(self):
        """Create a CILogParser instance."""
        return CILogParser()

    def test_parse_flake8_log_with_violations(self, parser):
        """Test parsing flake8 log with violations."""
        log_content = """
./src/module_a.py:15:1: E302 expected 2 blank lines, found 1
./src/module_a.py:42:80: E501 line too long (85 > 79 characters)
./src/module_b.py:10:5: F401 'os' imported but unused
./src/module_c.py:25:10: W291 trailing whitespace
"""
        violations = parser.parse_flake8_log(log_content)

        assert len(violations) == 4
        assert violations[0]["file"] == "./src/module_a.py"
        assert violations[0]["line"] == 15
        assert violations[0]["column"] == 1
        assert violations[0]["code"] == "E302"
        assert "expected 2 blank lines" in violations[0]["message"]

        assert violations[2]["code"] == "F401"
        assert violations[3]["code"] == "W291"

    def test_parse_flake8_log_no_violations(self, parser):
        """Test parsing flake8 log with no violations."""
        violations = parser.parse_flake8_log("")
        assert violations == []


class TestFailurePatternDetection:
    """Test detection of common failure patterns in CI logs."""

    @pytest.fixture
    def parser(self):
        """Create a CILogParser instance."""
        return CILogParser()

    def test_detect_timeout_pattern(self, parser):
        """Test detection of timeout failures."""
        log_content = """
tests/test_slow.py::test_long_running FAILED

=================================== FAILURES ===================================
_____________________________ test_long_running ________________________________

    @pytest.mark.timeout(30)
    def test_long_running():
>       time.sleep(60)
E       Failed: Timeout >30.0s

tests/test_slow.py:15: Failed
"""
        patterns = parser.detect_failure_patterns(log_content)

        assert len(patterns) > 0
        timeout_patterns = [p for p in patterns if p["type"] == "timeout"]
        assert len(timeout_patterns) > 0
        assert "timeout" in timeout_patterns[0]["description"].lower()

    def test_detect_platform_specific_pattern(self, parser):
        """Test detection of platform-specific failures."""
        log_content = """
tests/test_symlink.py::test_create_symlink SKIPPED [ 50%]
tests/test_symlink.py::test_follow_symlink SKIPPED [100%]

SKIPPED [2] tests/test_symlink.py:10: requires Unix
========================= 2 skipped in 0.05s ==========================
"""
        patterns = parser.detect_failure_patterns(log_content)

        platform_patterns = [p for p in patterns if p["type"] == "platform-specific"]
        assert len(platform_patterns) > 0
        assert "Unix" in platform_patterns[0]["description"] or "platform" in platform_patterns[0]["description"].lower()

    def test_detect_setup_failure_pattern(self, parser):
        """Test detection of setup/fixture failures."""
        log_content = """
ERROR at setup of test_with_database

@pytest.fixture
def database():
>   conn = psycopg2.connect(...)
E   psycopg2.OperationalError: could not connect to server

tests/conftest.py:25: OperationalError
"""
        patterns = parser.detect_failure_patterns(log_content)

        setup_patterns = [p for p in patterns if p["type"] == "setup"]
        assert len(setup_patterns) > 0
        assert "setup" in setup_patterns[0]["description"].lower() or "fixture" in setup_patterns[0]["description"].lower()

    def test_detect_import_error_pattern(self, parser):
        """Test detection of import/dependency errors."""
        log_content = """
ERROR collecting tests/test_feature.py

ImportError while importing test module 'tests/test_feature.py'.
Hint: make sure your test file is named test_*.py or *_test.py
tests/test_feature.py:5: in <module>
    from external_package import SomeClass
E   ModuleNotFoundError: No module named 'external_package'
"""
        patterns = parser.detect_failure_patterns(log_content)

        import_patterns = [p for p in patterns if p["type"] == "dependency"]
        assert len(import_patterns) > 0
        assert "ModuleNotFoundError" in import_patterns[0]["description"] or "import" in import_patterns[0]["description"].lower()

    def test_detect_multiple_patterns(self, parser):
        """Test detection of multiple different failure patterns."""
        log_content = """
ERROR at setup of test_db
E   OperationalError: database connection failed

tests/test_slow.py FAILED
E   Failed: Timeout >30.0s

ImportError: No module named 'missing_package'

tests/test_symlink.py SKIPPED (requires Unix)
"""
        patterns = parser.detect_failure_patterns(log_content)

        pattern_types = {p["type"] for p in patterns}
        # Should detect multiple different pattern types
        assert len(pattern_types) >= 2

    def test_no_patterns_in_successful_log(self, parser):
        """Test that successful logs don't produce failure patterns."""
        log_content = """
============================= test session starts ==============================
collected 10 items

tests/test_example.py::test_one PASSED                                   [ 10%]
tests/test_example.py::test_two PASSED                                   [ 20%]
tests/test_example.py::test_three PASSED                                 [ 30%]
tests/test_example.py::test_four PASSED                                  [ 40%]
tests/test_example.py::test_five PASSED                                  [ 50%]
tests/test_example.py::test_six PASSED                                   [ 60%]
tests/test_example.py::test_seven PASSED                                 [ 70%]
tests/test_example.py::test_eight PASSED                                 [ 80%]
tests/test_example.py::test_nine PASSED                                  [ 90%]
tests/test_example.py::test_ten PASSED                                   [100%]

============================== 10 passed in 2.50s ===============================
"""
        patterns = parser.detect_failure_patterns(log_content)

        # Successful logs should not produce failure patterns
        assert len(patterns) == 0
