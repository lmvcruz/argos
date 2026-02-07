"""
Tests for Lens backend logging configuration.

Tests the LoggerManager singleton and logging initialization.
"""

import logging
import tempfile
from pathlib import Path
import pytest

from lens.backend.logging_config import (
    LoggerManager,
    get_logger,
    initialize_logging
)


class TestLoggerManager:
    """Tests for LoggerManager singleton."""

    def test_singleton_pattern(self):
        """Test that LoggerManager follows singleton pattern."""
        mgr1 = LoggerManager()
        mgr2 = LoggerManager()
        assert mgr1 is mgr2

    def test_initialize_creates_logger(self):
        """Test that initialize() creates a logger with handlers."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        logger = LoggerManager.initialize(logging.INFO)

        assert logger is not None
        assert logger.name == 'lens.backend'
        assert len(logger.handlers) >= 1

    def test_initialize_creates_log_directory(self):
        """Test that initialize() creates ~/.lens/logs directory."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        LoggerManager.initialize(logging.INFO)

        log_dir = Path.home() / '.lens' / 'logs'
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_initialize_creates_log_file(self):
        """Test that initialize() creates log file."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        LoggerManager.initialize(logging.INFO)

        log_file = Path.home() / '.lens' / 'logs' / 'backend.log'
        assert log_file.exists()

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger() returns configured logger."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        LoggerManager.initialize()
        logger = LoggerManager.get_logger()

        assert logger.name == 'lens.backend'
        assert len(logger.handlers) >= 1

    def test_get_logger_with_custom_name(self):
        """Test get_logger with custom name."""
        logger = LoggerManager.get_logger('test.module')
        assert logger.name == 'test.module'

    def test_set_level_changes_log_level(self):
        """Test that set_level() changes logging level."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        LoggerManager.initialize(logging.INFO)
        LoggerManager.set_level(logging.DEBUG)

        logger = LoggerManager._logger
        assert logger.level == logging.DEBUG
        # Check all handlers have correct level
        for handler in logger.handlers:
            assert handler.level == logging.DEBUG

    def test_logger_writes_to_file(self):
        """Test that logger writes messages to file."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        LoggerManager.initialize(logging.INFO)
        logger = LoggerManager.get_logger()

        test_message = "Test message for logging"
        logger.info(test_message)

        log_file = Path.home() / '.lens' / 'logs' / 'backend.log'
        content = log_file.read_text()

        assert test_message in content


class TestLoggingFunctions:
    """Tests for convenience functions."""

    def test_get_logger_function(self):
        """Test get_logger() convenience function."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        logger = get_logger()
        assert logger.name == 'lens.backend'

    def test_initialize_logging_function(self):
        """Test initialize_logging() convenience function."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        logger = initialize_logging(logging.DEBUG)
        assert logger.name == 'lens.backend'
        assert logger.level == logging.DEBUG

    def test_logging_with_different_levels(self):
        """Test logging at different levels."""
        LoggerManager._instance = None
        LoggerManager._logger = None

        logger = initialize_logging(logging.DEBUG)

        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # All should be in file since we set DEBUG level
        log_file = Path.home() / '.lens' / 'logs' / 'backend.log'
        content = log_file.read_text()

        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
