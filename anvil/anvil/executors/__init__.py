"""
Executors for running validators with enhanced capabilities.

This module provides executor wrappers around validators that add
features like execution history tracking, selective execution, and
statistics calculation.
"""

from anvil.executors.pytest_executor import PytestExecutorWithHistory

__all__ = [
    "PytestExecutorWithHistory",
]
