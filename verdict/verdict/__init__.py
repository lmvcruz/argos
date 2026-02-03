"""
Verdict: Generic test validation framework.

This package provides a flexible framework for validating software
components by comparing actual outputs against expected results.
"""

__version__ = "1.0.0"

from verdict.executor import TargetExecutor
from verdict.loader import ConfigLoader, TestCaseLoader
from verdict.logger import TestLogger
from verdict.runner import TestRunner
from verdict.validator import OutputValidator

__all__ = [
    "ConfigLoader",
    "TestCaseLoader",
    "TargetExecutor",
    "OutputValidator",
    "TestRunner",
    "TestLogger",
]
