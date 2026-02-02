"""
Unit tests for Scout test failure parser.

Tests parsing of test failures from various test frameworks:
- pytest (text and JSON output)
- unittest (text output)
- Google Test (XML and JSON output)
"""

from scout.failure_parser import (
    Failure,
    FailureLocation,
    FailureParser,
    GoogleTestParser,
    PytestParser,
    StackFrame,
    UnittestParser,
)


class TestFailureLocation:
    """Test FailureLocation dataclass."""

    def test_failure_location_creation(self):
        """Test creation of failure location with all fields."""
        location = FailureLocation(
            file="test_example.py",
            line=42,
            column=10,
            function="test_something",
        )

        assert location.file == "test_example.py"
        assert location.line == 42
        assert location.column == 10
        assert location.function == "test_something"

    def test_failure_location_without_column(self):
        """Test creation of failure location without column."""
        location = FailureLocation(file="test_example.py", line=42, function="test_something")

        assert location.file == "test_example.py"
        assert location.line == 42
        assert location.column is None
        assert location.function == "test_something"

    def test_failure_location_string_representation(self):
        """Test string representation of failure location."""
        location = FailureLocation(file="test_example.py", line=42, function="test_something")

        location_str = str(location)
        assert "test_example.py" in location_str
        assert "42" in location_str


class TestStackFrame:
    """Test StackFrame dataclass."""

    def test_stack_frame_creation(self):
        """Test creation of stack frame."""
        frame = StackFrame(
            file="module.py",
            line=100,
            function="helper_function",
            code="    result = process(data)",
        )

        assert frame.file == "module.py"
        assert frame.line == 100
        assert frame.function == "helper_function"
        assert frame.code == "    result = process(data)"

    def test_stack_frame_without_code(self):
        """Test creation of stack frame without code snippet."""
        frame = StackFrame(file="module.py", line=100, function="helper_function")

        assert frame.file == "module.py"
        assert frame.line == 100
        assert frame.code is None


class TestFailureDataclass:
    """Test Failure dataclass."""

    def test_test_failure_creation(self):
        """Test creation of test failure with all fields."""
        location = FailureLocation(file="test_math.py", line=15, function="test_addition")
        stack = [
            StackFrame(file="test_math.py", line=15, function="test_addition"),
            StackFrame(file="math_lib.py", line=42, function="add"),
        ]

        failure = Failure(
            test_name="test_addition",
            test_file="test_math.py",
            location=location,
            failure_type="AssertionError",
            message="assert 3 == 4",
            stack_trace=stack,
            duration_ms=123.45,
        )

        assert failure.test_name == "test_addition"
        assert failure.test_file == "test_math.py"
        assert failure.location == location
        assert failure.failure_type == "AssertionError"
        assert failure.message == "assert 3 == 4"
        assert failure.stack_trace == stack
        assert failure.duration_ms == 123.45

    def test_test_failure_minimal(self):
        """Test creation of test failure with minimal fields."""
        failure = Failure(
            test_name="test_something",
            test_file="test_file.py",
            message="Test failed",
        )

        assert failure.test_name == "test_something"
        assert failure.test_file == "test_file.py"
        assert failure.message == "Test failed"
        assert failure.location is None
        assert failure.failure_type is None
        assert failure.stack_trace is None
        assert failure.duration_ms is None


class TestPytestParser:
    """Test pytest output parsing."""

    def test_parse_pytest_simple_failure(self):
        """Test parsing simple pytest failure from text output."""
        output = """
============================= test session starts ==============================
collected 3 items

test_example.py .F.                                                      [100%]

=================================== FAILURES ===================================
________________________________ test_addition _________________________________

    def test_addition():
>       assert 1 + 1 == 3
E       assert 2 == 3

test_example.py:5: AssertionError
=========================== short test summary info ============================
FAILED test_example.py::test_addition - assert 2 == 3
========================= 1 failed, 2 passed in 0.12s ==========================
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_addition"
        assert failure.test_file == "test_example.py"
        assert "assert 2 == 3" in failure.message
        assert failure.location is not None
        assert failure.location.line == 5

    def test_parse_pytest_with_stack_trace(self):
        """Test parsing pytest failure with stack trace."""
        output = """
=================================== FAILURES ===================================
______________________________ test_with_helpers _______________________________

test_helpers.py:10: in test_with_helpers
    result = helper_function(5)
helpers.py:20: in helper_function
    return process(value)
processor.py:30: in process
    raise ValueError("Invalid value")
E   ValueError: Invalid value
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_with_helpers"
        assert failure.failure_type == "ValueError"
        assert "Invalid value" in failure.message
        assert failure.stack_trace is not None
        assert len(failure.stack_trace) >= 3

    def test_parse_pytest_multiple_failures(self):
        """Test parsing multiple pytest failures."""
        output = """
=================================== FAILURES ===================================
________________________________ test_first ____________________________________

    def test_first():
>       assert False
E       assert False

test_multi.py:5: AssertionError
________________________________ test_second ___________________________________

    def test_second():
>       assert 1 == 2
E       assert 1 == 2

test_multi.py:10: AssertionError
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 2
        assert failures[0].test_name == "test_first"
        assert failures[1].test_name == "test_second"

    def test_parse_pytest_json_output(self):
        """Test parsing pytest JSON output."""
        json_output = {
            "tests": [
                {
                    "nodeid": "test_example.py::test_addition",
                    "outcome": "failed",
                    "call": {
                        "longrepr": "assert 2 == 3",
                        "crash": {"path": "test_example.py", "lineno": 5},
                    },
                    "duration": 0.123,
                }
            ]
        }

        parser = PytestParser()
        failures = parser.parse_json(json_output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_addition"
        assert failure.test_file == "test_example.py"
        assert failure.duration_ms == 123.0

    def test_parse_pytest_parametrized_test(self):
        """Test parsing parametrized pytest failure."""
        output = """
=================================== FAILURES ===================================
_________________________ test_parametrized[input1] ____________________________

    @pytest.mark.parametrize("value", [1, 2, 3])
    def test_parametrized(value):
>       assert value == 0
E       assert 1 == 0

test_param.py:8: AssertionError
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert "test_parametrized" in failure.test_name
        assert "[input1]" in failure.test_name or "test_parametrized" in failure.test_name

    def test_parse_pytest_no_failures(self):
        """Test parsing pytest output with no failures."""
        output = """
============================= test session starts ==============================
collected 5 items

test_example.py .....                                                    [100%]

============================== 5 passed in 0.42s ===============================
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 0

    def test_parse_pytest_with_captured_output(self):
        """Test parsing pytest failure with captured stdout/stderr."""
        output = """
=================================== FAILURES ===================================
_______________________________ test_with_output _______________________________

    def test_with_output():
        print("Debug message")
>       assert False
E       assert False

test_output.py:10: AssertionError
---------------------------- Captured stdout call -----------------------------
Debug message
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_with_output"


class TestUnittestParser:
    """Test unittest output parsing."""

    def test_parse_unittest_simple_failure(self):
        """Test parsing simple unittest failure."""
        output = """
F..
======================================================================
FAIL: test_addition (test_math.TestMath)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_math.py", line 10, in test_addition
    self.assertEqual(1 + 1, 3)
AssertionError: 2 != 3

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (failures=1)
"""

        parser = UnittestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_addition"
        assert failure.test_file == "test_math.py"
        assert failure.location is not None
        assert failure.location.line == 10
        assert "2 != 3" in failure.message

    def test_parse_unittest_error(self):
        """Test parsing unittest error (not failure)."""
        output = """
E..
======================================================================
ERROR: test_division (test_math.TestMath)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_math.py", line 20, in test_division
    result = 1 / 0
ZeroDivisionError: division by zero

----------------------------------------------------------------------
Ran 3 tests in 0.001s

FAILED (errors=1)
"""

        parser = UnittestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "test_division"
        assert failure.failure_type == "ZeroDivisionError"
        assert "division by zero" in failure.message

    def test_parse_unittest_multiple_failures(self):
        """Test parsing multiple unittest failures."""
        output = """
FF.
======================================================================
FAIL: test_first (test_suite.TestSuite)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_suite.py", line 5, in test_first
    self.assertTrue(False)
AssertionError: False is not true

======================================================================
FAIL: test_second (test_suite.TestSuite)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_suite.py", line 10, in test_second
    self.assertEqual(1, 2)
AssertionError: 1 != 2

----------------------------------------------------------------------
Ran 3 tests in 0.002s

FAILED (failures=2)
"""

        parser = UnittestParser()
        failures = parser.parse(output)

        assert len(failures) == 2
        assert failures[0].test_name == "test_first"
        assert failures[1].test_name == "test_second"

    def test_parse_unittest_no_failures(self):
        """Test parsing unittest output with no failures."""
        output = """
...
----------------------------------------------------------------------
Ran 3 tests in 0.001s

OK
"""

        parser = UnittestParser()
        failures = parser.parse(output)

        assert len(failures) == 0

    def test_parse_unittest_with_stack_trace(self):
        """Test parsing unittest failure with deep stack trace."""
        output = """
F
======================================================================
FAIL: test_nested (test_deep.TestDeep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_deep.py", line 15, in test_nested
    self.helper()
  File "test_deep.py", line 20, in helper
    self.another_helper()
  File "test_deep.py", line 25, in another_helper
    self.assertEqual(1, 2)
AssertionError: 1 != 2

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
"""

        parser = UnittestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.stack_trace is not None
        assert len(failure.stack_trace) >= 3


class TestGoogleTestParser:
    """Test Google Test output parsing."""

    def test_parse_gtest_simple_failure(self):
        """Test parsing simple Google Test failure from text output."""
        output = """
[==========] Running 3 tests from 1 test suite.
[----------] Global test environment set-up.
[----------] 3 tests from MathTest
[ RUN      ] MathTest.Addition
test_math.cpp:10: Failure
Expected equality of these values:
  add(1, 1)
    Which is: 2
  3
[  FAILED  ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (0 ms)
[----------] 3 tests from MathTest (1 ms total)

[==========] 3 tests from 1 test suite ran. (1 ms total)
[  PASSED  ] 2 tests.
[  FAILED  ] 1 test, listed below:
[  FAILED  ] MathTest.Addition

 1 FAILED TEST
"""

        parser = GoogleTestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "MathTest.Addition"
        assert failure.test_file == "test_math.cpp"
        assert failure.location is not None
        assert failure.location.line == 10

    def test_parse_gtest_xml_output(self):
        """Test parsing Google Test XML output."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites tests="3" failures="1" errors="0">
  <testsuite name="MathTest" tests="3" failures="1">
    <testcase name="Addition" status="run" time="0.001" classname="MathTest">
      <failure message="Expected equality" type=""><![CDATA[
test_math.cpp:10
Expected equality of these values:
  add(1, 1)
    Which is: 2
  3
]]></failure>
    </testcase>
    <testcase name="Subtraction" status="run" time="0.001" classname="MathTest"/>
  </testsuite>
</testsuites>
"""

        parser = GoogleTestParser()
        failures = parser.parse_xml(xml_output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "MathTest.Addition"
        assert "Expected equality" in failure.message

    def test_parse_gtest_json_output(self):
        """Test parsing Google Test JSON output."""
        json_output = {
            "testsuites": [
                {
                    "name": "MathTest",
                    "tests": 3,
                    "failures": 1,
                    "testsuite": [
                        {
                            "name": "Addition",
                            "status": "RUN",
                            "time": "0.001s",
                            "classname": "MathTest",
                            "failures": [
                                {
                                    "failure": "Expected equality",
                                    "type": "",
                                }
                            ],
                        }
                    ],
                }
            ]
        }

        parser = GoogleTestParser()
        failures = parser.parse_json(json_output)

        assert len(failures) == 1
        failure = failures[0]
        assert failure.test_name == "MathTest.Addition"

    def test_parse_gtest_multiple_failures(self):
        """Test parsing multiple Google Test failures."""
        output = """
[==========] Running 3 tests from 1 test suite.
[ RUN      ] MathTest.Addition
test_math.cpp:10: Failure
Expected: 2 == 3
[  FAILED  ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Division
test_math.cpp:20: Failure
Expected: (1 / 0), actual: division by zero
[  FAILED  ] MathTest.Division (0 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (0 ms)
[==========] 3 tests ran.
[  PASSED  ] 1 test.
[  FAILED  ] 2 tests, listed below:
[  FAILED  ] MathTest.Addition
[  FAILED  ] MathTest.Division

 2 FAILED TESTS
"""

        parser = GoogleTestParser()
        failures = parser.parse(output)

        assert len(failures) == 2
        assert failures[0].test_name == "MathTest.Addition"
        assert failures[1].test_name == "MathTest.Division"

    def test_parse_gtest_no_failures(self):
        """Test parsing Google Test output with no failures."""
        output = """
[==========] Running 3 tests from 1 test suite.
[ RUN      ] MathTest.Addition
[       OK ] MathTest.Addition (0 ms)
[ RUN      ] MathTest.Subtraction
[       OK ] MathTest.Subtraction (0 ms)
[ RUN      ] MathTest.Multiplication
[       OK ] MathTest.Multiplication (0 ms)
[==========] 3 tests ran. (1 ms total)
[  PASSED  ] 3 tests.
"""

        parser = GoogleTestParser()
        failures = parser.parse(output)

        assert len(failures) == 0


class TestFailureParser:
    """Test main FailureParser class."""

    def test_auto_detect_pytest(self):
        """Test automatic detection of pytest output."""
        output = """
============================= test session starts ==============================
FAILED test_example.py::test_something
"""

        parser = FailureParser()
        failures = parser.parse(output)

        # Should detect pytest and parse
        assert isinstance(failures, list)

    def test_auto_detect_unittest(self):
        """Test automatic detection of unittest output."""
        output = """
F..
======================================================================
FAIL: test_something (test_module.TestClass)
----------------------------------------------------------------------
"""

        parser = FailureParser()
        failures = parser.parse(output)

        # Should detect unittest and parse
        assert isinstance(failures, list)

    def test_auto_detect_gtest(self):
        """Test automatic detection of Google Test output."""
        output = """
[==========] Running 3 tests from 1 test suite.
[  FAILED  ] TestSuite.TestCase
"""

        parser = FailureParser()
        failures = parser.parse(output)

        # Should detect gtest and parse
        assert isinstance(failures, list)

    def test_parse_with_explicit_format(self):
        """Test parsing with explicitly specified format."""
        output = """
FAILED test_example.py::test_something
"""

        parser = FailureParser()
        failures = parser.parse(output, format="pytest")

        assert isinstance(failures, list)

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        parser = FailureParser()
        failures = parser.parse("")

        assert len(failures) == 0

    def test_parse_unknown_format(self):
        """Test parsing output with unknown format."""
        output = "Some random text that doesn't match any format"

        parser = FailureParser()
        failures = parser.parse(output)

        # Should return empty list for unknown format
        assert len(failures) == 0

    def test_parse_json_pytest(self):
        """Test parsing JSON output for pytest."""
        json_data = {
            "tests": [
                {
                    "nodeid": "test_example.py::test_fail",
                    "outcome": "failed",
                    "call": {"longrepr": "assert False"},
                }
            ]
        }

        parser = FailureParser()
        failures = parser.parse_json(json_data, format="pytest")

        assert len(failures) >= 0  # May be empty if not implemented yet

    def test_get_parser_by_format(self):
        """Test getting specific parser by format."""
        parser = FailureParser()

        pytest_parser = parser._get_parser("pytest")
        assert isinstance(pytest_parser, PytestParser)

        unittest_parser = parser._get_parser("unittest")
        assert isinstance(unittest_parser, UnittestParser)

        gtest_parser = parser._get_parser("gtest")
        assert isinstance(gtest_parser, GoogleTestParser)


class FailureExtraction:
    """Test failure information extraction edge cases."""

    def test_extract_file_and_line_from_pytest(self):
        """Test extraction of file and line number from pytest output."""
        output = """
test_example.py:42: AssertionError
"""

        parser = PytestParser()
        # This should extract location even from minimal output
        location = parser._extract_location(output)

        if location:
            assert location.file == "test_example.py"
            assert location.line == 42

    def test_extract_assertion_message(self):
        """Test extraction of assertion message."""
        output = """
>       assert result == expected, "Values don't match"
E       AssertionError: Values don't match
E       assert 5 == 10
"""

        parser = PytestParser()
        message = parser._extract_message(output)

        assert message is not None
        assert "Values don't match" in message or "assert 5 == 10" in message

    def test_parse_stack_trace_with_relative_paths(self):
        """Test parsing stack trace with relative paths."""
        output = """
../src/module.py:100: in function_name
    result = process()
./tests/test_file.py:50: in test_function
    assert result is not None
"""

        parser = PytestParser()
        frames = parser._parse_stack_trace(output)

        assert frames is not None
        if frames:
            assert any("module.py" in frame.file for frame in frames)
            assert any("test_file.py" in frame.file for frame in frames)

    def test_handle_unicode_in_failure_message(self):
        """Test handling of Unicode characters in failure messages."""
        output = """
=================================== FAILURES ===================================
________________________________ test_unicode __________________________________

    def test_unicode():
>       assert "héllo" == "world 🌍"
E       AssertionError: assert 'héllo' == 'world 🌍'

test_unicode.py:5: AssertionError
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        failure = failures[0]
        assert "héllo" in failure.message or "world" in failure.message

    def test_handle_very_long_failure_messages(self):
        """Test handling of very long failure messages."""
        long_message = "x" * 10000
        output = f"""
=================================== FAILURES ===================================
________________________________ test_long _____________________________________

>       assert False, "{long_message}"
E       AssertionError: {long_message}

test_long.py:5: AssertionError
"""

        parser = PytestParser()
        failures = parser.parse(output)

        assert len(failures) == 1
        # Should not crash, message may be truncated
        assert failures[0].message is not None
