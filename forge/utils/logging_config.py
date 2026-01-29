"""
Logging configuration for Forge application.

Provides centralized logging setup with support for console and file output,
multiple log levels, and proper formatting.
"""

import logging
from pathlib import Path
import sys
from typing import Optional

# Global flag to track if logging has been configured
_logging_configured = False


class ForgeFormatter(logging.Formatter):
    """
    Custom formatter for Forge logging with clean prefix format.

    Formats log messages with [FORGE] prefix for INFO level and
    [DEBUG] prefix for DEBUG level. Other levels use standard formatting.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with custom prefix.

        Args:
            record: Log record to format

        Returns:
            Formatted log message string
        """
        if record.levelno == logging.INFO:
            return f"[FORGE] {record.getMessage()}"
        elif record.levelno == logging.DEBUG:
            return f"[DEBUG] {record.getMessage()}"
        elif record.levelno == logging.WARNING:
            return f"[WARNING] {record.getMessage()}"
        elif record.levelno == logging.ERROR:
            return f"[ERROR] {record.getMessage()}"
        else:
            # For other levels, use standard format
            return super().format(record)


def configure_logging(
    level: Optional[int] = None,
    verbose: bool = False,
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure logging for the Forge application.

    Sets up logging with console output and optionally file output.
    Supports verbose mode for debug logging.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
               If None, defaults to INFO (or DEBUG if verbose=True)
        verbose: If True, sets level to DEBUG and enables verbose output
        log_file: Optional path to log file. If provided, logs will also
                  be written to this file. Parent directories will be created
                  if they don't exist.

    Examples:
        >>> configure_logging()  # Default INFO level to console
        >>> configure_logging(verbose=True)  # DEBUG level to console
        >>> configure_logging(log_file=Path("forge.log"))  # INFO to console and file
    """
    global _logging_configured

    # Determine effective log level
    if verbose:
        effective_level = logging.DEBUG
    elif level is not None:
        effective_level = level
    else:
        effective_level = logging.INFO

    # Get the root logger for forge
    logger = logging.getLogger("forge")
    logger.setLevel(effective_level)

    # Prevent duplicate handlers if already configured
    if _logging_configured:
        # Remove existing handlers
        logger.handlers.clear()

    # Create custom formatter
    formatter = ForgeFormatter()

    # Console handler (stdout for INFO and DEBUG, stderr for WARNING and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if requested)
    if log_file is not None:
        # Create parent directories if needed
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Use timestamp formatter for file logs
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(effective_level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Keep propagate=True to allow pytest caplog to work
    logger.propagate = True

    _logging_configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the given module name.

    Creates a logger under the 'forge' namespace. If no name is provided,
    returns the root forge logger.

    Args:
        name: Optional module name. Will be prefixed with 'forge.'

    Returns:
        Logger instance

    Examples:
        >>> logger = get_logger("executor")
        >>> logger.info("Executing command")
        >>> logger = get_logger()  # Root forge logger
    """
    if name:
        return logging.getLogger(f"forge.{name}")
    return logging.getLogger("forge")


def reset_logging() -> None:
    """
    Reset logging configuration.

    Removes all handlers from the forge logger and resets the configured flag.
    Useful for testing and reconfiguration.

    Examples:
        >>> configure_logging()
        >>> # ... use logging ...
        >>> reset_logging()  # Clean up for reconfiguration
        >>> configure_logging(verbose=True)  # Reconfigure with different settings
    """
    global _logging_configured

    logger = logging.getLogger("forge")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True

    _logging_configured = False
