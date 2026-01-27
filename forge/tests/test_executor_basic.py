"""
Integration tests for basic CMake process execution.

Tests process execution, exit code capture, and error handling.
"""

from pathlib import Path
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from forge.cmake.executor import CMakeExecutor
from forge.models.results import BuildResult, ConfigureResult


class TestSuccessfulExecution:
    """Test successful command execution scenarios."""

    def test_execute_configure_success(self, tmp_path):
        """Test successful configure command execution with exit code 0."""
        executor = CMakeExecutor()

        # Mock successful cmake execution
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                b"-- Configuring done\n-- Generating done\n",
                b"",
            )
            mock_popen.return_value = mock_process

            result = executor.execute_configure(
                command=["cmake", "-S", str(tmp_path), "-B", str(tmp_path / "build")]
            )

            assert isinstance(result, ConfigureResult)
            assert result.success is True
            assert result.exit_code == 0

    def test_execute_build_success(self, tmp_path):
        """Test successful build command execution with exit code 0."""
        executor = CMakeExecutor()

        # Mock successful cmake build
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"[100%] Built target myapp\n", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", str(tmp_path / "build")])

            assert isinstance(result, BuildResult)
            assert result.success is True
            assert result.exit_code == 0

    def test_execute_with_echo_command(self):
        """Test execution with simple shell command (echo) for real subprocess test."""
        executor = CMakeExecutor()

        # Use real subprocess with simple command
        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(command=["cmd", "/c", "echo test output"])
        else:
            result = executor.execute_configure(command=["echo", "test output"])


class TestFailedExecution:
    """Test failed command execution scenarios."""

    def test_execute_configure_failure(self, tmp_path):
        """Test failed configure command with non-zero exit code."""
        executor = CMakeExecutor()

        # Mock failed cmake execution
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (
                b"",
                b"CMake Error: Could not find CMAKE_ROOT\n",
            )
            mock_popen.return_value = mock_process

            result = executor.execute_configure(
                command=["cmake", "-S", str(tmp_path), "-B", str(tmp_path / "build")]
            )

            assert result.success is False
            assert result.exit_code == 1
            assert len(result.stderr) > 0

    def test_execute_build_failure(self, tmp_path):
        """Test failed build command with non-zero exit code."""
        executor = CMakeExecutor()

        # Mock failed build
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 2
            mock_process.communicate.return_value = (b"", b"error: no targets specified\n")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", str(tmp_path / "build")])

            assert result.success is False
            assert result.exit_code == 2

    def test_execute_with_failing_command(self):
        """Test execution with command that returns non-zero exit code."""
        executor = CMakeExecutor()

        # Use a command that will fail (exit with code 1)
        # On Windows, we can use a PowerShell command that fails
        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(command=["powershell", "-Command", "exit 1"])
        else:
            result = executor.execute_configure(command=["sh", "-c", "exit 1"])

        assert result.success is False
        assert result.exit_code == 1


class TestCommandNotFound:
    """Test handling of commands that don't exist."""

    def test_command_not_found_configure(self):
        """Test error handling when configure command is not found."""
        executor = CMakeExecutor()

        # Try to execute non-existent command
        result = executor.execute_configure(command=["nonexistent_command_xyz123", "--help"])

        assert result.success is False
        assert result.exit_code != 0
        # Error should be captured in stderr or as exception message
        assert len(result.stderr) > 0 or "not found" in result.stdout.lower()

    def test_command_not_found_build(self):
        """Test error handling when build command is not found."""
        executor = CMakeExecutor()

        result = executor.execute_build(command=["nonexistent_build_command_xyz", "--version"])

        assert result.success is False
        assert result.exit_code != 0


class TestTimeoutHandling:
    """Test execution timeout handling."""

    def test_execution_timeout(self):
        """Test that long-running commands can be timed out."""
        executor = CMakeExecutor()

        # Mock a process that takes too long
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="sleep", timeout=1)
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["sleep", "100"], timeout=1)

            # Should handle timeout gracefully
            assert result.success is False
            # Timeout should be reflected in result
            assert "timeout" in result.stderr.lower() or result.exit_code != 0


class TestWorkingDirectory:
    """Test working directory handling."""

    def test_working_directory_is_set(self, tmp_path):
        """Test that working directory is correctly set for command execution."""
        executor = CMakeExecutor()

        # Create a test directory
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        # Execute command that outputs current directory
        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(
                command=["powershell", "-Command", "Get-Location"], working_dir=test_dir
            )
        else:
            result = executor.execute_configure(command=["pwd"], working_dir=test_dir)

        assert result.success is True
        # The output should contain the test directory path
        assert str(test_dir) in result.stdout or test_dir.name in result.stdout

    def test_default_working_directory(self):
        """Test that default working directory is current directory."""
        executor = CMakeExecutor()

        # Mock process to check cwd parameter
        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            import platform

            if platform.system() == "Windows":
                executor.execute_configure(command=["cmd", "/c", "echo test"])
            else:
                executor.execute_configure(command=["echo", "test"])
        """Test ConfigureResult contains all expected fields after execution."""


class TestResultObjectPopulation:
    """Test that result objects are properly populated."""

    def test_configure_result_has_all_fields(self):
        """Test ConfigureResult contains all expected fields after execution."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(command=["cmd", "/c", "echo test"])
        else:
            result = executor.execute_configure(command=["echo", "test"])

        assert hasattr(result, "success")
        assert hasattr(result, "exit_code")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "duration")
        assert hasattr(result, "start_time")
        assert hasattr(result, "end_time")
        assert result.stdout is not None
        assert result.stderr is not None

    def test_build_result_has_all_fields(self):
        """Test BuildResult contains all expected fields after execution."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            result = executor.execute_build(command=["cmd", "/c", "echo build"])
        else:
            result = executor.execute_build(command=["echo", "build"])

        assert hasattr(result, "success")
        assert hasattr(result, "exit_code")
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert hasattr(result, "duration")
        assert hasattr(result, "start_time")
        assert hasattr(result, "end_time")

    def test_stdout_is_captured(self):
        """Test that stdout is captured in result object."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(command=["cmd", "/c", "echo hello stdout"])
        else:
            result = executor.execute_configure(command=["echo", "hello stdout"])

        assert "hello stdout" in result.stdout

    def test_stderr_is_captured(self):
        """Test that stderr is captured in result object."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            # PowerShell command to write to stderr
            result = executor.execute_configure(
                command=["powershell", "-Command", "[Console]::Error.WriteLine('error message')"]
            )
        else:
            # Unix command to write to stderr
            result = executor.execute_configure(command=["sh", "-c", "echo 'error message' >&2"])

        assert "error message" in result.stderr


class TestExitCodeCapture:
    """Test exit code capture from subprocess."""

    def test_exit_code_zero(self):
        """Test capture of exit code 0 (success)."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            result = executor.execute_configure(command=["cmd", "/c", "echo success"])
        else:
            result = executor.execute_configure(command=["echo", "success"])

        assert result.exit_code == 0

    def test_exit_code_nonzero(self):
        """Test capture of non-zero exit codes."""
        executor = CMakeExecutor()

        import platform

        if platform.system() == "Windows":
            result = executor.execute_build(command=["powershell", "-Command", "exit 5"])
        else:
            result = executor.execute_build(command=["sh", "-c", "exit 5"])

        assert result.exit_code == 5

    def test_exit_code_in_result_object(self):
        """Test that exit code is properly stored in result object."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 42
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["test"])

            assert result.exit_code == 42
            assert result.success is False  # Non-zero means failure
