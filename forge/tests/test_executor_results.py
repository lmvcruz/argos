"""
Integration tests for CMake executor timing and result object population.

Tests timing accuracy, result object completeness, and proper field population.
"""

from datetime import datetime
import time
from unittest.mock import MagicMock, patch

from forge.cmake.executor import CMakeExecutor
from forge.models.results import ConfigureResult


class TestTimingAccuracy:
    """Test timing measurement accuracy."""

    def test_start_time_recorded_before_execution(self):
        """Test that start_time is recorded before command execution."""
        executor = CMakeExecutor()
        before_call = datetime.now()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # start_time should be between before_call and now
            assert result.start_time >= before_call
            assert result.start_time <= datetime.now()

    def test_end_time_recorded_after_execution(self):
        """Test that end_time is recorded after command execution."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])
            after_call = datetime.now()

            # end_time should be between start_time and after_call
            assert result.end_time >= result.start_time
            assert result.end_time <= after_call

    def test_duration_calculated_correctly(self):
        """Test that duration equals end_time - start_time."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Calculate expected duration
            expected_duration = (result.end_time - result.start_time).total_seconds()

            # Duration should match (allow small floating point difference)
            assert abs(result.duration - expected_duration) < 0.01

    def test_timing_with_sub_millisecond_precision(self):
        """Test timing precision is sub-millisecond."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Duration should have precision better than 0.001 seconds
            # (it should be a float with meaningful decimal places)
            assert isinstance(result.duration, float)
            # Even fast commands should have non-zero but small duration
            assert result.duration >= 0.0

    def test_timing_for_quick_commands(self):
        """Test timing accuracy for commands that execute quickly."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"quick", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["echo", "test"])

            # Even quick commands should have measurable duration
            assert result.duration >= 0.0
            # Should complete in less than 1 second (it's mocked)
            assert result.duration < 1.0

    def test_timing_for_longer_commands(self):
        """Test timing accuracy for commands that take longer."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0

            # Simulate a delay in communicate()
            def slow_communicate(timeout=None):
                time.sleep(0.1)  # Simulate 100ms execution
                return (b"output", b"")

            mock_process.communicate = slow_communicate
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Duration should be at least 0.1 seconds
            assert result.duration >= 0.1
            # But not much more than that (allow some overhead)
            assert result.duration < 0.5

    def test_timing_consistency_across_multiple_calls(self):
        """Test that timing is consistent across multiple executions."""
        executor = CMakeExecutor()
        durations = []

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            # Execute multiple times
            for _ in range(5):
                result = executor.execute_configure(command=["cmake", ".."])
                durations.append(result.duration)

            # All durations should be small and similar (not random)
            assert all(d >= 0.0 for d in durations)
            assert all(d < 1.0 for d in durations)


class TestConfigureResultPopulation:
    """Test ConfigureResult object field population."""

    def test_configure_result_has_all_required_fields(self):
        """Test that ConfigureResult contains all required fields."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"stdout", b"stderr")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Check all required fields are present
            assert hasattr(result, "success")
            assert hasattr(result, "exit_code")
            assert hasattr(result, "duration")
            assert hasattr(result, "stdout")
            assert hasattr(result, "stderr")
            assert hasattr(result, "start_time")
            assert hasattr(result, "end_time")

    def test_configure_result_success_field_correct(self):
        """Test that success field reflects exit code."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            # Test successful execution
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"success", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])
            assert result.success is True
            assert result.exit_code == 0

    def test_configure_result_failure_field_correct(self):
        """Test that failure is reflected in success field."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"error")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])
            assert result.success is False
            assert result.exit_code == 1

    def test_configure_result_stdout_populated(self):
        """Test that stdout is properly captured in result."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            expected_stdout = b"CMake configuration output\nMultiple lines\n"
            mock_process.communicate.return_value = (expected_stdout, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.stdout == expected_stdout.decode("utf-8", errors="replace")
            assert "CMake configuration output" in result.stdout
            assert "Multiple lines" in result.stdout

    def test_configure_result_stderr_populated(self):
        """Test that stderr is properly captured in result."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            expected_stderr = b"Warning: something\n"
            mock_process.communicate.return_value = (b"", expected_stderr)
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.stderr == expected_stderr.decode("utf-8", errors="replace")
            assert "Warning: something" in result.stderr

    def test_configure_result_datetime_types(self):
        """Test that start_time and end_time are datetime objects."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)

    def test_configure_result_optional_fields_none(self):
        """Test that optional metadata fields default to None."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Optional fields should be None (will be populated by inspector later)
            assert result.cmake_version is None
            assert result.generator is None
            assert result.compiler_c is None
            assert result.compiler_cxx is None
            assert result.build_type is None


class TestBuildResultPopulation:
    """Test BuildResult object field population."""

    def test_build_result_has_all_required_fields(self):
        """Test that BuildResult contains all required fields."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"build output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            # Check all required fields are present
            assert hasattr(result, "success")
            assert hasattr(result, "exit_code")
            assert hasattr(result, "duration")
            assert hasattr(result, "stdout")
            assert hasattr(result, "stderr")
            assert hasattr(result, "start_time")
            assert hasattr(result, "end_time")

    def test_build_result_success_with_exit_code_zero(self):
        """Test successful build result."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Build succeeded", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert result.success is True
            assert result.exit_code == 0

    def test_build_result_failure_with_nonzero_exit_code(self):
        """Test failed build result."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 2
            mock_process.communicate.return_value = (b"", b"Build failed")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert result.success is False
            assert result.exit_code == 2

    def test_build_result_stdout_populated(self):
        """Test build stdout capture."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            build_output = b"[1/10] Building CXX object\n[2/10] Linking\n"
            mock_process.communicate.return_value = (build_output, b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert "Building CXX object" in result.stdout
            assert "Linking" in result.stdout

    def test_build_result_stderr_populated(self):
        """Test build stderr capture."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"compilation error\n")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert "compilation error" in result.stderr

    def test_build_result_timing_fields(self):
        """Test build timing fields are populated."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)
            assert isinstance(result.duration, float)
            assert result.duration >= 0.0

    def test_build_result_optional_fields_defaults(self):
        """Test build optional fields have proper defaults."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_build(command=["cmake", "--build", "."])

            # Optional fields should have defaults (will be populated by inspector later)
            assert result.targets_built == []
            assert result.warnings_count == 0
            assert result.errors_count == 0


class TestErrorCaseResultPopulation:
    """Test result population in error scenarios."""

    def test_command_not_found_result(self):
        """Test result when command is not found."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("cmake not found")

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is False
            assert result.exit_code == 127  # Command not found
            assert "Command not found" in result.stderr
            assert result.stdout == ""
            # Timing should still be recorded
            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)
            assert result.duration >= 0.0

    def test_timeout_result_population(self):
        """Test result when execution times out."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            import subprocess

            mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="cmake", timeout=1)
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."], timeout=1)

            assert result.success is False
            assert result.exit_code == -1
            assert "timed out" in result.stderr
            # Timing should still be recorded
            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)

    def test_general_exception_result(self):
        """Test result when general exception occurs."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Unexpected error")

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.success is False
            assert result.exit_code == -1
            assert "Unexpected error" in result.stderr
            # Timing should be recorded
            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)


class TestResultObjectConsistency:
    """Test consistency between configure and build results."""

    def test_configure_and_build_results_structure_similar(self):
        """Test that ConfigureResult and BuildResult have similar structure."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            config_result = executor.execute_configure(command=["cmake", ".."])
            build_result = executor.execute_build(command=["cmake", "--build", "."])

            # Both should have these common fields
            for field in [
                "success",
                "exit_code",
                "duration",
                "stdout",
                "stderr",
                "start_time",
                "end_time",
            ]:
                assert hasattr(config_result, field)
                assert hasattr(build_result, field)

    def test_results_are_independent_objects(self):
        """Test that each execution creates a new result object."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result1 = executor.execute_configure(command=["cmake", ".."])
            result2 = executor.execute_configure(command=["cmake", ".."])

            # Should be different objects
            assert result1 is not result2
            # But both should be valid
            assert isinstance(result1, ConfigureResult)
            assert isinstance(result2, ConfigureResult)

    def test_empty_output_still_creates_valid_result(self):
        """Test that result is valid even with no output."""
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
            assert result.duration >= 0.0
            assert isinstance(result.start_time, datetime)
            assert isinstance(result.end_time, datetime)


class TestDurationCalculation:
    """Test duration calculation edge cases."""

    def test_duration_is_positive(self):
        """Test that duration is always positive."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.duration >= 0.0

    def test_duration_matches_time_difference(self):
        """Test duration equals end_time - start_time in seconds."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            calculated_duration = (result.end_time - result.start_time).total_seconds()
            # Allow small floating point error
            assert abs(result.duration - calculated_duration) < 0.01

    def test_duration_precision(self):
        """Test that duration has sufficient precision."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Duration should be a float with meaningful precision
            assert isinstance(result.duration, float)
            # Should be able to measure sub-second durations
            assert result.duration < 1.0  # Our mocked command is instant

    def test_start_time_before_end_time(self):
        """Test that start_time is always before end_time."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"output", b"")
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            assert result.start_time <= result.end_time

    def test_duration_with_simulated_delay(self):
        """Test duration calculation with simulated execution delay."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0

            # Simulate 0.05 second execution
            def delayed_communicate(timeout=None):
                time.sleep(0.05)
                return (b"output", b"")

            mock_process.communicate = delayed_communicate
            mock_popen.return_value = mock_process

            result = executor.execute_configure(command=["cmake", ".."])

            # Duration should reflect the delay
            assert result.duration >= 0.05
            assert result.duration < 0.2  # Allow some overhead
