"""
Result dataclasses for configure and build operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ConfigureResult:
    """
    Represents the result of a CMake configuration operation.

    Attributes:
        success: Whether the configuration succeeded
        exit_code: Process exit code
        duration: Time taken in seconds
        stdout: Standard output from cmake
        stderr: Standard error from cmake
        start_time: When configuration started
        end_time: When configuration ended
        cmake_version: Detected CMake version
        generator: CMake generator used
        compiler_c: C compiler path
        compiler_cxx: C++ compiler path
        build_type: Build type (Debug, Release, etc.)
    """

    success: bool
    exit_code: int
    duration: float
    stdout: str
    stderr: str
    start_time: datetime
    end_time: datetime
    cmake_version: Optional[str] = None
    generator: Optional[str] = None
    compiler_c: Optional[str] = None
    compiler_cxx: Optional[str] = None
    build_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with datetime objects converted to ISO format strings
        """
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "cmake_version": self.cmake_version,
            "generator": self.generator,
            "compiler_c": self.compiler_c,
            "compiler_cxx": self.compiler_cxx,
            "build_type": self.build_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigureResult":
        """
        Create ConfigureResult from dictionary.

        Args:
            data: Dictionary with result data

        Returns:
            ConfigureResult instance
        """
        # Convert ISO format strings back to datetime objects
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])

        return cls(**data)


@dataclass
class BuildResult:
    """
    Represents the result of a CMake build operation.

    Attributes:
        success: Whether the build succeeded
        exit_code: Process exit code
        duration: Time taken in seconds
        stdout: Standard output from build
        stderr: Standard error from build
        start_time: When build started
        end_time: When build ended
        warnings_count: Number of compiler warnings
        errors_count: Number of compiler errors
        targets_built: List of target names that were built
    """

    success: bool
    exit_code: int
    duration: float
    stdout: str
    stderr: str
    start_time: datetime
    end_time: datetime
    warnings_count: int = 0
    errors_count: int = 0
    targets_built: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with datetime objects converted to ISO format strings
        """
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "duration": self.duration,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "targets_built": self.targets_built,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildResult":
        """
        Create BuildResult from dictionary.

        Args:
            data: Dictionary with result data

        Returns:
            BuildResult instance
        """
        # Convert ISO format strings back to datetime objects
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("end_time"), str):
            data["end_time"] = datetime.fromisoformat(data["end_time"])

        return cls(**data)
