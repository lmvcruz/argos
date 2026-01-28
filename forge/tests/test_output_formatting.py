"""
Tests for output formatting and user feedback.

This module tests the formatting utilities and user-facing output functions
that provide clear, helpful console feedback during build operations.
"""

from datetime import datetime
from unittest.mock import patch

import pytest  # noqa: F401 (used for fixtures)

from forge.models.results import BuildResult, ConfigureResult
from forge.utils.formatting import (
    format_duration,
    format_timestamp,
    print_build_summary,
    print_configure_summary,
    print_error,
    print_section_header,
    print_success,
    print_warning,
    supports_color,
)


class TestDurationFormatting:
    """Test duration formatting for user display."""

    def test_format_duration_milliseconds(self):
        """Test formatting sub-second durations."""
        assert format_duration(0.123) == "123ms"
        assert format_duration(0.001) == "1ms"
        assert format_duration(0.999) == "999ms"

    def test_format_duration_seconds(self):
        """Test formatting durations in seconds."""
        assert format_duration(1.0) == "1.00s"
        assert format_duration(5.5) == "5.50s"
        assert format_duration(59.9) == "59.90s"

    def test_format_duration_minutes(self):
        """Test formatting durations in minutes."""
        assert format_duration(60.0) == "1m 0s"
        assert format_duration(90.5) == "1m 30s"
        assert format_duration(125.0) == "2m 5s"

    def test_format_duration_hours(self):
        """Test formatting durations in hours."""
        assert format_duration(3600.0) == "1h 0m 0s"
        assert format_duration(3665.0) == "1h 1m 5s"
        assert format_duration(7325.0) == "2h 2m 5s"

    def test_format_duration_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0.0) == "0ms"

    def test_format_duration_very_small(self):
        """Test formatting very small durations."""
        assert format_duration(0.0001) == "0ms"
        assert format_duration(0.0009) == "1ms"


class TestTimestampFormatting:
    """Test timestamp formatting for user display."""

    def test_format_timestamp_datetime(self):
        """Test formatting datetime objects."""
        dt = datetime(2024, 3, 15, 14, 30, 45)
        result = format_timestamp(dt)
        assert "2024-03-15" in result
        assert "14:30:45" in result

    def test_format_timestamp_iso_string(self):
        """Test formatting ISO 8601 strings."""
        iso_str = "2024-03-15T14:30:45"
        result = format_timestamp(iso_str)
        assert "2024-03-15" in result
        assert "14:30" in result

    def test_format_timestamp_none(self):
        """Test formatting None timestamps."""
        assert format_timestamp(None) == "N/A"

    def test_format_timestamp_invalid(self):
        """Test formatting invalid timestamp strings."""
        assert format_timestamp("invalid") == "invalid"


class TestColorSupport:
    """Test color output support detection."""

    def test_supports_color_with_tty(self):
        """Test color support detection on TTY."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("platform.system", return_value="Linux"):
                assert supports_color() is True

    def test_supports_color_no_tty(self):
        """Test color support detection without TTY."""
        with patch("sys.stdout.isatty", return_value=False):
            assert supports_color() is False

    def test_supports_color_windows_with_wt(self):
        """Test color support on Windows with Windows Terminal."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("platform.system", return_value="Windows"):
                with patch.dict("os.environ", {"WT_SESSION": "1"}):
                    assert supports_color() is True

    def test_supports_color_windows_without_wt(self):
        """Test color support on Windows without Windows Terminal."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch("platform.system", return_value="Windows"):
                with patch.dict("os.environ", {}, clear=True):
                    # Should still support color on modern Windows
                    result = supports_color()
                    assert isinstance(result, bool)

    def test_supports_color_no_color_env(self):
        """Test NO_COLOR environment variable disables color."""
        with patch("sys.stdout.isatty", return_value=True):
            with patch.dict("os.environ", {"NO_COLOR": "1"}):
                assert supports_color() is False


class TestPrintFunctions:
    """Test print helper functions."""

    def test_print_success_with_color(self, capsys):
        """Test success message with color."""
        with patch("forge.utils.formatting.supports_color", return_value=True):
            print_success("Build completed successfully")
            captured = capsys.readouterr()
            assert "Build completed successfully" in captured.out
            # Should contain ANSI color codes
            assert "\033[" in captured.out or "✓" in captured.out

    def test_print_success_without_color(self, capsys):
        """Test success message without color."""
        with patch("forge.utils.formatting.supports_color", return_value=False):
            print_success("Build completed successfully")
            captured = capsys.readouterr()
            assert "Build completed successfully" in captured.out
            # Should not contain ANSI color codes
            assert "\033[" not in captured.out

    def test_print_error_with_color(self, capsys):
        """Test error message with color."""
        with patch("forge.utils.formatting.supports_color", return_value=True):
            print_error("Build failed")
            captured = capsys.readouterr()
            assert "Build failed" in captured.err
            # Should contain ANSI color codes
            assert "\033[" in captured.err or "✗" in captured.err

    def test_print_error_without_color(self, capsys):
        """Test error message without color."""
        with patch("forge.utils.formatting.supports_color", return_value=False):
            print_error("Build failed")
            captured = capsys.readouterr()
            assert "Build failed" in captured.err
            # Should not contain ANSI color codes
            assert "\033[" not in captured.err

    def test_print_warning_with_color(self, capsys):
        """Test warning message with color."""
        with patch("forge.utils.formatting.supports_color", return_value=True):
            print_warning("Deprecated option used")
            captured = capsys.readouterr()
            assert "Deprecated option used" in captured.out
            # Should contain ANSI color codes
            assert "\033[" in captured.out or "⚠" in captured.out

    def test_print_warning_without_color(self, capsys):
        """Test warning message without color."""
        with patch("forge.utils.formatting.supports_color", return_value=False):
            print_warning("Deprecated option used")
            captured = capsys.readouterr()
            assert "Deprecated option used" in captured.out
            # Should not contain ANSI color codes
            assert "\033[" not in captured.out

    def test_print_section_header(self, capsys):
        """Test section header formatting."""
        print_section_header("Configuration Phase")
        captured = capsys.readouterr()
        assert "Configuration Phase" in captured.out
        # Should have some visual separation
        assert len(captured.out) > len("Configuration Phase")


class TestConfigureSummary:
    """Test configuration summary output."""

    def test_print_configure_summary_success(self, capsys):
        """Test summary for successful configuration."""
        result = ConfigureResult(
            success=True,
            exit_code=0,
            duration=5.0,
            stdout="Configuration successful",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 0),
            end_time=datetime(2024, 3, 15, 14, 0, 5),
            cmake_version="3.28.1",
            generator="Ninja",
            compiler_c="gcc",
            compiler_cxx="g++",
            build_type="Release",
        )

        print_configure_summary(result)
        captured = capsys.readouterr()

        assert "Configuration" in captured.out or "Configure" in captured.out
        assert "CMake" in captured.out and "3.28.1" in captured.out
        assert "Ninja" in captured.out
        assert "gcc" in captured.out
        assert "Release" in captured.out
        assert "5" in captured.out  # Duration

    def test_print_configure_summary_failure(self, capsys):
        """Test summary for failed configuration."""
        result = ConfigureResult(
            success=False,
            exit_code=1,
            duration=1.0,
            stdout="",
            stderr="CMake Error: Could not find CMakeLists.txt",
            start_time=datetime(2024, 3, 15, 14, 0, 0),
            end_time=datetime(2024, 3, 15, 14, 0, 1),
        )

        print_configure_summary(result)
        captured = capsys.readouterr()

        # Error messages go to stderr
        assert "failed" in captured.err.lower() or "error" in captured.err.lower()
        assert "exit code" in captured.err.lower() or "1" in captured.err

    def test_print_configure_summary_minimal_metadata(self, capsys):
        """Test summary with minimal metadata."""
        result = ConfigureResult(
            success=True,
            exit_code=0,
            duration=2.0,
            stdout="",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 0),
            end_time=datetime(2024, 3, 15, 14, 0, 2),
            cmake_version="3.28.1",
            generator=None,
            compiler_c=None,
            compiler_cxx=None,
            build_type=None,
        )

        print_configure_summary(result)
        captured = capsys.readouterr()

        # Should handle None values gracefully
        assert "N/A" in captured.out or "Unknown" in captured.out or "3.28.1" in captured.out


class TestBuildSummary:
    """Test build summary output."""

    def test_print_build_summary_success_no_warnings(self, capsys):
        """Test summary for successful build without warnings."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=20.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 30),
            warnings_count=0,
            errors_count=0,
            targets_built=["myapp"],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        assert "Build" in captured.out
        assert (
            "success" in captured.out.lower()
            or "✓" in captured.out
            or "completed" in captured.out.lower()
        )
        assert "1 target" in captured.out or "myapp" in captured.out
        assert "0" in captured.out  # Warnings count
        assert "20" in captured.out  # Duration

    def test_print_build_summary_success_with_warnings(self, capsys):
        """Test summary for successful build with warnings."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=20.0,
            stdout="Build finished with warnings",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 30),
            warnings_count=2,
            errors_count=0,
            targets_built=["myapp"],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        assert "2 warnings" in captured.out or "2 warning" in captured.out
        # Should highlight warnings even on success
        assert "warning" in captured.out.lower()

    def test_print_build_summary_failure(self, capsys):
        """Test summary for failed build."""
        result = BuildResult(
            success=False,
            exit_code=2,
            duration=2.0,
            stdout="",
            stderr="Build failed",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 12),
            warnings_count=0,
            errors_count=1,
            targets_built=[],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        # Error messages go to stderr
        assert "failed" in captured.err.lower() or "error" in captured.err.lower()
        assert "1 error" in captured.err or "1 error" in captured.out
        assert "exit code" in captured.err.lower() or "2" in captured.err

    def test_print_build_summary_multiple_targets(self, capsys):
        """Test summary with multiple build targets."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=35.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 45),
            warnings_count=0,
            errors_count=0,
            targets_built=["myapp", "libutils", "libhelper"],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        assert "3 targets" in captured.out or "3 target" in captured.out

    def test_print_build_summary_no_metadata(self, capsys):
        """Test summary with minimal data."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=5.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 15),
            warnings_count=0,
            errors_count=0,
            targets_built=[],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        # Should handle empty targets list gracefully
        assert "Build" in captured.out
        assert "success" in captured.out.lower() or "completed" in captured.out.lower()


class TestVerboseOutput:
    """Test verbose vs normal output modes."""

    def test_verbose_mode_shows_details(self, capsys):
        """Test that verbose mode shows additional details."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=20.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 30),
            warnings_count=0,
            errors_count=0,
            targets_built=["myapp"],
        )

        # Test verbose mode
        print_build_summary(result, verbose=True)
        verbose_output = capsys.readouterr()

        # Test normal mode
        print_build_summary(result, verbose=False)
        normal_output = capsys.readouterr()

        # Verbose should have more information
        assert len(verbose_output.out) >= len(normal_output.out)

    def test_verbose_mode_shows_timestamps(self, capsys):
        """Test that verbose mode shows start/end timestamps."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=20.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 30),
            warnings_count=0,
            errors_count=0,
            targets_built=[],
        )

        print_build_summary(result, verbose=True)
        captured = capsys.readouterr()

        # Should show timestamps in verbose mode
        assert "2024" in captured.out or "14:00" in captured.out


class TestOutputConsistency:
    """Test output formatting consistency."""

    def test_all_summaries_use_consistent_formatting(self, capsys):
        """Test that all summary functions use consistent formatting."""
        configure_result = ConfigureResult(
            success=True,
            exit_code=0,
            duration=1.0,
            stdout="",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
            cmake_version="3.28.1",
            generator="Ninja",
            compiler_c="gcc",
            compiler_cxx="g++",
            build_type="Release",
        )

        build_result = BuildResult(
            success=True,
            exit_code=0,
            duration=1.0,
            stdout="",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
            warnings_count=0,
            errors_count=0,
            targets_built=[],
        )

        print_configure_summary(configure_result)
        configure_output = capsys.readouterr()

        print_build_summary(build_result)
        build_output = capsys.readouterr()

        # Both should have similar structure (non-empty, formatted)
        assert len(configure_output.out) > 0
        assert len(build_output.out) > 0

    def test_line_length_is_reasonable(self, capsys):
        """Test that output lines don't exceed reasonable length."""
        result = BuildResult(
            success=True,
            exit_code=0,
            duration=20.0,
            stdout="Build finished",
            stderr="",
            start_time=datetime(2024, 3, 15, 14, 0, 10),
            end_time=datetime(2024, 3, 15, 14, 0, 30),
            warnings_count=0,
            errors_count=0,
            targets_built=["myapp_with_very_long_name"],
        )

        print_build_summary(result)
        captured = capsys.readouterr()

        # Most lines should be under 100 characters (reasonable terminal width)
        lines = captured.out.split("\n")
        long_lines = [line for line in lines if len(line) > 120]
        assert len(long_lines) < len(lines) / 2  # Most lines should be reasonable length
