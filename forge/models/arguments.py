"""
ForgeArguments dataclass for command-line arguments.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ForgeArguments:
    """
    Represents parsed and validated command-line arguments for Forge.

    Attributes:
        build_dir: Path to the build directory (required)
        source_dir: Path to the source directory (optional, detected from build_dir if not provided)
        cmake_args: List of arguments to pass to cmake configure step
        build_args: List of arguments to pass to cmake build step
        project_name: Override for project name (detected from CMakeLists.txt if not provided)
        server_url: URL of the Argus server for data upload (optional)
        verbose: Enable verbose output
        dry_run: Perform a dry run without executing commands
        database_path: Path to SQLite database (optional, uses default if not provided)
    """

    build_dir: Path
    source_dir: Optional[Path] = None
    cmake_args: List[str] = field(default_factory=list)
    build_args: List[str] = field(default_factory=list)
    project_name: Optional[str] = None
    server_url: Optional[str] = None
    verbose: bool = False
    dry_run: bool = False
    database_path: Optional[Path] = None

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.build_dir, str):
            self.build_dir = Path(self.build_dir)
        if isinstance(self.source_dir, str):
            self.source_dir = Path(self.source_dir)
        if self.database_path and isinstance(self.database_path, str):
            self.database_path = Path(self.database_path)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation with Path objects converted to strings
        """
        return {
            "build_dir": str(self.build_dir) if self.build_dir else None,
            "source_dir": str(self.source_dir) if self.source_dir else None,
            "cmake_args": self.cmake_args,
            "build_args": self.build_args,
            "project_name": self.project_name,
            "server_url": self.server_url,
            "verbose": self.verbose,
            "dry_run": self.dry_run,
            "database_path": (
                str(self.database_path) if self.database_path else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForgeArguments":
        """
        Create ForgeArguments from dictionary.

        Args:
            data: Dictionary with argument data

        Returns:
            ForgeArguments instance
        """
        # Convert string paths back to Path objects
        if data.get("build_dir"):
            data["build_dir"] = Path(data["build_dir"])
        if data.get("source_dir"):
            data["source_dir"] = Path(data["source_dir"])
        if data.get("database_path"):
            data["database_path"] = Path(data["database_path"])

        return cls(**data)
