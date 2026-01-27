"""
Error handling and user feedback for command-line arguments.

Provides ArgumentError exception class and error formatting utilities
for presenting validation errors to users with helpful context and suggestions.
"""

import os
import sys
from types import SimpleNamespace
from typing import Optional

from forge.cli.argument_validator import ValidationError


class ArgumentError(Exception):
    """
    User-friendly exception for command-line argument errors.

    This exception wraps ValidationError and other argument-related errors
    to provide consistent, helpful error messages with suggestions and
    help references.

    Attributes:
        message: The main error message
        suggestion: Optional suggestion for fixing the error
        path: Optional path related to the error
        exit_code: Exit code for CLI (default: 2 for invalid arguments)
        original_error: The original exception if this wraps another error
    """

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        message: str,
        suggestion: Optional[str] = None,
        path: Optional[str] = None,
        exit_code: int = 2,
        original_error: Optional[Exception] = None,
    ):
        """
        Initialize ArgumentError.

        Args:
            message: The main error message
            suggestion: Optional suggestion for fixing the error
            path: Optional path related to the error
            exit_code: Exit code for CLI (default: 2)
            original_error: The original exception if wrapping
        """
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion
        self.path = path
        self.exit_code = exit_code
        self.original_error = original_error

    @classmethod
    def from_validation_error(cls, error: ValidationError) -> "ArgumentError":
        """
        Create ArgumentError from ValidationError.

        Extracts the error message and converts it to a user-friendly
        ArgumentError with help references.

        Args:
            error: The ValidationError to convert

        Returns:
            ArgumentError with formatted message and help reference
        """
        message = str(error)

        # Extract suggestion if present in message (look for newlines)
        suggestion = None
        if "\n" in message:
            parts = message.split("\n", 1)
            message = parts[0]
            suggestion = parts[1].strip() if len(parts) > 1 else None

        return cls(
            message=message,
            suggestion=suggestion,
            original_error=error,
        )

    def __str__(self) -> str:
        """Return user-friendly string representation."""
        return self.message

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"ArgumentError(message={self.message!r}, " f"exit_code={self.exit_code})"


def format_error(
    error: ArgumentError,
    use_color: Optional[bool] = None,
) -> str:
    """
    Format an ArgumentError for display to the user.

    Creates a user-friendly error message with:
    - Clear error indication
    - The error message
    - Suggestions if available
    - Help command reference
    - Optional ANSI color codes for terminal output

    Args:
        error: The ArgumentError to format
        use_color: Whether to use ANSI color codes. If None, auto-detects
                  based on terminal support.

    Returns:
        Formatted error message string
    """
    # Auto-detect color support if not specified
    if use_color is None:
        use_color = _supports_color()

    # ANSI color codes
    if use_color:
        ansi = SimpleNamespace(red="\033[31m", yellow="\033[33m", reset="\033[0m", bold="\033[1m")
    else:
        ansi = SimpleNamespace(red="", yellow="", reset="", bold="")

    # Build the error message
    lines = []

    # Error header
    lines.append(f"{ansi.red}{ansi.bold}Error:{ansi.reset} {error.message}")

    # Add path if provided
    if error.path:
        lines.append(f"  Path: {error.path}")

    # Add suggestion if provided
    if error.suggestion:
        lines.append(f"{ansi.yellow}Suggestion:{ansi.reset} {error.suggestion}")

    # Add help reference
    lines.append("\nRun 'forge --help' for usage information.")

    # Join and ensure reset at end if using colors
    result = "\n".join(lines)
    if use_color and not result.endswith(ansi.reset):
        result += ansi.reset

    return result


def _supports_color() -> bool:
    """
    Detect if the terminal supports ANSI color codes.

    Returns:
        True if terminal supports colors, False otherwise
    """
    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # On Windows, check for ANSICON or WT_SESSION (Windows Terminal)
    if os.name == "nt":
        return "ANSICON" in os.environ or "WT_SESSION" in os.environ or "TERM" in os.environ

    # On Unix-like systems, check TERM variable
    return True
