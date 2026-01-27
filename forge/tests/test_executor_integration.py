"""
Integration tests for CMake executor with real subprocess execution.

These tests run actual commands (using Python for cross-platform compatibility)
to verify that CMakeExecutor and result objects work correctly with real processes.
No mocking - tests actual subprocess behavior, output capture, and timing.
"""

from pathlib import Path
import sys
import tempfile

from forge.cmake.executor import CMakeExecutor


class TestRealProcessExecution:
    """Test CMakeExecutor with real subprocess execution."""

    def test_real_stdout_capture(self):
        """Test that executor captures real stdout from actual command."""
        executor = CMakeExecutor()

        # Run real Python command - no mocking
        result = executor.execute_configure(command=[sys.executable, "-c", "print('Hello World')"])

        assert result.success is True
        assert result.exit_code == 0
        assert "Hello World" in result.stdout
        assert result.stderr == ""
        # Real timing should be measured
        assert result.duration >= 0.0
        assert result.duration < 2.0  # Should be quick

    def test_real_stderr_capture(self):
        """Test that executor captures real stderr from actual command."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('Error message\\n')",
            ]
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == ""
        assert "Error message" in result.stderr

    def test_real_exit_code_success(self):
        """Test that executor captures real exit code 0."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[sys.executable, "-c", "import sys; sys.exit(0)"]
        )

        assert result.success is True
        assert result.exit_code == 0

    def test_real_exit_code_failure(self):
        """Test that executor captures real non-zero exit code."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[sys.executable, "-c", "import sys; sys.exit(42)"]
        )

        assert result.success is False
        assert result.exit_code == 42

    def test_real_command_not_found(self):
        """Test that executor handles real command-not-found error."""
        executor = CMakeExecutor()

        result = executor.execute_configure(command=["nonexistent_command_12345"])

        assert result.success is False
        assert result.exit_code == 127
        assert "Command not found" in result.stderr

    def test_real_unicode_output(self):
        """Test that executor handles real Unicode output correctly."""
        executor = CMakeExecutor()

        # Set UTF-8 encoding to handle Unicode on all platforms
        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stdout.reconfigure(encoding='utf-8'); print('Hello 世界 🎉 Café')",
            ]
        )

        assert result.success is True
        assert "世界" in result.stdout
        assert "🎉" in result.stdout
        assert "Café" in result.stdout

    def test_real_large_output(self):
        """Test that executor handles large real output without data loss."""
        executor = CMakeExecutor()

        # Generate 100KB of output
        result = executor.execute_configure(command=[sys.executable, "-c", "print('x' * 100000)"])

        assert result.success is True
        assert len(result.stdout) >= 100000
        # Verify no data loss
        assert result.stdout.count("x") >= 100000

    def test_real_multiline_output(self):
        """Test that executor preserves line structure in real output."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "print('Line 1\\nLine 2\\nLine 3')",
            ]
        )

        assert result.success is True
        assert "Line 1" in result.stdout
        assert "Line 2" in result.stdout
        assert "Line 3" in result.stdout
        # Check line structure is preserved
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 3

    def test_real_mixed_output(self):
        """Test that executor captures both stdout and stderr from real command."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; print('to stdout'); sys.stderr.write('to stderr\\n')",
            ]
        )

        assert result.success is True
        assert "to stdout" in result.stdout
        assert "to stderr" in result.stderr
        # Verify separation
        assert "to stderr" not in result.stdout
        assert "to stdout" not in result.stderr

    def test_real_empty_output(self):
        """Test that executor handles commands with no output."""
        executor = CMakeExecutor()

        result = executor.execute_configure(command=[sys.executable, "-c", "pass"])

        assert result.success is True
        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_real_working_directory(self):
        """Test that executor respects working directory with real command."""
        executor = CMakeExecutor()

        # Use temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            result = executor.execute_configure(
                command=[sys.executable, "-c", "import os; print(os.getcwd())"],
                working_dir=Path(tmpdir),
            )

            assert result.success is True
            # Output should contain the temp directory path
            assert tmpdir in result.stdout or Path(tmpdir).resolve().as_posix() in result.stdout

    def test_real_timing_accuracy(self):
        """Test that executor measures real execution time accurately."""
        executor = CMakeExecutor()

        # Command that sleeps for 0.1 seconds
        result = executor.execute_configure(
            command=[sys.executable, "-c", "import time; time.sleep(0.1)"]
        )

        assert result.success is True
        # Duration should reflect actual sleep time
        assert result.duration >= 0.1
        assert result.duration < 0.5  # Allow overhead but not too much

    def test_real_multiple_executions_independent(self):
        """Test that multiple real executions are independent."""
        executor = CMakeExecutor()

        result1 = executor.execute_configure(command=[sys.executable, "-c", "print('First')"])
        result2 = executor.execute_configure(command=[sys.executable, "-c", "print('Second')"])

        # Results should be independent
        assert result1 is not result2
        assert "First" in result1.stdout
        assert "Second" in result2.stdout
        assert "Second" not in result1.stdout
        assert "First" not in result2.stdout


class TestRealBuildExecution:
    """Test build command execution with real processes."""

    def test_real_build_stdout_capture(self):
        """Test that build execution captures real stdout."""
        executor = CMakeExecutor()

        result = executor.execute_build(command=[sys.executable, "-c", "print('Building target')"])

        assert result.success is True
        assert "Building target" in result.stdout

    def test_real_build_exit_code(self):
        """Test that build execution captures real exit codes."""
        executor = CMakeExecutor()

        result = executor.execute_build(command=[sys.executable, "-c", "import sys; sys.exit(5)"])

        assert result.success is False
        assert result.exit_code == 5

    def test_real_build_timing(self):
        """Test that build execution measures real timing."""
        executor = CMakeExecutor()

        result = executor.execute_build(
            command=[sys.executable, "-c", "import time; time.sleep(0.05)"]
        )

        assert result.success is True
        assert result.duration >= 0.05
        assert result.duration < 0.3


class TestRealStreamingBehavior:
    """Test streaming behavior with real commands."""

    def test_real_streaming_enabled(self):
        """Test that streaming works with real command (visual inspection in CI logs)."""
        executor = CMakeExecutor()

        # This will stream output in real-time (visible in test output)
        result = executor.execute_configure(
            command=[sys.executable, "-c", "print('Streamed output')"],
            stream_output=True,
        )

        assert result.success is True
        assert "Streamed output" in result.stdout

    def test_real_streaming_disabled(self):
        """Test that streaming can be disabled with real command."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[sys.executable, "-c", "print('No streaming')"],
            stream_output=False,
        )

        assert result.success is True
        assert "No streaming" in result.stdout


class TestRealTimeoutBehavior:
    """Test timeout behavior with real commands."""

    def test_real_timeout_kills_process(self):
        """Test that real timeout actually terminates the process."""
        executor = CMakeExecutor()

        # Command that sleeps longer than timeout
        result = executor.execute_configure(
            command=[sys.executable, "-c", "import time; time.sleep(10)"],
            timeout=0.5,
        )

        assert result.success is False
        assert result.exit_code == -1
        assert "timed out" in result.stderr
        # Should timeout quickly, not wait full 10 seconds
        assert result.duration < 2.0

    def test_real_timeout_not_triggered(self):
        """Test that timeout doesn't trigger when command completes quickly."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[sys.executable, "-c", "print('Quick')"], timeout=5.0
        )

        assert result.success is True
        assert "Quick" in result.stdout
        assert "timed out" not in result.stderr


class TestRealEdgeCases:
    """Test edge cases with real command execution."""

    def test_real_output_with_no_newline(self):
        """Test real output that doesn't end with newline."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stdout.write('No newline')",
            ]
        )

        assert result.success is True
        assert "No newline" in result.stdout

    def test_real_output_with_multiple_newlines(self):
        """Test real output with multiple consecutive newlines."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[sys.executable, "-c", "print('Line 1\\n\\n\\nLine 2')"]
        )

        assert result.success is True
        assert "Line 1" in result.stdout
        assert "Line 2" in result.stdout
        # Multiple newlines should be preserved (handle both Unix \n and Windows \r\n)
        assert "\n\n" in result.stdout or "\r\n\r\n" in result.stdout

    def test_real_binary_output_handling(self):
        """Test that executor handles binary-like output from real command."""
        executor = CMakeExecutor()

        # Print bytes that might cause encoding issues
        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'Binary\\x00\\xff\\xfe')",
            ]
        )

        # Should not crash, output decoded with replacement
        assert result.success is True
        assert len(result.stdout) > 0

    def test_real_very_long_line(self):
        """Test that executor handles very long lines from real output."""
        executor = CMakeExecutor()

        result = executor.execute_configure(command=[sys.executable, "-c", "print('x' * 50000)"])

        assert result.success is True
        assert len(result.stdout) >= 50000
        assert result.stdout.count("x") >= 50000

    def test_real_rapid_output(self):
        """Test that executor captures rapid output from real command."""
        executor = CMakeExecutor()

        # Print many lines rapidly
        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "for i in range(1000): print(f'Line {i}')",
            ]
        )

        assert result.success is True
        # Verify we got all lines
        assert "Line 0" in result.stdout
        assert "Line 999" in result.stdout
        line_count = result.stdout.count("Line ")
        assert line_count >= 1000

    def test_real_stderr_without_stdout(self):
        """Test real command that only writes to stderr."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('Only stderr\\n'); sys.exit(0)",
            ]
        )

        assert result.success is True
        assert result.stdout == ""
        assert "Only stderr" in result.stderr

    def test_real_exit_with_output(self):
        """Test real command that exits with code but produces output."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "print('Before exit'); import sys; sys.exit(1)",
            ]
        )

        assert result.success is False
        assert result.exit_code == 1
        assert "Before exit" in result.stdout


class TestRealCrossCompatibility:
    """Test that executor works across different platforms (tested by CI)."""

    def test_real_python_executable(self):
        """Test that we can execute Python on any platform."""
        executor = CMakeExecutor()

        result = executor.execute_configure(command=[sys.executable, "--version"])

        # Python --version writes to stdout (Python 3.4+)
        assert result.success is True
        assert "Python" in result.stdout or "Python" in result.stderr  # Some versions use stderr

    def test_real_path_handling(self):
        """Test that executor handles paths correctly on any platform."""
        executor = CMakeExecutor()

        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import os, sys; print(os.path.exists(sys.executable))",
            ]
        )

        assert result.success is True
        assert "True" in result.stdout

    def test_real_environment_inheritance(self):
        """Test that executed commands inherit environment variables."""
        executor = CMakeExecutor()

        # PYTHONIOENCODING should be inherited
        result = executor.execute_configure(
            command=[
                sys.executable,
                "-c",
                "import os; print('PATH' in os.environ)",
            ]
        )

        assert result.success is True
        assert "True" in result.stdout
