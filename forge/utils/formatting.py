"""
Output formatting utilities for user-friendly console output.

This module provides functions for formatting build output, timing information,
and user feedback messages with optional color support.
"""

from datetime import datetime
import os
import platform
import sys
from typing import Optional, Union

from forge.models.results import BuildResult, ConfigureResult


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns:
        True if color output is supported, False otherwise
    """
    # Check NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False

    # Check if stdout is a TTY
    if not sys.stdout.isatty():
        return False

    # Windows: Check for Windows Terminal or ANSICON
    if platform.system() == "Windows":
        # Windows Terminal sets WT_SESSION
        if os.environ.get("WT_SESSION"):
            return True
        # ANSICON
        if os.environ.get("ANSICON"):
            return True
        # Windows 10+ supports ANSI escape sequences
        return True

    # Unix-like systems: assume color support if TTY
    return True


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1.23s", "2m 30s", "1h 15m 30s")
    """
    if seconds < 1.0:
        # Sub-second: show milliseconds
        ms = round(seconds * 1000)
        return f"{ms}ms"
    elif seconds < 60.0:
        # Seconds with 2 decimal places
        return f"{seconds:.2f}s"
    elif seconds < 3600.0:
        # Minutes and seconds
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        # Hours, minutes, and seconds
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {mins}m {secs}s"


def format_timestamp(timestamp: Optional[Union[datetime, str]]) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Datetime object or ISO 8601 string

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        return "N/A"

    if isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return timestamp

    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return str(timestamp)


def print_success(message: str) -> None:
    """
    Print success message to stdout.

    Args:
        message: Success message to display
    """
    if supports_color():
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
    else:
        print(f"[SUCCESS] {message}")


def print_error(message: str) -> None:
    """
    Print error message to stderr.

    Args:
        message: Error message to display
    """
    if supports_color():
        print(f"{Colors.RED}✗{Colors.RESET} {message}", file=sys.stderr)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """
    Print warning message to stdout.

    Args:
        message: Warning message to display
    """
    if supports_color():
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
    else:
        print(f"[WARNING] {message}")


def print_section_header(title: str) -> None:
    """
    Print section header with visual separation.

    Args:
        title: Section title
    """
    if supports_color():
        print(f"\n{Colors.BOLD}{Colors.CYAN}{title}{Colors.RESET}")
        print(f"{Colors.CYAN}{'─' * len(title)}{Colors.RESET}")
    else:
        print(f"\n{title}")
        print("=" * len(title))


def print_configure_summary(result: ConfigureResult, verbose: bool = False) -> None:
    """
    Print summary of configuration phase.

    Args:
        result: Configuration result to summarize
        verbose: If True, show additional details
    """
    print_section_header("Configuration Summary")

    # Status
    if result.success:
        print_success(f"Configuration completed in {format_duration(result.duration)}")
    else:
        print_error(f"Configuration failed (exit code {result.exit_code})")
        print(f"  Duration: {format_duration(result.duration)}")
        return

    # Result fields (not metadata object)
    print(f"  CMake Version: {result.cmake_version or 'N/A'}")
    print(f"  Generator: {result.generator or 'N/A'}")
    print(f"  C Compiler: {result.compiler_c or 'N/A'}")
    print(f"  C++ Compiler: {result.compiler_cxx or 'N/A'}")
    print(f"  Build Type: {result.build_type or 'N/A'}")

    # Verbose mode: show timestamps
    if verbose:
        print(f"  Start Time: {format_timestamp(result.start_time)}")
        print(f"  End Time: {format_timestamp(result.end_time)}")


def print_build_summary(result: BuildResult, verbose: bool = False) -> None:
    """
    Print summary of build phase.

    Args:
        result: Build result to summarize
        verbose: If True, show additional details
    """
    print_section_header("Build Summary")

    # Status
    if result.success:
        print_success(f"Build completed in {format_duration(result.duration)}")
    else:
        print_error(f"Build failed (exit code {result.exit_code})")
        print(f"  Duration: {format_duration(result.duration)}")

    # Result fields (not metadata object)
    # Targets
    target_count = len(result.targets_built)
    if target_count > 0:
        target_word = "target" if target_count == 1 else "targets"
        print(f"  Built {target_count} {target_word}")

        if verbose:
            for target in result.targets_built:
                print(f"    - {target}")

    # Warnings
    warning_count = result.warnings_count
    if warning_count > 0:
        warning_word = "warning" if warning_count == 1 else "warnings"
        print_warning(f"{warning_count} {warning_word}")
    else:
        print("  Warnings: 0")

    # Errors
    error_count = result.errors_count
    if error_count > 0:
        error_word = "error" if error_count == 1 else "errors"
        print_error(f"{error_count} {error_word}")
    elif not result.success:
        # Build failed but no errors extracted - show exit code
        pass  # Already shown in status

    # Verbose mode: show timestamps
    if verbose:
        print(f"  Start Time: {format_timestamp(result.start_time)}")
        print(f"  End Time: {format_timestamp(result.end_time)}")
