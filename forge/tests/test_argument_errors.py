"""
Unit tests for argument error handling and user feedback.

Tests error message formatting, help references, and colored output support.
Following TDD principles - these tests are written before implementation.
"""

import os
from unittest.mock import patch

from forge.cli.argument_validator import ValidationError
from forge.cli.argument_errors import (
    ArgumentError,
    format_error,
    _supports_color,
)


class TestArgumentErrorCreation:
    """Test ArgumentError exception creation and attributes."""

    def test_argument_error_with_single_message(self):
        """Test creating ArgumentError with a single error message."""
        error = ArgumentError("Build directory does not exist")

        assert str(error)
        assert "Build directory does not exist" in str(error)

    def test_argument_error_with_validation_error(self):
        """Test creating ArgumentError from ValidationError."""
        validation_err = ValidationError("Source directory missing CMakeLists.txt")
        error = ArgumentError.from_validation_error(validation_err)

        assert str(error)
        assert "CMakeLists.txt" in str(error)

    def test_argument_error_has_exit_code(self):
        """Test that ArgumentError includes exit code for CLI."""
        error = ArgumentError("Invalid arguments")

        assert hasattr(error, "exit_code")
        assert error.exit_code == 2  # Standard for invalid arguments

    def test_argument_error_preserves_original_exception(self):
        """Test that ArgumentError preserves the original ValidationError."""
        validation_err = ValidationError("Test error")
        error = ArgumentError.from_validation_error(validation_err)

        assert hasattr(error, "original_error")
        assert error.original_error is validation_err


class TestErrorMessageFormatting:
    """Test error message formatting with proper structure."""

    def test_formatted_error_includes_error_prefix(self):
        """Test that formatted errors have 'Error:' prefix."""
        error = ArgumentError("Test error")
        formatted = format_error(error, use_color=False)

        assert "error:" in formatted.lower()

    def test_formatted_error_includes_message(self):
        """Test that formatted errors include the error message."""
        error = ArgumentError("Build directory does not exist")
        formatted = format_error(error, use_color=False)

        assert "Build directory does not exist" in formatted

    def test_formatted_error_includes_help_reference(self):
        """Test that formatted errors reference the help command."""
        error = ArgumentError("Invalid arguments")
        formatted = format_error(error, use_color=False)

        # Should suggest using --help
        assert "--help" in formatted or "help" in formatted.lower()

    def test_formatted_error_suggests_fixes(self):
        """Test that formatted errors include suggestions when available."""
        error = ArgumentError(
            "Build directory does not exist",
            suggestion="Provide --source-dir to create a new build",
        )
        formatted = format_error(error, use_color=False)

        assert "source-dir" in formatted.lower()
        assert "suggestion" in formatted.lower() or "try" in formatted.lower()


class TestColoredOutput:
    """Test colored vs plain output formatting."""

    def test_plain_output_no_ansi_codes(self):
        """Test that plain output contains no ANSI color codes."""
        error = ArgumentError("Test error")
        formatted = format_error(error, use_color=False)

        # ANSI codes start with \033[ or \x1b[
        assert "\033[" not in formatted
        assert "\x1b[" not in formatted

    def test_colored_output_has_ansi_codes(self):
        """Test that colored output includes ANSI color codes."""
        error = ArgumentError("Test error")
        formatted = format_error(error, use_color=True)

        # Should contain ANSI color codes
        assert "\033[" in formatted or "\x1b[" in formatted

    def test_colored_output_resets_at_end(self):
        """Test that colored output resets colors at the end."""
        error = ArgumentError("Test error")
        formatted = format_error(error, use_color=True)

        # Should contain reset code (0m)
        assert formatted.endswith("\033[0m") or formatted.endswith("\x1b[0m")

    def test_color_auto_detection(self):
        """Test that color is auto-detected based on terminal support."""
        error = ArgumentError("Test error")

        # format_error with no use_color should auto-detect
        formatted = format_error(error)

        # Should produce some output (color or not)
        assert len(formatted) > 0

    def test_color_detection_on_unix(self):
        """Test color detection on Unix-like systems."""
        # Mock Unix environment
        with patch("os.name", "posix"):
            with patch("sys.stdout.isatty", return_value=True):
                assert _supports_color() is True

    def test_color_detection_on_windows_with_wt(self):
        """Test color detection on Windows Terminal."""
        # Mock Windows with Windows Terminal
        with patch("os.name", "nt"):
            with patch("sys.stdout.isatty", return_value=True):
                with patch.dict(os.environ, {"WT_SESSION": "some-value"}):
                    assert _supports_color() is True

    def test_color_detection_no_tty(self):
        """Test color detection when not a TTY."""
        with patch("sys.stdout.isatty", return_value=False):
            assert _supports_color() is False


class TestMultiLineErrors:
    """Test formatting of errors with multiple lines."""

    def test_multiline_error_preserves_structure(self):
        """Test that multiline error messages are formatted correctly."""
        message = (
            "Build directory does not exist: /path/to/build\n" "This can happen when..."
        )
        error = ArgumentError(message)
        formatted = format_error(error, use_color=False)

        # Should preserve line structure
        assert "/path/to/build" in formatted
        assert "This can happen" in formatted

    def test_error_with_suggestion_on_new_line(self):
        """Test that suggestions appear on separate lines."""
        error = ArgumentError(
            "Source directory missing",
            suggestion=("Provide a valid source directory with CMakeLists.txt"),
        )
        formatted = format_error(error, use_color=False)

        lines = formatted.split("\n")
        assert len(lines) >= 2  # At least error line and suggestion line


class TestErrorContextInformation:
    """Test that errors include helpful context."""

    def test_error_includes_command_example(self):
        """Test that errors can include example commands."""
        error = ArgumentError(
            "Missing required argument",
            suggestion="Example: forge --build-dir build --source-dir src",
        )
        formatted = format_error(error, use_color=False)

        assert "forge" in formatted
        assert "build-dir" in formatted

    def test_error_shows_problematic_path(self):
        """Test that errors show the problematic path when relevant."""
        error = ArgumentError(
            "Source directory does not exist: /path/to/missing", path="/path/to/missing"
        )
        formatted = format_error(error, use_color=False)

        assert "/path/to/missing" in formatted

    def test_error_references_documentation(self):
        """Test that complex errors reference documentation."""
        error = ArgumentError(
            "Invalid configuration", suggestion="See --help for more information"
        )
        formatted = format_error(error, use_color=False)

        assert "help" in formatted.lower()


class TestValidationErrorConversion:
    """Test converting ValidationError to ArgumentError for user display."""

    def test_convert_simple_validation_error(self):
        """Test converting a simple ValidationError to ArgumentError."""
        validation_err = ValidationError("Build directory does not exist")
        error = ArgumentError.from_validation_error(validation_err)

        formatted = format_error(error, use_color=False)
        assert "Build directory does not exist" in formatted

    def test_convert_validation_error_extracts_suggestion(self):
        """
        Test that conversion extracts suggestions from ValidationError
        message.
        """
        validation_err = ValidationError(
            "Source directory does not exist: /path\n"
            "Please provide a valid source directory path."
        )
        error = ArgumentError.from_validation_error(validation_err)

        formatted = format_error(error, use_color=False)
        assert "source directory" in formatted.lower()
        assert "/path" in formatted

    def test_convert_validation_error_adds_help_reference(self):
        """Test that converted errors include help reference."""
        validation_err = ValidationError("Invalid configuration")
        error = ArgumentError.from_validation_error(validation_err)

        formatted = format_error(error, use_color=False)
        # Should add help reference during conversion
        assert "help" in formatted.lower() or "--help" in formatted


class TestErrorExitCodes:
    """Test that errors have appropriate exit codes."""

    def test_validation_error_has_exit_code_2(self):
        """Test that validation errors have exit code 2 (invalid arguments)."""
        error = ArgumentError("Invalid arguments")
        assert error.exit_code == 2

    def test_can_override_exit_code(self):
        """Test that exit code can be customized if needed."""
        error = ArgumentError("System error", exit_code=1)
        assert error.exit_code == 1


class TestErrorStringRepresentation:
    """Test string representation of errors for logging."""

    def test_str_representation_is_user_friendly(self):
        """Test that str(error) gives clean user-facing message."""
        error = ArgumentError("Build directory does not exist")
        error_str = str(error)

        # Should not include Python class names or internal details
        assert "ArgumentError" not in error_str
        assert "Traceback" not in error_str
        assert "Build directory does not exist" in error_str

    def test_repr_includes_class_info(self):
        """Test that repr(error) includes class information for debugging."""
        error = ArgumentError("Test error")
        error_repr = repr(error)

        # repr should include class name for debugging
        assert "ArgumentError" in error_repr
