"""
Parser for include-what-you-use (IWYU) output.

IWYU analyzes C++ code and suggests include optimizations.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Optional

from anvil.models.validator import Issue, ValidationResult


class IWYUParser:
    """
    Parser for include-what-you-use output.

    IWYU suggests adding/removing includes and forward declarations
    to optimize C++ include dependencies.
    """

    def parse_output(self, output: str, files: List[str], exit_code: int = 0) -> ValidationResult:
        """
        Parse IWYU output and extract include suggestions.

        IWYU output format:
        - "file.cpp has correct #includes/fwd-decls" = no issues
        - "file.cpp should add these lines:" = missing includes
        - "file.cpp should remove these lines:" = unnecessary includes
        - "The full include-list for file.cpp:" = complete include list

        Args:
            output: Raw output from IWYU
            files: List of files that were analyzed
            exit_code: IWYU exit code (ignored, uses text parsing)

        Returns:
            ValidationResult with warnings for include suggestions
        """
        issues = []

        if not output.strip():
            # Empty output means no issues
            return ValidationResult(
                validator_name="iwyu",
                passed=True,
                errors=[],
                warnings=[],
                execution_time=0.0,
                files_checked=len(files),
            )

        # Split output by file sections
        # IWYU outputs suggestions per file
        lines = output.split("\n")

        current_file = None
        in_add_section = False
        in_remove_section = False

        for line in lines:
            # Check if this line indicates correct includes
            if "has correct #includes/fwd-decls" in line:
                # Extract filename
                match = re.search(r"^(.+?)\s+has correct", line)
                if match:
                    current_file = match.group(1).strip()
                    # Normalize path
                    current_file = Path(current_file).as_posix()
                continue

            # Check for file with suggestions
            file_match = re.match(r"^(.+?)\s+should (add|remove) these lines:", line)
            if file_match:
                current_file = file_match.group(1).strip()
                current_file = Path(current_file).as_posix()
                action = file_match.group(2)

                if action == "add":
                    in_add_section = True
                    in_remove_section = False
                elif action == "remove":
                    in_add_section = False
                    in_remove_section = True

                continue

            # Check for full include list section
            if "The full include-list for" in line:
                in_add_section = False
                in_remove_section = False
                # Extract filename
                match = re.search(r"The full include-list for (.+?):", line)
                if match:
                    current_file = match.group(1).strip()
                    current_file = Path(current_file).as_posix()
                continue

            # Section delimiter
            if line.strip() == "---":
                in_add_section = False
                in_remove_section = False
                current_file = None
                continue

            # Parse suggestions in add section
            if in_add_section and current_file:
                line = line.strip()
                if line and not line.startswith("(") and not line.startswith("---"):
                    # Extract include or forward declaration
                    include_match = re.match(r"#include\s+[<\"](.+?)[>\"]", line)
                    fwd_decl_match = re.match(r"(class|struct|enum)\s+\w+;", line)

                    if include_match:
                        include_name = include_match.group(1)
                        issues.append(
                            Issue(
                                file_path=current_file,
                                line_number=None,
                                column_number=None,
                                message=f"Should add #include for {include_name}",
                                rule_name="iwyu-add-include",
                                error_code="add",
                                severity="warning",
                            )
                        )
                    elif fwd_decl_match:
                        issues.append(
                            Issue(
                                file_path=current_file,
                                line_number=None,
                                column_number=None,
                                message=f"Should add forward declaration: {line}",
                                rule_name="iwyu-add-fwd-decl",
                                error_code="add",
                                severity="warning",
                            )
                        )

            # Parse suggestions in remove section
            if in_remove_section and current_file:
                line = line.strip()
                if line.startswith("-"):
                    # Remove lines start with "-"
                    # Extract include name
                    include_match = re.search(r"#include\s+[<\"](.+?)[>\"]", line)
                    if include_match:
                        include_name = include_match.group(1)
                        # Extract line numbers if present
                        line_num_match = re.search(r"lines?\s+(\d+)", line)
                        line_num = int(line_num_match.group(1)) if line_num_match else None

                        issues.append(
                            Issue(
                                file_path=current_file,
                                line_number=line_num,
                                column_number=None,
                                message=f"Should remove unnecessary #include <{include_name}>",
                                rule_name="iwyu-remove-include",
                                error_code="remove",
                                severity="warning",
                            )
                        )

        # Determine overall pass/fail
        passed = len(issues) == 0

        return ValidationResult(
            validator_name="iwyu",
            passed=passed,
            errors=[],
            warnings=issues,
            execution_time=0.0,
            files_checked=len(files),
        )

    def build_command(
        self,
        files: List[str],
        mapping_file: Optional[str] = None,
        compiler_flags: Optional[List[str]] = None,
        xiwyu_options: Optional[List[str]] = None,
        std: Optional[str] = None,
        include_paths: Optional[List[str]] = None,
        defines: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Build IWYU command with specified options.

        Args:
            files: List of files to analyze
            mapping_file: Path to IWYU mapping file (.imp)
            compiler_flags: Additional compiler flags
            xiwyu_options: IWYU-specific options (passed with -Xiwyu)
            std: C++ standard (e.g., "c++17")
            include_paths: Include directories
            defines: Preprocessor defines

        Returns:
            Command as list of strings
        """
        command = ["include-what-you-use"]

        # Add mapping file
        if mapping_file:
            command.append(f"--mapping_file={mapping_file}")

        # Add Xiwyu options
        if xiwyu_options:
            for option in xiwyu_options:
                command.extend(["-Xiwyu", option])

        # Add C++ standard
        if std:
            command.append(f"-std={std}")

        # Add include paths
        if include_paths:
            for path in include_paths:
                command.append(f"-I{path}")

        # Add defines
        if defines:
            for define in defines:
                command.append(f"-D{define}")

        # Add additional compiler flags
        if compiler_flags:
            command.extend(compiler_flags)

        # Add files
        command.extend(files)

        return command

    def run(
        self,
        files: List[str],
        timeout: Optional[int] = None,
        **kwargs,
    ) -> ValidationResult:
        """
        Execute IWYU on specified files.

        Args:
            files: List of C++ files to analyze
            timeout: Command timeout in seconds
            **kwargs: Additional options for build_command

        Returns:
            ValidationResult with IWYU suggestions
        """
        try:
            command = self.build_command(files, **kwargs)

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            # IWYU outputs to stderr, not stdout
            output = result.stderr if result.stderr else result.stdout

            return self.parse_output(output, files, result.returncode)

        except FileNotFoundError:
            return ValidationResult(
                validator_name="iwyu",
                passed=False,
                errors=[
                    Issue(
                        file_path="",
                        line_number=None,
                        column_number=None,
                        message="include-what-you-use not found. Please install IWYU.",
                        rule_name="iwyu-not-found",
                        error_code="tool-missing",
                        severity="error",
                    )
                ],
                warnings=[],
                execution_time=0.0,
                files_checked=len(files),
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                validator_name="iwyu",
                passed=False,
                errors=[
                    Issue(
                        file_path="",
                        line_number=None,
                        column_number=None,
                        message=f"IWYU timed out after {timeout} seconds",
                        rule_name="iwyu-timeout",
                        error_code="timeout",
                        severity="error",
                    )
                ],
                warnings=[],
                execution_time=float(timeout) if timeout else 0.0,
                files_checked=len(files),
            )

    def get_version(self) -> Optional[str]:
        """
        Get IWYU version.

        Returns:
            Version string or None if unable to detect
        """
        try:
            result = subprocess.run(
                ["include-what-you-use", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # IWYU version output: "include-what-you-use 0.18 based on clang..."
            output = result.stdout + result.stderr
            match = re.search(r"include-what-you-use\s+(?:version\s+)?(\d+\.\d+)", output)
            if match:
                return match.group(1)

            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def detect_config_file(self, start_path: Path) -> Optional[Path]:
        """
        Detect IWYU mapping file (.iwyu.imp or custom .imp file).

        Searches up directory tree for mapping files.

        Args:
            start_path: Starting directory for search

        Returns:
            Path to mapping file or None if not found
        """
        current = start_path.resolve()

        # Search up to 10 levels
        for _ in range(10):
            # Check for common mapping file names
            for name in [".iwyu.imp", "iwyu.imp", "custom.imp"]:
                config_file = current / name
                if config_file.exists():
                    return config_file

            # Move to parent
            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    def generate_fix_command(
        self, files: List[str], mapping_file: Optional[str] = None
    ) -> List[str]:
        """
        Generate fix command using fix_includes.py script.

        IWYU provides fix_includes.py to apply suggested changes.

        Args:
            files: Files to fix
            mapping_file: Optional mapping file

        Returns:
            Command to apply IWYU suggestions
        """
        command = ["fix_includes.py"]

        if mapping_file:
            command.extend(["--mapping_file", mapping_file])

        # fix_includes.py reads from stdin, so we'd redirect IWYU output
        # For now, just return the base command
        command.extend(files)

        return command
