"""
Metadata dataclasses for configuration and build information.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Warning:
    """
    Represents a compiler warning.

    Attributes:
        file: Source file where warning occurred
        line: Line number
        column: Column number
        message: Warning message
        warning_type: Type/category of warning
    """

    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    warning_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "warning_type": self.warning_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Warning":
        """Create Warning from dictionary."""
        return cls(**data)


@dataclass
class Error:
    """
    Represents a compiler error.

    Attributes:
        file: Source file where error occurred
        line: Line number
        column: Column number
        message: Error message
        error_type: Type/category of error
    """

    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    error_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "error_type": self.error_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Error":
        """Create Error from dictionary."""
        return cls(**data)


@dataclass
class ConfigureMetadata:
    """
    Metadata extracted from CMake configuration output.

    Attributes:
        project_name: Detected project name
        cmake_version: CMake version used
        generator: CMake generator used
        compiler_c: C compiler path
        compiler_cxx: C++ compiler path
        build_type: Build type (Debug, Release, etc.)
        system_name: Operating system name
        system_processor: Processor architecture
        found_packages: List of packages found by find_package()
        configuration_options: Dictionary of CMake cache variables
    """

    project_name: Optional[str]
    cmake_version: Optional[str]
    generator: Optional[str]
    system_name: Optional[str]
    system_processor: Optional[str]
    compiler_c: Optional[str] = None
    compiler_cxx: Optional[str] = None
    build_type: Optional[str] = None
    found_packages: List[str] = field(default_factory=list)
    configuration_options: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "cmake_version": self.cmake_version,
            "generator": self.generator,
            "compiler_c": self.compiler_c,
            "compiler_cxx": self.compiler_cxx,
            "build_type": self.build_type,
            "system_name": self.system_name,
            "system_processor": self.system_processor,
            "found_packages": self.found_packages,
            "configuration_options": self.configuration_options,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigureMetadata":
        """Create ConfigureMetadata from dictionary."""
        return cls(**data)


@dataclass
class BuildMetadata:
    """
    Metadata extracted from build output.

    Attributes:
        project_name: Project name
        targets_built: List of target names that were built
        warnings: List of Warning objects
        errors: List of Error objects
        total_files_compiled: Number of source files compiled
        parallel_jobs: Number of parallel jobs used
    """

    project_name: Optional[str]
    targets_built: List[str]
    warnings: List[Warning] = field(default_factory=list)
    errors: List[Error] = field(default_factory=list)
    total_files_compiled: Optional[int] = None
    parallel_jobs: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "targets_built": self.targets_built,
            "warnings": [w.to_dict() for w in self.warnings],
            "errors": [e.to_dict() for e in self.errors],
            "total_files_compiled": self.total_files_compiled,
            "parallel_jobs": self.parallel_jobs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildMetadata":
        """Create BuildMetadata from dictionary."""
        # Convert warning and error dictionaries to objects
        if "warnings" in data:
            data["warnings"] = [Warning.from_dict(w) for w in data["warnings"]]
        if "errors" in data:
            data["errors"] = [Error.from_dict(e) for e in data["errors"]]

        return cls(**data)
