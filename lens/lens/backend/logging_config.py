"""
Centralized logging configuration for Lens backend.

Configures both file-based and console logging with proper rotation.
Logs are written to ~/.argos/lens/logs/backend.log with automatic rotation.

Log directory can be configured via:
1. LENS_LOG_DIR environment variable
2. Default: ~/.argos/lens/logs
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


class LoggerManager:
    """Manages centralized logging configuration for Lens backend."""

    _instance: Optional['LoggerManager'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls) -> 'LoggerManager':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_log_dir(cls) -> Path:
        """
        Get the log directory path.

        Priority:
        1. LENS_LOG_DIR environment variable
        2. Default: ~/.argos/lens/logs

        Returns:
            Path to log directory
        """
        if 'LENS_LOG_DIR' in os.environ:
            return Path(os.environ['LENS_LOG_DIR'])
        return Path.home() / '.argos' / 'lens' / 'logs'

    @classmethod
    def initialize(cls, log_level: int = logging.DEBUG) -> logging.Logger:
        """
        Initialize logging with file and console handlers.

        Creates log directory if it doesn't exist.
        Sets up rotating file handler (10MB, 7-day retention).
        Configures console output with proper formatting.

        Args:
            log_level: Logging level (default: logging.DEBUG)

        Returns:
            Configured logger instance
        """
        if cls._logger is not None:
            return cls._logger

        # Create logs directory
        log_dir = cls.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / 'backend.log'

        # Create loggers
        logger = logging.getLogger('lens.backend')
        root_logger = logging.getLogger()  # Root logger for all loggers including anvil
        logger.setLevel(log_level)
        root_logger.setLevel(log_level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        root_logger.handlers.clear()

        # Create formatters
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(name)s - %(message)s'
        )

        # File handler with rotation (10MB, keep 7 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=7
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        cls._logger = logger
        logger.info('Logging initialized at %s', log_file)

        return logger

    @classmethod
    def get_logger(cls, name: str = 'lens.backend') -> logging.Logger:
        """
        Get a logger instance.

        If logging hasn't been initialized, initializes with INFO level.

        Args:
            name: Logger name (default: 'lens.backend')

        Returns:
            Logger instance
        """
        if cls._logger is None:
            cls.initialize()

        return logging.getLogger(name)

    @classmethod
    def set_level(cls, level: int) -> None:
        """
        Set logging level for all handlers.

        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        if cls._logger is None:
            cls.initialize(level)
        else:
            cls._logger.setLevel(level)
            for handler in cls._logger.handlers:
                handler.setLevel(level)


def get_logger(name: str = 'lens.backend') -> logging.Logger:
    """
    Convenience function to get a logger.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return LoggerManager.get_logger(name)


def initialize_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function to initialize logging.

    Args:
        log_level: Logging level

    Returns:
        Logger instance
    """
    return LoggerManager.initialize(log_level)
