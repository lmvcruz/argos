"""
ArgumentParser for Forge CLI.

Handles command-line argument parsing and converts to ForgeArguments dataclass.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from forge.models.arguments import ForgeArguments


class ArgumentParser:
    """
    Parser for Forge command-line arguments.

    Parses command-line arguments and returns a ForgeArguments object
    with all parsed values.
    """

    def __init__(self):
        """Initialize the argument parser with all Forge arguments."""
        self.parser = argparse.ArgumentParser(
            prog="forge",
            description="Forge - Non-intrusive CMake build wrapper",
            epilog="For more information, see the documentation.",
        )

        self._add_arguments()

    def _add_arguments(self):
        """Add all command-line arguments to the parser."""
        # Required arguments
        self.parser.add_argument(
            "--build-dir",
            type=Path,
            required=True,
            help="CMake build directory (required)",
        )

        # Optional path arguments
        self.parser.add_argument(
            "--source-dir",
            type=Path,
            default=None,
            help="Source directory containing CMakeLists.txt (optional, inferred from build-dir if not provided)",
        )

        self.parser.add_argument(
            "--database",
            type=Path,
            default=None,
            dest="database_path",
            help="Path to SQLite database file (default: ~/.forge/forge.db)",
        )

        # Project configuration
        self.parser.add_argument(
            "--project-name",
            type=str,
            default=None,
            help="Override project name (default: detected from CMakeLists.txt)",
        )

        # Boolean flags
        self.parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose output",
        )

        self.parser.add_argument(
            "--no-configure",
            action="store_false",
            dest="configure",
            default=True,
            help="Skip CMake configure step (build only)",
        )

        self.parser.add_argument(
            "--clean-build",
            action="store_true",
            default=False,
            help="Clean build directory before building",
        )

        # Version
        self.parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )

    def parse(self, args: Optional[List[str]] = None) -> ForgeArguments:
        """
        Parse command-line arguments and return ForgeArguments object.

        Args:
            args: List of argument strings to parse. If None, uses sys.argv[1:].

        Returns:
            ForgeArguments object with parsed values.

        Raises:
            SystemExit: If parsing fails or --help/--version is used.
        """
        if args is None:
            args = sys.argv[1:]

        # Handle --cmake-args and --build-args specially
        # Extract them before passing to argparse
        cmake_args_list = []
        build_args_list = []
        filtered_args = []

        # Known flags that end cmake-args/build-args collection
        forge_flags = {
            "--build-dir", "--source-dir", "--database",
            "--project-name", "--verbose", "--no-configure",
            "--clean-build", "--version", "--help", "-h"
        }

        i = 0
        while i < len(args):
            if args[i] == "--cmake-args":
                # Collect all args until next forge flag or end
                i += 1
                while i < len(args) and args[i] not in forge_flags:
                    cmake_args_list.append(args[i])
                    i += 1
                continue
            elif args[i] == "--build-args":
                # Collect all args until next forge flag or end
                i += 1
                while i < len(args) and args[i] not in forge_flags:
                    build_args_list.append(args[i])
                    i += 1
                continue
            else:
                filtered_args.append(args[i])
                i += 1

        # Parse arguments
        parsed = self.parser.parse_args(filtered_args)

        # Convert to absolute paths and expand user directory
        build_dir = Path(parsed.build_dir).expanduser().resolve()
        source_dir = (
            Path(parsed.source_dir).expanduser().resolve()
            if parsed.source_dir
            else None
        )
        database_path = (
            Path(parsed.database_path).expanduser().resolve()
            if parsed.database_path
            else None
        )

        # Use the cmake_args and build_args we collected
        cmake_args = cmake_args_list if cmake_args_list else []
        build_args = build_args_list if build_args_list else []

        # Create and return ForgeArguments object
        return ForgeArguments(
            build_dir=build_dir,
            source_dir=source_dir,
            cmake_args=cmake_args,
            build_args=build_args,
            database_path=database_path,
            project_name=parsed.project_name,
            verbose=parsed.verbose,
            configure=parsed.configure,
            clean_build=parsed.clean_build,
        )
