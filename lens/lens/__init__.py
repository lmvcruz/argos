"""
Lens - CI Analytics and Visualization Tool.

Provides comprehensive CI health analysis, failure pattern detection,
and visual reports for GitHub Actions workflows.
"""

from lens.backend import (
    ActionRunner,
    ActionType,
    ActionStatus,
    ActionInput,
    ActionOutput,
    app,
)

__version__ = "0.1.0"
__author__ = "Argos Project"

__all__ = [
    "ActionRunner",
    "ActionType",
    "ActionStatus",
    "ActionInput",
    "ActionOutput",
    "app",
]
