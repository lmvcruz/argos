"""
Integration tests for CMake executor output streaming and capture.

Tests output capture, real-time streaming, and handling of various output scenarios.
"""

import io
from unittest.mock import MagicMock, patch

from forge.cmake.executor import CMakeExecutor


class TestStdoutCapture:
    """Test stdout capture functionality."""

    def test_stdout_captured_completely(self):
        """Test that all stdout is captured without loss."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            stdout_data = b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
            mock_process.communicate.return_value = (stdout_data, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "Line 1" in result.stdout
            assert "Line 2" in result.stdout
            assert "Line 3" in result.stdout
            assert "Line 4" in result.stdout
            assert "Line 5" in result.stdout

    def test_large_stdout_handling(self):
        """Test handling of large stdout (memory efficiency)."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Generate large output (10,000 lines)
            large_output = "\n".join([f"Line {i}" for i in range(10000)])
            mock_process.communicate.return_value = (large_output.encode(), b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "Line 0" in result.stdout
            assert "Line 9999" in result.stdout
            # Verify line count
            assert result.stdout.count("\n") >= 9999

    def test_stdout_with_unicode_characters(self):
        """Test stdout capture with Unicode and special characters."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            unicode_output = "Hello 世界 🎉\nCafé ñoño\n日本語\n"
            mock_process.communicate.return_value = (unicode_output.encode("utf-8"), b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "世界" in result.stdout
            assert "🎉" in result.stdout
            assert "Café" in result.stdout
            assert "日本語" in result.stdout


class TestStderrCapture:
    """Test stderr capture functionality."""

    def test_stderr_captured_completely(self):
        """Test that all stderr is captured without loss."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            stderr_data = b"Error 1\nError 2\nError 3\n"
            mock_process.communicate.return_value = (b"", stderr_data)
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is False
            assert "Error 1" in result.stderr
            assert "Error 2" in result.stderr
            assert "Error 3" in result.stderr

    def test_stderr_with_warnings(self):
        """Test stderr capture with warning messages."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            stderr_data = b"Warning: unused variable\nWarning: deprecated function\n"
            mock_process.communicate.return_value = (b"Success", stderr_data)
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "unused variable" in result.stderr
            assert "deprecated function" in result.stderr


class TestMixedOutput:
    """Test handling of mixed stdout and stderr."""

    def test_mixed_stdout_stderr(self):
        """Test capture of both stdout and stderr in same execution."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                b"Standard output line\n",
                b"Standard error line\n",
            )
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "Standard output line" in result.stdout
            assert "Standard error line" in result.stderr
            # Verify they're in separate fields
            assert "Standard error line" not in result.stdout
            assert "Standard output line" not in result.stderr

    def test_empty_stdout_with_stderr(self):
        """Test when stdout is empty but stderr has content."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Error occurred\n")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is False
            assert result.stdout == ""
            assert "Error occurred" in result.stderr

    def test_empty_stderr_with_stdout(self):
        """Test when stderr is empty but stdout has content."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Success message\n", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "Success message" in result.stdout
            assert result.stderr == ""


class TestSpecialCharacters:
    """Test handling of special characters and encodings."""

    def test_ansi_color_codes_in_output(self):
        """Test handling of ANSI color codes in output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # ANSI color codes: \033[31m = red, \033[0m = reset
            colored_output = b"\033[31mRed text\033[0m\nNormal text\n"
            mock_process.communicate.return_value = (colored_output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            # ANSI codes should be preserved in output
            assert "Red text" in result.stdout

    def test_carriage_return_handling(self):
        """Test handling of carriage returns (progress indicators)."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Progress indicator with carriage return
            output = b"Progress: 10%\rProgress: 50%\rProgress: 100%\n"
            mock_process.communicate.return_value = (output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            # Output should contain progress indicators
            assert "Progress" in result.stdout

    def test_null_bytes_in_output(self):
        """Test handling of null bytes in output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Output with null bytes
            output = b"Before\x00After\n"
            mock_process.communicate.return_value = (output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            # Null bytes should be handled gracefully
            assert len(result.stdout) > 0

    def test_invalid_utf8_sequences(self):
        """Test handling of invalid UTF-8 sequences."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Invalid UTF-8 sequence
            output = b"Valid text\xff\xfeInvalid\n"
            mock_process.communicate.return_value = (output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            # Should use replacement character for invalid sequences
            assert "Valid text" in result.stdout
            # The decode with errors='replace' should handle this


class TestOutputBuffering:
    """Test output buffering and line handling."""

    def test_output_with_no_trailing_newline(self):
        """Test output that doesn't end with newline."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"No trailing newline", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "No trailing newline" in result.stdout

    def test_output_with_multiple_newlines(self):
        """Test output with multiple consecutive newlines."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            output = b"Line 1\n\n\nLine 2\n"
            mock_process.communicate.return_value = (output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert "Line 1" in result.stdout
            assert "Line 2" in result.stdout
            # Multiple newlines should be preserved
            assert "\n\n" in result.stdout

    def test_very_long_lines(self):
        """Test handling of very long lines (no line breaks)."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Generate a very long line (10,000 characters)
            long_line = "x" * 10000 + "\n"
            mock_process.communicate.return_value = (long_line.encode(), b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert len(result.stdout) >= 10000


class TestBuildOutput:
    """Test output capture for build commands."""

    def test_build_stdout_capture(self):
        """Test stdout capture for build command."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            build_output = b"[1/10] Building CXX object\n[2/10] Linking target\n"
            mock_process.communicate.return_value = (build_output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert result.success is True
            assert "Building CXX object" in result.stdout
            assert "Linking target" in result.stdout

    def test_build_with_compilation_errors(self):
        """Test build output with compilation errors in stderr."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            stderr = b"error: expected ';' before '}' token\n"
            mock_process.communicate.return_value = (b"", stderr)
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert result.success is False
            assert "expected ';'" in result.stderr


class TestEmptyOutput:
    """Test handling of empty output scenarios."""

    def test_no_output_success(self):
        """Test successful command with no output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is True
            assert result.stdout == ""
            assert result.stderr == ""

    def test_no_output_failure(self):
        """Test failed command with no output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is False
            assert result.stdout == ""
            assert result.stderr == ""


class TestRealTimeStreaming:
    """Test real-time output streaming to console."""

    def test_stdout_streams_to_console(self):
        """Test that stdout is streamed to console in real-time."""
        executor = CMakeExecutor()

        with (
            patch("subprocess.Popen") as mock_popen,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Build output\n", b"")
            mock_popen.return_value = mock_process

            # Execute with streaming enabled (default)
            result = executor.execute_configure(command=["cmake", ".."], stream_output=True)

            # Verify output was captured
            assert "Build output" in result.stdout
            # Verify output was also printed to console
            console_output = mock_stdout.getvalue()
            assert "Build output" in console_output

    def test_stderr_streams_to_console(self):
        """Test that stderr is streamed to console in real-time."""
        executor = CMakeExecutor()

        with (
            patch("subprocess.Popen") as mock_popen,
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"Warning message\n")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."], stream_output=True)

            # Verify stderr was captured
            assert "Warning message" in result.stderr
            # Verify stderr was also printed to console
            console_output = mock_stderr.getvalue()
            assert "Warning message" in console_output

    def test_streaming_can_be_disabled(self):
        """Test that output streaming can be disabled for performance."""
        executor = CMakeExecutor()

        with (
            patch("subprocess.Popen") as mock_popen,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Build output\n", b"")
            mock_popen.return_value = mock_process

            # Execute with streaming disabled
            result = executor.execute_configure(command=["cmake", ".."], stream_output=False)

            # Verify output was captured
            assert "Build output" in result.stdout
            # Verify output was NOT printed to console
            console_output = mock_stdout.getvalue()
            assert "Build output" not in console_output

    def test_interleaved_output_streaming(self):
        """Test streaming of interleaved stdout and stderr."""
        executor = CMakeExecutor()

        with (
            patch("subprocess.Popen") as mock_popen,
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"stdout line\n", b"stderr line\n")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."], stream_output=True)

            # Verify both were captured
            assert "stdout line" in result.stdout
            assert "stderr line" in result.stderr
            # Verify both were printed to respective streams
            assert "stdout line" in mock_stdout.getvalue()
            assert "stderr line" in mock_stderr.getvalue()


class TestStreamingPerformance:
    """Test streaming with performance considerations."""

    def test_streaming_with_large_output(self):
        """Test streaming doesn't cause memory issues with large output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen, patch("sys.stdout", new_callable=io.StringIO):
            mock_process = MagicMock()
            mock_process.returncode = 0
            # Generate large output
            large_output = "\n".join([f"Line {i}" for i in range(10000)])
            mock_process.communicate.return_value = (large_output.encode(), b"")
            mock_popen.return_value = mock_process

            # Should not raise memory error
            result = executor.execute_configure(command=["cmake", ".."], stream_output=True)

            assert result.success is True
            assert len(result.stdout) > 0

    def test_streaming_performance_mode(self):
        """Test that disabling streaming improves performance."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output\n", b"")
            mock_popen.return_value = mock_process

            # With streaming disabled, should skip streaming logic
            result = executor.execute_configure(command=["cmake", ".."], stream_output=False)

            assert result.success is True
            # Verify communicate was called (no streaming)
            mock_process.communicate.assert_called_once()

    def test_streaming_with_stderr_only(self):
        """Test streaming when only stderr has content."""
        executor = CMakeExecutor()

        with (
            patch("subprocess.Popen") as mock_popen,
            patch("sys.stderr", new_callable=io.StringIO) as mock_stderr,
        ):
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"Error output\n")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."], stream_output=True)

            assert result.success is False
            assert "Error output" in result.stderr
            # Verify stderr was streamed to console
            assert "Error output" in mock_stderr.getvalue()

    def test_streaming_disabled_with_timeout(self):
        """Test that streaming disabled mode handles timeout correctly."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            # Simulate timeout
            import subprocess

            mock_process.communicate.side_effect = [
                subprocess.TimeoutExpired(cmd="cmake", timeout=1),
                (b"partial", b"error"),
            ]
            mock_popen.return_value = mock_process

            result = executor.execute_configure(
                command=["cmake", ".."], timeout=1, stream_output=False
            )

            assert result.success is False
            assert result.exit_code == -1
            assert "timed out" in result.stderr
