"""
Test logging configuration and output.

Tests logging setup, levels, formatters, and output destinations.
"""

import io
import logging
from pathlib import Path
import sys
from typing import Optional

import pytest

from forge.utils.logging_config import (
    configure_logging,
    get_logger,
    reset_logging,
)


class TestLoggingConfiguration:
    """Test basic logging configuration."""

    def test_configure_logging_default_level(self, caplog):
        """Test default logging level is INFO."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        # Debug should not be logged, info should be
        assert "Debug message" not in caplog.text
        assert "Info message" in caplog.text

    def test_configure_logging_verbose_level(self, caplog):
        """Test verbose mode sets DEBUG level."""
        reset_logging()
        configure_logging(verbose=True)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        # Both should be logged in verbose mode
        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text

    def test_configure_logging_info_level_explicit(self, caplog):
        """Test INFO level can be set explicitly."""
        reset_logging()
        configure_logging(level=logging.INFO)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        assert "Debug message" not in caplog.text
        assert "Info message" in caplog.text

    def test_configure_logging_warning_level(self, caplog):
        """Test WARNING level filters out INFO."""
        reset_logging()
        configure_logging(level=logging.WARNING)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.info("Info message")
            logger.warning("Warning message")

        assert "Info message" not in caplog.text
        assert "Warning message" in caplog.text

    def test_configure_logging_error_level(self, caplog):
        """Test ERROR level filters out WARNING."""
        reset_logging()
        configure_logging(level=logging.ERROR)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.warning("Warning message")
            logger.error("Error message")

        assert "Warning message" not in caplog.text
        assert "Error message" in caplog.text


class TestLoggerRetrieval:
    """Test logger retrieval and naming."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_name(self):
        """Test get_logger uses provided name."""
        logger = get_logger("my_module")
        assert logger.name == "forge.my_module"

    def test_get_logger_default_name(self):
        """Test get_logger with no name uses root logger."""
        logger = get_logger()
        assert logger.name == "forge"

    def test_get_logger_same_name_returns_same_instance(self):
        """Test get_logger returns same instance for same name."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        assert logger1 is logger2


class TestConsoleOutput:
    """Test console output configuration."""

    def test_log_output_to_console_default(self, caplog):
        """Test logs are output to console by default."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Test message")

        assert "Test message" in caplog.text

    def test_console_handler_configured(self):
        """Test console handler is configured."""
        reset_logging()
        configure_logging()
        logger = get_logger()

        # Check that at least one handler is configured
        assert len(logger.handlers) > 0 or len(logging.root.handlers) > 0


class TestFileOutput:
    """Test file output configuration."""

    def test_log_output_to_file(self, tmp_path):
        """Test logs can be written to file."""
        log_file = tmp_path / "test.log"
        reset_logging()
        configure_logging(log_file=log_file)
        logger = get_logger("test")

        logger.info("Test message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()
        for handler in logging.root.handlers:
            handler.flush()

        # Read log file
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_log_file_created_in_directory(self, tmp_path):
        """Test log file is created in specified directory."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "forge.log"
        reset_logging()
        configure_logging(log_file=log_file)
        logger = get_logger("test")

        logger.info("Test message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()
        for handler in logging.root.handlers:
            handler.flush()

        assert log_dir.exists()
        assert log_file.exists()

    def test_both_console_and_file_output(self, tmp_path, caplog):
        """Test logs can go to both console and file."""
        log_file = tmp_path / "test.log"
        reset_logging()
        configure_logging(log_file=log_file)
        logger = get_logger("test")

        logger.info("Test message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()
        for handler in logging.root.handlers:
            handler.flush()

        # Check console
        assert "Test message" in caplog.text

        # Check file
        content = log_file.read_text()
        assert "Test message" in content


class TestLogFormatting:
    """Test log message formatting."""

    def test_log_format_includes_level(self, caplog):
        """Test log format includes level name."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Test message")

        assert "INFO" in caplog.text

    def test_log_format_includes_message(self, caplog):
        """Test log format includes the message."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Test message")

        assert "Test message" in caplog.text

    def test_log_format_includes_logger_name(self, caplog):
        """Test log format includes logger name."""
        reset_logging()
        configure_logging()
        logger = get_logger("mymodule")

        logger.info("Test message")

        # Should contain the logger name
        assert "forge.mymodule" in caplog.text

    def test_log_format_different_levels(self, caplog):
        """Test different log levels are formatted correctly."""
        reset_logging()
        configure_logging(level=logging.DEBUG, verbose=True)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        assert "DEBUG" in caplog.text
        assert "INFO" in caplog.text
        assert "WARNING" in caplog.text
        assert "ERROR" in caplog.text


class TestExceptionLogging:
    """Test exception logging with stack traces."""

    def test_exception_logged_with_traceback(self, caplog):
        """Test exceptions are logged with stack traces."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")

        # Check error message is logged
        assert "An error occurred" in caplog.text
        # Check exception type is logged
        assert "ValueError" in caplog.text
        # Check exception message is logged
        assert "Test error" in caplog.text

    def test_exception_traceback_includes_file_info(self, caplog):
        """Test exception traceback includes file and line info."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        try:
            raise RuntimeError("Test error")
        except RuntimeError:
            logger.exception("Exception occurred")

        # Should contain traceback information
        assert "Traceback" in caplog.text or "RuntimeError" in caplog.text

    def test_error_without_exception_context(self, caplog):
        """Test error logging without exception context."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.error("Error message without exception")

        assert "Error message without exception" in caplog.text
        # Should NOT contain traceback if no exception
        assert "Traceback" not in caplog.text


class TestPerformanceLogging:
    """Test performance logging (timing info)."""

    def test_timing_info_logged(self, caplog):
        """Test timing information can be logged."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        duration = 1.234
        logger.info(f"Operation completed in {duration:.2f}s")

        assert "Operation completed in 1.23s" in caplog.text

    def test_multiple_timing_logs(self, caplog):
        """Test multiple timing logs are captured."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Starting operation")
        logger.info("Step 1 completed in 0.5s")
        logger.info("Step 2 completed in 1.2s")
        logger.info("Total time: 1.7s")

        assert "Starting operation" in caplog.text
        assert "Step 1 completed in 0.5s" in caplog.text
        assert "Step 2 completed in 1.2s" in caplog.text
        assert "Total time: 1.7s" in caplog.text


class TestLoggingReset:
    """Test logging reset functionality."""

    def test_reset_logging_clears_handlers(self):
        """Test reset_logging removes all handlers."""
        configure_logging()
        logger = get_logger()
        initial_handler_count = len(logger.handlers) + len(logging.root.handlers)

        reset_logging()

        # After reset, should have no handlers (or just default root handler)
        logger = get_logger()
        # Root logger might still have handlers, but our forge logger shouldn't
        assert len(logger.handlers) == 0

    def test_reconfigure_after_reset(self, caplog):
        """Test logging can be reconfigured after reset."""
        configure_logging()
        reset_logging()
        configure_logging(verbose=True)
        logger = get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug after reset")

        assert "Debug after reset" in caplog.text


class TestContextualLogging:
    """Test logging with contextual information."""

    def test_log_with_extra_context(self, caplog):
        """Test logging with extra contextual information."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Build completed", extra={"build_id": 123})

        assert "Build completed" in caplog.text

    def test_log_structured_data(self, caplog):
        """Test logging structured data."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Configuration: source_dir=/path/to/src, build_dir=/path/to/build")

        assert "Configuration" in caplog.text
        assert "source_dir=/path/to/src" in caplog.text


class TestMultipleLoggers:
    """Test multiple loggers with different configurations."""

    def test_different_modules_same_config(self, caplog):
        """Test different modules share configuration."""
        reset_logging()
        configure_logging()
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        logger1.info("Message from module1")
        logger2.info("Message from module2")

        assert "Message from module1" in caplog.text
        assert "Message from module2" in caplog.text

    def test_logger_hierarchy(self, caplog):
        """Test logger hierarchy works correctly."""
        reset_logging()
        configure_logging()
        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        parent_logger.info("Parent message")
        child_logger.info("Child message")

        assert "Parent message" in caplog.text
        assert "Child message" in caplog.text


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_configure_logging_multiple_times(self, caplog):
        """Test calling configure_logging multiple times."""
        configure_logging()
        configure_logging()  # Should handle gracefully
        logger = get_logger("test")

        logger.info("Test message")

        # Should not duplicate messages
        assert caplog.text.count("Test message") == 1

    def test_log_with_none_message(self, caplog):
        """Test logging None doesn't crash."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info(None)

        assert "None" in caplog.text

    def test_log_with_empty_string(self, caplog):
        """Test logging empty string."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("")

        # Should log without error (even if empty)
        # Caplog will capture the log record

    def test_log_with_unicode(self, caplog):
        """Test logging Unicode characters."""
        reset_logging()
        configure_logging()
        logger = get_logger("test")

        logger.info("Unicode test: 你好世界 🎉")

        assert "Unicode test" in caplog.text
        assert "你好世界" in caplog.text

    def test_log_file_path_with_spaces(self, tmp_path, caplog):
        """Test log file path with spaces."""
        log_file = tmp_path / "log dir with spaces" / "test.log"
        reset_logging()
        configure_logging(log_file=log_file)
        logger = get_logger("test")

        logger.info("Test message")

        # Force flush
        for handler in logger.handlers:
            handler.flush()
        for handler in logging.root.handlers:
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
