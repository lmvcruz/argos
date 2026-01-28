"""
Metadata dataclasses for configuration and build information.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BuildWarning:
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
        error_code: Compiler-specific error code (e.g., C2065 for MSVC)
    """

    file: Optional[str]
    line: Optional[int]
    column: Optional[int]
    message: str
    error_type: Optional[str] = None
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "error_type": self.error_type,
            "error_code": self.error_code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Error":
        """Create Error from dictionary."""
        return cls(**data)


@dataclass
class BuildTarget:
    """
    Represents a build target (executable, library, etc.).

    Attributes:
        name: Target name (e.g., "myapp", "libutils.a")
        target_type: Type of target (executable, static_library, shared_library)
        completion_step: Build step when target was completed (e.g., 10 in [10/20])
        total_steps: Total build steps (e.g., 20 in [10/20])
    """

    name: str
    target_type: str
    completion_step: Optional[int] = None
    total_steps: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "target_type": self.target_type,
            "completion_step": self.completion_step,
            "total_steps": self.total_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildTarget":
        """Create BuildTarget from dictionary."""
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
        targets: List of BuildTarget objects that were built
        warnings: List of BuildWarning objects
        errors: List of Error objects
    """

    project_name: Optional[str]
    targets: List[BuildTarget] = field(default_factory=list)
    warnings: List[BuildWarning] = field(default_factory=list)
    errors: List[Error] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "project_name": self.project_name,
            "targets": [t.to_dict() for t in self.targets],
            "warnings": [w.to_dict() for w in self.warnings],
            "errors": [e.to_dict() for e in self.errors],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildMetadata":
        """Create BuildMetadata from dictionary."""
        # Convert dictionaries to objects
        if "targets" in data:
            data["targets"] = [BuildTarget.from_dict(t) for t in data["targets"]]
        if "warnings" in data:
            data["warnings"] = [BuildWarning.from_dict(w) for w in data["warnings"]]
        if "errors" in data:
            data["errors"] = [Error.from_dict(e) for e in data["errors"]]

        return cls(**data)
