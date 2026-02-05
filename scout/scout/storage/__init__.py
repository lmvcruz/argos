"""
Storage module for Scout CI data persistence.

This module provides database models and persistence layer for storing
GitHub Actions CI data including workflow runs, jobs, test results, and
failure patterns.
"""

from scout.storage.database import DatabaseManager
from scout.storage.schema import (
    AnalysisResult,
    Base,
    CIFailurePattern,
    ExecutionLog,
    WorkflowJob,
    WorkflowRun,
    WorkflowTestResult,
)

__all__ = [
    "Base",
    "DatabaseManager",
    "WorkflowRun",
    "WorkflowJob",
    "WorkflowTestResult",
    "CIFailurePattern",
    "ExecutionLog",
    "AnalysisResult",
]
