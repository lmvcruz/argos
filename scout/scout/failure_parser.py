"""
Test failure parser for Scout.

Parses test output from various test frameworks to extract failure information:
- pytest (text and JSON output)
- unittest (text output)
- Google Test (text, XML, and JSON output)
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class FailureLocation:
    """
    Represents the location of a test failure.

    Args:
        file: File path where the failure occurred
        line: Line number of the failure
        column: Optional column number
        function: Optional function/method name
    """

    file: str
    line: int
    column: Optional[int] = None
    function: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation of failure location."""
        if self.column:
            return f"{self.file}:{self.line}:{self.column}"
        return f"{self.file}:{self.line}"


@dataclass
class StackFrame:
    """
    Represents a single frame in a stack trace.

    Args:
        file: File path for this frame
        line: Line number in the file
        function: Function name
        code: Optional code snippet
    """

    file: str
    line: int
    function: str
    code: Optional[str] = None


@dataclass
class Failure:
    """
    Represents a single test failure.

    Args:
        test_name: Name of the failed test
        test_file: File containing the test
        message: Failure message
        location: Optional failure location
        failure_type: Optional exception/failure type
        stack_trace: Optional stack trace frames
        duration_ms: Optional test duration in milliseconds
    """

    test_name: str
    test_file: str
    message: str
    location: Optional[FailureLocation] = None
    failure_type: Optional[str] = None
    stack_trace: Optional[List[StackFrame]] = None
    duration_ms: Optional[float] = None


class PytestParser:
    """Parser for pytest output."""

    # Patterns for parsing pytest output
    FAILURE_HEADER = re.compile(r"_{10,}\s+(\S+)\s+_{10,}")
    FILE_LINE = re.compile(r"(\S+\.py):(\d+)(?::(\d+))?:?\s+(\w+)?")
    ASSERTION_LINE = re.compile(r"^E\s+(.+)$", re.MULTILINE)
    STACK_FRAME = re.compile(r"^(\S+\.py):(\d+):\s+in\s+(\S+)")
    TEST_NODE = re.compile(r"(\S+\.py)::(\S+)")

    def parse(self, output: str) -> List[Failure]:
        """
        Parse pytest text output to extract failures.

        Args:
            output: Raw pytest output text

        Returns:
            List of Failure objects
        """
        failures = []

        # Find the FAILURES section
        if "FAILURES" not in output and "FAILED" not in output:
            return failures

        # Split by failure headers
        sections = self.FAILURE_HEADER.split(output)

        # Process each failure section
        i = 1
        while i < len(sections):
            test_name = sections[i].strip()
            failure_content = sections[i + 1] if i + 1 < len(sections) else ""

            failure = self._parse_failure_section(test_name, failure_content)
            if failure:
                failures.append(failure)

            i += 2

        # Also check for short test summary info
        if "short test summary info" in output.lower():
            summary_failures = self._parse_summary_section(output)
            # Merge with existing failures or add new ones
            for sf in summary_failures:
                if not any(f.test_name == sf.test_name for f in failures):
                    failures.append(sf)

        return failures

    def _parse_failure_section(self, test_name: str, content: str) -> Optional[Failure]:
        """Parse a single failure section."""
        # Extract file and line from content
        location = self._extract_location(content)

        # Extract failure message
        message = self._extract_message(content)

        # Extract stack trace
        stack_trace = self._parse_stack_trace(content)

        # Determine test file
        test_file = location.file if location else "unknown"

        # Extract failure type from message
        failure_type = self._extract_failure_type(message)

        return Failure(
            test_name=test_name,
            test_file=test_file,
            message=message or "Test failed",
            location=location,
            failure_type=failure_type,
            stack_trace=stack_trace,
        )

    def _extract_location(self, content: str) -> Optional[FailureLocation]:
        """Extract file location from content."""
        match = self.FILE_LINE.search(content)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            col_num = int(match.group(3)) if match.group(3) else None
            func_name = match.group(4)

            return FailureLocation(
                file=file_path, line=line_num, column=col_num, function=func_name
            )
        return None

    def _extract_message(self, content: str) -> Optional[str]:
        """Extract failure message from content."""
        # Find all assertion lines (lines starting with E)
        assertion_lines = self.ASSERTION_LINE.findall(content)

        if assertion_lines:
            # Combine assertion lines into message
            return "\n".join(assertion_lines)

        # Fallback: look for common error patterns
        lines = content.split("\n")
        for line in lines:
            if "Error:" in line or "Exception:" in line:
                return line.strip()

        return None

    def _parse_stack_trace(self, content: str) -> Optional[List[StackFrame]]:
        """Parse stack trace from content."""
        frames = []

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.STACK_FRAME.match(line)
            if match:
                file_path = match.group(1)
                line_num = int(match.group(2))
                func_name = match.group(3)

                # Next line might contain code snippet
                code_snippet = None
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not self.STACK_FRAME.match(next_line):
                        code_snippet = next_line

                frames.append(
                    StackFrame(
                        file=file_path,
                        line=line_num,
                        function=func_name,
                        code=code_snippet,
                    )
                )

            i += 1

        return frames if frames else None

    def _extract_failure_type(self, message: Optional[str]) -> Optional[str]:
        """Extract failure type from message."""
        if not message:
            return None

        # Look for exception types
        error_pattern = re.compile(r"(\w+(?:Error|Exception))")
        match = error_pattern.search(message)
        if match:
            return match.group(1)

        # Default to AssertionError for assert statements
        if "assert" in message.lower():
            return "AssertionError"

        return None

    def _parse_summary_section(self, output: str) -> List[Failure]:
        """Parse short test summary info section."""
        failures = []

        # Find summary section
        summary_match = re.search(
            r"short test summary info.*?(?=\n=|$)", output, re.DOTALL | re.IGNORECASE
        )
        if not summary_match:
            return failures

        summary_text = summary_match.group(0)

        # Parse FAILED lines
        failed_pattern = re.compile(r"FAILED\s+(\S+)\s*-?\s*(.*)?")
        for match in failed_pattern.finditer(summary_text):
            test_path = match.group(1)
            message = match.group(2) or "Test failed"

            # Extract test name and file
            node_match = self.TEST_NODE.match(test_path)
            if node_match:
                test_file = node_match.group(1)
                test_name = node_match.group(2)
            else:
                test_file = "unknown"
                test_name = test_path

            failures.append(Failure(test_name=test_name, test_file=test_file, message=message))

        return failures

    def parse_json(self, data: Dict) -> List[Failure]:
        """
        Parse pytest JSON output.

        Args:
            data: Parsed JSON data from pytest --json

        Returns:
            List of Failure objects
        """
        failures = []

        tests = data.get("tests", [])
        for test in tests:
            if test.get("outcome") == "failed":
                # Extract test information
                nodeid = test.get("nodeid", "")
                node_match = self.TEST_NODE.match(nodeid)

                if node_match:
                    test_file = node_match.group(1)
                    test_name = node_match.group(2)
                else:
                    test_file = "unknown"
                    test_name = nodeid

                # Extract failure message
                call = test.get("call", {})
                message = call.get("longrepr", "Test failed")

                # Extract duration
                duration_s = test.get("duration", 0)
                duration_ms = duration_s * 1000

                # Extract location if available
                location = None
                if "crash" in call:
                    crash = call["crash"]
                    location = FailureLocation(
                        file=crash.get("path", test_file),
                        line=crash.get("lineno", 0),
                    )

                failures.append(
                    Failure(
                        test_name=test_name,
                        test_file=test_file,
                        message=message if isinstance(message, str) else str(message),
                        location=location,
                        duration_ms=duration_ms,
                    )
                )

        return failures


class UnittestParser:
    """Parser for unittest output."""

    # Patterns for parsing unittest output
    FAILURE_HEADER = re.compile(r"^(FAIL|ERROR):\s+(\S+)\s+\((\S+)\)", re.MULTILINE)
    TRACEBACK_FILE = re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\S+)')
    ERROR_TYPE = re.compile(r"^(\w+(?:Error|Exception)):\s*(.*)$", re.MULTILINE)

    def parse(self, output: str) -> List[Failure]:
        """
        Parse unittest text output to extract failures.

        Args:
            output: Raw unittest output text

        Returns:
            List of Failure objects
        """
        failures = []

        # Find all failure/error blocks
        matches = list(self.FAILURE_HEADER.finditer(output))

        for i, match in enumerate(matches):
            # match.group(1) is FAIL or ERROR
            test_name = match.group(2)
            test_class = match.group(3)

            # Extract content until next failure or end
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                # Find the Ran X tests line (end of this failure block)
                ran_match = re.search(r"^Ran\s+\d+\s+test", output[start_pos:], re.MULTILINE)
                end_pos = start_pos + ran_match.start() if ran_match else len(output)

            content = output[start_pos:end_pos]

            failure = self._parse_failure_block(test_name, test_class, content)
            if failure:
                failures.append(failure)

        return failures

    def _parse_failure_block(
        self, test_name: str, test_class: str, content: str
    ) -> Optional[Failure]:
        """Parse a single failure block."""
        # Extract stack trace
        stack_trace = self._parse_traceback(content)

        # Extract test file and line from stack trace
        test_file = "unknown"
        location = None

        if stack_trace:
            # Use the last frame (where the assertion happened)
            last_frame = stack_trace[-1]
            test_file = last_frame.file
            location = FailureLocation(
                file=last_frame.file, line=last_frame.line, function=last_frame.function
            )

        # If no stack trace, try to extract from first File line
        if not location:
            file_match = self.TRACEBACK_FILE.search(content)
            if file_match:
                test_file = file_match.group(1)
                location = FailureLocation(
                    file=file_match.group(1),
                    line=int(file_match.group(2)),
                    function=file_match.group(3),
                )

        # Extract error type and message
        failure_type, message = self._extract_error_info(content)

        return Failure(
            test_name=test_name,
            test_file=test_file,
            message=message or "Test failed",
            location=location,
            failure_type=failure_type,
            stack_trace=stack_trace,
        )

    def _parse_traceback(self, content: str) -> Optional[List[StackFrame]]:
        """Parse traceback from content."""
        # Only parse if there's a Traceback keyword
        if "Traceback" not in content:
            return None

        frames = []

        # Find all file/line references
        for match in self.TRACEBACK_FILE.finditer(content):
            file_path = match.group(1)
            line_num = int(match.group(2))
            func_name = match.group(3)

            # Try to find the code snippet (next line after File line)
            code_snippet = None
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if match.group(0) in line and i + 1 < len(lines):
                    code_snippet = lines[i + 1].strip()
                    break

            frames.append(
                StackFrame(
                    file=file_path,
                    line=line_num,
                    function=func_name,
                    code=code_snippet,
                )
            )

        return frames if frames else None

    def _extract_error_info(self, content: str) -> Tuple:
        """Extract error type and message."""
        # Look for error type pattern (e.g., "AssertionError: message")
        match = self.ERROR_TYPE.search(content)
        if match:
            error_type = match.group(1)
            message_part = match.group(2).strip()
            # Get the full error line as the message
            full_message = match.group(0)
            return error_type, message_part if message_part else full_message

        # Fallback: try to get last non-empty line which might be the error
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if lines:
            # Check if last line looks like an error
            for line in reversed(lines):
                if line and not line.startswith("-"):
                    return None, line

        return None, content.strip()


class GoogleTestParser:
    """Parser for Google Test output."""

    # Patterns for parsing Google Test output
    FAILURE_LINE = re.compile(r"^\[  FAILED  \]\s+(\S+)", re.MULTILINE)
    FILE_LINE = re.compile(r"^([^:]+):(\d+):\s+Failure", re.MULTILINE)
    TEST_RUN = re.compile(r"^\[\s+RUN\s+\]\s+(\S+)", re.MULTILINE)

    def parse(self, output: str) -> List[Failure]:
        """
        Parse Google Test text output to extract failures.

        Args:
            output: Raw Google Test output text

        Returns:
            List of Failure objects
        """
        failures = []
        seen_tests = set()  # Track seen tests to avoid duplicates

        # Find all failed tests
        failed_tests = [m.group(1) for m in self.FAILURE_LINE.finditer(output)]

        # Match failures with their locations
        for test_name in failed_tests:
            # Skip if we've already processed this test
            if test_name in seen_tests:
                continue
            seen_tests.add(test_name)

            # Find the test run section
            pattern = (
                rf"\[\s+RUN\s+\]\s+{re.escape(test_name)}"
                r"(.+?)(?=\[\s+(?:RUN|FAILED)\s+\]|\[==========\]|$)"
            )
            test_run_match = re.search(pattern, output, re.DOTALL)

            if test_run_match:
                test_content = test_run_match.group(1)

                # Find failure location in this section
                file_line_match = self.FILE_LINE.search(test_content)
                location = None
                test_file = "unknown"

                if file_line_match:
                    # Strip all whitespace including newlines from file path
                    raw_file = file_line_match.group(1)
                    test_file = raw_file.strip().lstrip("\n").strip()
                    line_num = int(file_line_match.group(2))
                    location = FailureLocation(file=test_file, line=line_num)

                # Extract message (text between failure marker and end)
                message_start = file_line_match.end() if file_line_match else 0
                message_content = test_content[message_start:].strip()

                # Clean up message (remove test result lines)
                message_lines = []
                for line in message_content.split("\n"):
                    if not line.startswith("[") and line.strip():
                        message_lines.append(line)
                message = "\n".join(message_lines).strip() or "Test failed"

                failures.append(
                    Failure(
                        test_name=test_name,
                        test_file=test_file,
                        message=message,
                        location=location,
                    )
                )

        return failures

    def parse_xml(self, xml_str: str) -> List[Failure]:
        """
        Parse Google Test XML output.

        Args:
            xml_str: XML string from Google Test

        Returns:
            List of Failure objects
        """
        failures = []

        try:
            root = ET.fromstring(xml_str)

            # Find all testcase elements with failures
            for testsuite in root.findall(".//testsuite"):
                suite_name = testsuite.get("name", "")

                for testcase in testsuite.findall("testcase"):
                    test_name_attr = testcase.get("name", "")
                    test_name = f"{suite_name}.{test_name_attr}"
                    duration_s = float(testcase.get("time", 0))
                    duration_ms = duration_s * 1000

                    # Check for failure
                    failure_elem = testcase.find("failure")
                    if failure_elem is not None:
                        message = failure_elem.get("message", "")
                        failure_text = failure_elem.text or ""

                        # Try to extract file and line from failure text
                        location = None
                        file_match = self.FILE_LINE.search(failure_text)
                        if file_match:
                            location = FailureLocation(
                                file=file_match.group(1), line=int(file_match.group(2))
                            )

                        failures.append(
                            Failure(
                                test_name=test_name,
                                test_file=location.file if location else "unknown",
                                message=message or failure_text,
                                location=location,
                                duration_ms=duration_ms,
                            )
                        )

        except ET.ParseError:
            pass  # Return empty list on parse error

        return failures

    def parse_json(self, data: Dict) -> List[Failure]:
        """
        Parse Google Test JSON output.

        Args:
            data: Parsed JSON data from Google Test

        Returns:
            List of Failure objects
        """
        failures = []

        testsuites = data.get("testsuites", [])
        for testsuite in testsuites:
            suite_name = testsuite.get("name", "")

            for testcase in testsuite.get("testsuite", []):
                test_name_attr = testcase.get("name", "")
                test_name = f"{suite_name}.{test_name_attr}"

                # Check for failures
                test_failures = testcase.get("failures", [])
                if test_failures:
                    duration_str = testcase.get("time", "0s")
                    duration_s = float(duration_str.rstrip("s"))
                    duration_ms = duration_s * 1000

                    for failure_info in test_failures:
                        message = failure_info.get("failure", "Test failed")

                        failures.append(
                            Failure(
                                test_name=test_name,
                                test_file="unknown",
                                message=message,
                                duration_ms=duration_ms,
                            )
                        )

        return failures


class FailureParser:
    """
    Main failure parser that auto-detects test framework.

    Supports:
    - pytest
    - unittest
    - Google Test
    """

    def __init__(self):
        """Initialize failure parser."""
        self._parsers = {
            "pytest": PytestParser(),
            "unittest": UnittestParser(),
            "gtest": GoogleTestParser(),
        }

    def parse(self, output: str, format: Optional[str] = None) -> List[Failure]:
        """
        Parse test output to extract failures.

        Auto-detects test framework if format not specified.

        Args:
            output: Raw test output text
            format: Optional explicit format (pytest, unittest, gtest)

        Returns:
            List of Failure objects
        """
        if not output:
            return []

        # Use explicit format if provided
        if format:
            parser = self._get_parser(format)
            return parser.parse(output)

        # Auto-detect format
        detected_format = self._detect_format(output)
        if detected_format:
            parser = self._get_parser(detected_format)
            return parser.parse(output)

        # Unknown format
        return []

    def parse_json(self, data: Dict, format: str) -> List[Failure]:
        """
        Parse JSON test output.

        Args:
            data: Parsed JSON data
            format: Test framework format (pytest, gtest)

        Returns:
            List of Failure objects
        """
        parser = self._get_parser(format)
        if hasattr(parser, "parse_json"):
            return parser.parse_json(data)
        return []

    def _get_parser(self, format: str):
        """Get parser for specified format."""
        return self._parsers.get(format)

    def _detect_format(self, output: str) -> Optional[str]:
        """
        Auto-detect test framework from output.

        Args:
            output: Raw test output

        Returns:
            Detected format or None
        """
        # Check for pytest markers
        if "test session starts" in output or "pytest" in output.lower():
            return "pytest"

        # Check for unittest markers
        if re.search(r"^(FAIL|ERROR):\s+\w+\s+\(", output, re.MULTILINE):
            return "unittest"

        # Check for Google Test markers
        if "[==========]" in output or "[  FAILED  ]" in output:
            return "gtest"

        return None
