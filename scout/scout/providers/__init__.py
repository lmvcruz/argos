"""
CI provider implementations for Scout.

This module contains the abstract CI provider interface and concrete
implementations for various CI/CD platforms.
"""

from scout.providers.base import CIProvider, Job, LogEntry, WorkflowRun
from scout.providers.github_actions import GitHubActionsProvider

__all__ = [
    "CIProvider",
    "WorkflowRun",
    "Job",
    "LogEntry",
    "GitHubActionsProvider",
]
