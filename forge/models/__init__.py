"""
Forge data models package.

Contains all dataclasses for representing build arguments, results, and metadata.
"""

from forge.models.arguments import ForgeArguments
from forge.models.metadata import (
    BuildMetadata,
    ConfigureMetadata,
    Error,
    Warning,
)
from forge.models.results import BuildResult, ConfigureResult

__all__ = [
    "ForgeArguments",
    "ConfigureResult",
    "BuildResult",
    "ConfigureMetadata",
    "BuildMetadata",
    "Warning",
    "Error",
]
