"""
BuildInspector class for inspecting and analyzing build output.

This module provides functionality for:
- Detecting project names from CMakeLists.txt
- Extracting configuration metadata from CMake output
- Parsing compiler warnings and errors
- Identifying build targets
"""

from pathlib import Path, PureWindowsPath
import re
from typing import List, Optional, Union

from forge.models.metadata import (
    BuildMetadata,
    BuildTarget,
    BuildWarning,
    ConfigureMetadata,
    Error,
)


class BuildInspector:
    """
    Inspects CMake and build output to extract meaningful metadata.

    This class provides methods to analyze CMakeLists.txt files and
    build output to extract project information, warnings, errors,
    and other build metadata.
    """

    def detect_project_name(self, cmakelists_path: Union[str, Path]) -> Optional[str]:
        """
        Detect the project name from a CMakeLists.txt file.

        Parses the CMakeLists.txt file to find the project() command and
        extract the project name. Handles various project() formats including:
        - Simple: project(MyProject)
        - With language: project(MyProject CXX)
        - With version: project(MyProject VERSION 1.0.0)
        - Multiline declarations
        - Quoted names with spaces

        Args:
            cmakelists_path: Path to the CMakeLists.txt file (string or Path object)

        Returns:
            The project name as a string, or None if:
            - The file doesn't exist
            - No project() call is found
            - The project name cannot be parsed

        Examples:
            >>> inspector = BuildInspector()
            >>> inspector.detect_project_name("CMakeLists.txt")
            'MyProject'
            >>> inspector.detect_project_name("nonexistent.txt")
            None
        """
        # Convert to Path object for consistent handling
        path = Path(cmakelists_path)

        # Check if file exists
        if not path.exists() or not path.is_file():
            return None

        try:
            # Read the entire file content
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            # Handle file reading errors
            return None

        # Remove CMake comments (lines starting with #)
        # But preserve the content for multiline matching
        lines = []
        for line in content.splitlines():
            # Remove inline comments (everything after #)
            # But be careful with # inside strings
            if "#" in line:
                # Simple approach: remove from # to end of line
                # This might not handle all edge cases with strings, but works for most
                comment_pos = line.find("#")
                line = line[:comment_pos]
            lines.append(line)

        # Join back into single string for regex matching
        clean_content = "\n".join(lines)

        # Regular expression to match project() command
        # CMake commands are case-insensitive
        # Match: project( NAME ... ) where NAME can be quoted or unquoted
        # The pattern should handle:
        # - project(Name)
        # - project(Name CXX)
        # - project(Name VERSION 1.0)
        # - project("Name With Spaces")
        # - Multiline project(
        #       Name
        #       VERSION 1.0
        #   )

        # Pattern explanation:
        # (?i) - case insensitive
        # project - literal "project"
        # \s* - optional whitespace
        # \( - opening parenthesis
        # \s* - optional whitespace
        # ("([^"]+)"|'([^']+)'|([^\s\)]+)) - capture group for:
        #   - double-quoted string (group 2)
        #   - single-quoted string (group 3)
        #   - unquoted name (group 4)
        pattern = r'(?i)project\s*\(\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s\)]+))'

        match = re.search(pattern, clean_content)

        if not match:
            return None

        # Extract the project name from capture groups
        # The regex has three groups: (1) double-quoted, (2) single-quoted, (3) unquoted
        project_name = match.group(1) or match.group(2) or match.group(3)

        # Strip any remaining whitespace
        project_name = project_name.strip()

        return project_name if project_name else None

    def inspect_configure_output(self, output: str) -> ConfigureMetadata:
        """
        Inspect CMake configure output to extract metadata.

        Parses the configure output to extract information about:
        - CMake version
        - Generator used
        - C and C++ compilers
        - System name and processor
        - Found packages (via find_package)
        - Build type

        Args:
            output: The complete output from CMake configure command

        Returns:
            ConfigureMetadata object with extracted information.
            Fields will be None if not found in output.

        Examples:
            >>> inspector = BuildInspector(Path("/path"))
            >>> output = "-- CMake version: 3.28.1\\n..."
            >>> metadata = inspector.inspect_configure_output(output)
            >>> metadata.cmake_version
            '3.28.1'
        """
        metadata = ConfigureMetadata(
            project_name=None,
            cmake_version=self._extract_cmake_version(output),
            generator=self._extract_generator(output),
            system_name=self._extract_system_name(output),
            system_processor=self._extract_system_processor(output),
            compiler_c=self._extract_c_compiler(output),
            compiler_cxx=self._extract_cxx_compiler(output),
            build_type=self._extract_build_type(output),
            found_packages=self._extract_found_packages(output),
        )

        return metadata

    def _extract_cmake_version(self, output: str) -> Optional[str]:
        """Extract CMake version from configure output."""
        # Pattern: -- CMake version: 3.28.1
        pattern = r"--\s+CMake version:\s+(\d+\.\d+(?:\.\d+)?)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_generator(self, output: str) -> Optional[str]:
        """Extract generator from configure output."""
        # Pattern: -- Building for: Visual Studio 17 2022
        pattern = r"--\s+Building for:\s+(.+)"
        match = re.search(pattern, output)
        return match.group(1).strip() if match else None

    def _extract_c_compiler(self, output: str) -> Optional[str]:
        """Extract C compiler from configure output."""
        # Pattern: -- The C compiler identification is GNU 11.4.0
        # or: -- The C compiler identification is MSVC 19.37.32825.0
        # or: -- The C compiler identification is AppleClang 14.0.3.14030022
        pattern = r"--\s+The C compiler identification is\s+(\w+)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_cxx_compiler(self, output: str) -> Optional[str]:
        """Extract C++ compiler from configure output."""
        # Pattern: -- The CXX compiler identification is GNU 11.4.0
        pattern = r"--\s+The CXX compiler identification is\s+(\w+)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_system_name(self, output: str) -> Optional[str]:
        """Extract system name from configure output."""
        # Pattern: -- System: Linux
        pattern = r"--\s+System:\s+(\w+)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_system_processor(self, output: str) -> Optional[str]:
        """Extract system processor from configure output."""
        # Pattern: -- Processor: x86_64
        pattern = r"--\s+Processor:\s+(\S+)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_build_type(self, output: str) -> Optional[str]:
        """
        Extract build type from configure output.

        Looks for several patterns:
        - -- Build type: Release (explicit CMake message)
        - CMAKE_BUILD_TYPE:STRING=Debug (cache variable)
        - CMAKE_BUILD_TYPE=Release (configuration output)
        """
        # Pattern 1: -- Build type: Release (explicit message)
        pattern1 = r"--\s+Build type:\s+(\w+)"
        match = re.search(pattern1, output, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 2: CMAKE_BUILD_TYPE:STRING=Debug (cache variable in output)
        pattern2 = r"CMAKE_BUILD_TYPE:STRING=(\w+)"
        match = re.search(pattern2, output, re.IGNORECASE)
        if match:
            return match.group(1)

        # Pattern 3: CMAKE_BUILD_TYPE=Release (simple assignment in output)
        pattern3 = r"CMAKE_BUILD_TYPE=(\w+)"
        match = re.search(pattern3, output, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _extract_found_packages(self, output: str) -> List[str]:
        """
        Extract list of found packages from configure output.

        Matches patterns like:
        - -- Found OpenSSL: /path/to/lib (found version "3.0.2")
        - -- Found Boost: /path (found version "1.74.0") found components: ...
        """
        pattern = r"--\s+Found\s+(\w+):"
        matches = re.findall(pattern, output)

        # Return unique packages in order of appearance
        seen = set()
        packages = []
        for pkg in matches:
            if pkg not in seen:
                seen.add(pkg)
                packages.append(pkg)

        return packages

    def extract_warnings(self, output: str, deduplicate: bool = True) -> List[BuildWarning]:
        """
        Extract compiler warnings from build output.

        Supports warning formats from:
        - GCC: file.cpp:10:5: warning: message [-Wtype]
        - Clang: file.cpp:10:5: warning: message [-Wtype]
        - MSVC: file.cpp(10): warning C4101: message
        - MSVC with column: file.cpp(10,5): warning C4101: message

        Also handles:
        - Warnings without file/line info (linker warnings, etc.)
        - ANSI color codes in output
        - Multiline warnings

        Args:
            output: The build output string to parse
            deduplicate: Whether to remove duplicate warnings (default: True)

        Returns:
            List of BuildWarning objects

        Examples:
            >>> inspector = BuildInspector()
            >>> output = "file.cpp:10:5: warning: unused variable 'x'"
            >>> warnings = inspector.extract_warnings(output)
            >>> len(warnings)
            1
        """
        if not output:
            return []

        # Remove ANSI color codes first
        clean_output = self._strip_ansi_codes(output)

        warnings = []

        # GCC/Clang format: file.cpp:10:5: warning: message [-Wtype]
        gcc_pattern = r"^(.+?):(\d+)(?::(\d+))?\s*:\s*warning:\s*(.+?)(?:\s+\[-W([\w-]+)\])?$"

        # MSVC format: file.cpp(10): warning C4101: message
        # MSVC with column: file.cpp(10,5): warning C4101: message
        msvc_pattern = r"^(.+?)\((\d+)(?:,(\d+))?\)\s*:\s*warning\s+(C\d+):\s*(.+)$"

        # Warnings without file info: warning: message
        # or: ld: warning: message
        generic_pattern = r"^(?:\w+:\s+)?warning:\s*(.+)"

        for line in clean_output.splitlines():
            line = line.strip()

            # Try GCC/Clang format
            match = re.match(gcc_pattern, line)
            if match:
                file, line_num, column, message, warning_type = match.groups()
                warnings.append(
                    BuildWarning(
                        file=file.strip(),
                        line=int(line_num),
                        column=int(column) if column else None,
                        message=message.strip(),
                        warning_type=warning_type,
                    )
                )
                continue

            # Try MSVC format
            match = re.match(msvc_pattern, line)
            if match:
                file, line_num, column, warning_code, message = match.groups()
                warnings.append(
                    BuildWarning(
                        file=file.strip(),
                        line=int(line_num),
                        column=int(column) if column else None,
                        message=message.strip(),
                        warning_type=warning_code,
                    )
                )
                continue

            # Try generic warning format (no file info)
            match = re.match(generic_pattern, line)
            if match:
                message = match.group(1)
                warnings.append(
                    BuildWarning(file=None, line=None, column=None, message=message.strip())
                )

        # Deduplicate if requested
        if deduplicate:
            warnings = self._deduplicate_warnings(warnings)

        return warnings

    def extract_errors(self, output: str) -> List[Error]:
        """
        Extract compiler errors from build output.

        Supports error formats from:
        - GCC: file.cpp:10:5: error: message
        - GCC fatal: file.cpp:1:10: fatal error: message
        - Clang: file.cpp:10:5: error: message
        - MSVC: file.cpp(10): error C2065: message
        - MSVC fatal: file.cpp(1): fatal error C1083: message

        Also handles:
        - ANSI color codes in output
        - Multiline errors

        Args:
            output: The build output string to parse

        Returns:
            List of Error objects

        Examples:
            >>> inspector = BuildInspector()
            >>> output = "file.cpp:10:5: error: 'x' not declared"
            >>> errors = inspector.extract_errors(output)
            >>> len(errors)
            1
        """
        if not output:
            return []

        # Remove ANSI color codes first
        clean_output = self._strip_ansi_codes(output)

        errors = []

        # GCC/Clang format: file.cpp:10:5: error: message
        # Also: file.cpp:10:5: fatal error: message
        gcc_pattern = r"^(.+?):(\d+)(?::(\d+))?\s*:\s*(?:fatal\s+)?error:\s*(.+)"

        # MSVC format: file.cpp(10): error C2065: message
        # MSVC fatal: file.cpp(10): fatal error C1083: message
        msvc_pattern = r"^(.+?)\((\d+)(?:,(\d+))?\)\s*:\s*(?:fatal\s+)?error\s+(C\d+):\s*(.+)"

        for line in clean_output.splitlines():
            line = line.strip()

            # Try GCC/Clang format
            match = re.match(gcc_pattern, line)
            if match:
                file, line_num, column, message = match.groups()
                errors.append(
                    Error(
                        file=file.strip(),
                        line=int(line_num),
                        column=int(column) if column else None,
                        message=message.strip(),
                    )
                )
                continue

            # Try MSVC format
            match = re.match(msvc_pattern, line)
            if match:
                file, line_num, column, error_code, message = match.groups()
                errors.append(
                    Error(
                        file=file.strip(),
                        line=int(line_num),
                        column=int(column) if column else None,
                        message=message.strip(),
                        error_code=error_code,
                    )
                )

        return errors

    def _strip_ansi_codes(self, text: str) -> str:
        """
        Remove ANSI escape codes from text.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        # Pattern matches: ESC [ ... m
        # Where ESC is \033 or \x1b
        ansi_pattern = r"\033\[[0-9;]*m"
        return re.sub(ansi_pattern, "", text)

    def _deduplicate_warnings(self, warnings: List[BuildWarning]) -> List[BuildWarning]:
        """
        Remove duplicate warnings based on file, line, and message.

        Args:
            warnings: List of BuildWarning objects

        Returns:
            List of unique warnings, preserving order
        """
        seen = set()
        unique = []

        for warning in warnings:
            # Create a tuple key for comparison
            key = (warning.file, warning.line, warning.message)

            if key not in seen:
                seen.add(key)
                unique.append(warning)

        return unique

    def _parse_ninja_target(self, line: str, targets: List[BuildTarget]) -> bool:
        """Parse Ninja format target line. Returns True if match found."""
        ninja_linking_pattern = (
            r"\[(\d+)/(\d+)\]\s+Linking\s+(?:C\+\+|CXX|C)\s+"
            r"(executable|static library|shared library)\s+(.+)$"
        )
        match = re.search(ninja_linking_pattern, line)
        if match:
            completion_step = int(match.group(1))
            total_steps = int(match.group(2))
            link_type = match.group(3)
            target_name = match.group(4).strip()

            target_type = self._determine_target_type(target_name, link_type)

            targets.append(
                BuildTarget(
                    name=target_name,
                    target_type=target_type,
                    completion_step=completion_step,
                    total_steps=total_steps,
                )
            )
            return True
        return False

    def _target_already_exists(self, target_name: str, targets: List[BuildTarget]) -> bool:
        """Check if target already exists in list."""
        for existing in targets:
            existing_base = Path(existing.name).stem
            existing_base_no_lib = (
                existing_base[3:] if existing_base.startswith("lib") else existing_base
            )
            target_no_lib = target_name[3:] if target_name.startswith("lib") else target_name

            if (
                existing.name == target_name
                or existing_base == target_name
                or existing_base_no_lib == target_no_lib
            ):
                return True
        return False

    def _parse_make_built_target(self, line: str, targets: List[BuildTarget]) -> bool:
        """Parse Make 'Built target' format line. Returns True if match found."""
        make_built_target_pattern = r"\[\s*\d+%\]\s+Built target\s+(.+)$"
        match = re.search(make_built_target_pattern, line)
        if match:
            target_name = match.group(1).strip()

            # Skip special targets
            if target_name.lower() in ["clean", "all"]:
                return True

            if self._target_already_exists(target_name, targets):
                return True

            # Determine type from target name
            target_type = (
                self._determine_target_type(target_name, "") if "." in target_name else "executable"
            )

            targets.append(
                BuildTarget(
                    name=target_name,
                    target_type=target_type,
                    completion_step=None,
                    total_steps=None,
                )
            )
            return True
        return False

    def _parse_make_linking(self, line: str, targets: List[BuildTarget]) -> bool:
        """Parse Make linking format line. Returns True if match found."""
        make_linking_pattern = (
            r"\[\s*\d+%\]\s+Linking\s+(?:C\+\+|CXX|C)\s+"
            r"(executable|static library|shared library)\s+(.+)$"
        )
        match = re.search(make_linking_pattern, line)
        if match:
            link_type = match.group(1)
            target_name = match.group(2).strip()

            target_type = self._determine_target_type(target_name, link_type)

            base_name = Path(target_name).stem
            if not any(t.name == target_name or Path(t.name).stem == base_name for t in targets):
                targets.append(
                    BuildTarget(
                        name=target_name,
                        target_type=target_type,
                        completion_step=None,
                        total_steps=None,
                    )
                )
            return True
        return False

    def _parse_msvc_target(self, line: str, targets: List[BuildTarget]) -> bool:
        """Parse MSVC format target line. Returns True if match found."""
        msvc_target_pattern = r"\.vcxproj\s+->\s+(?:\")?([^\"]+\.(exe|lib|dll))(?:\")?"
        match = re.search(msvc_target_pattern, line)
        if match:
            full_path = match.group(1).strip()
            extension = match.group(2).lower()

            # Use PureWindowsPath to ensure Windows path parsing works on all platforms
            target_name = PureWindowsPath(full_path).name

            if extension == "exe":
                target_type = "executable"
            elif extension == "lib":
                target_type = "static_library"
            elif extension == "dll":
                target_type = "shared_library"
            else:
                target_type = "unknown"

            if not any(t.name == target_name for t in targets):
                targets.append(
                    BuildTarget(
                        name=target_name,
                        target_type=target_type,
                        completion_step=None,
                        total_steps=None,
                    )
                )
            return True
        return False

    def extract_targets(self, output: str) -> List[BuildTarget]:
        """
        Extract build targets from build system output.

        Parses output from Ninja, Make, and MSVC to identify built targets
        (executables, static libraries, shared libraries).

        Supports:
        - Ninja format: [10/20] Linking CXX executable myapp
        - Make format: [100%] Built target myapp
        - MSVC format: myapp.vcxproj -> C:\\build\\myapp.exe

        Args:
            output: Build output text

        Returns:
            List of BuildTarget objects with name, type, and build progress
        """
        if not output:
            return []

        output = self._strip_ansi_codes(output)
        targets = []

        for line in output.split("\n"):
            line = line.strip()

            # Try each parser in order
            if self._parse_ninja_target(line, targets):
                continue
            if self._parse_make_built_target(line, targets):
                continue
            if self._parse_make_linking(line, targets):
                continue
            if self._parse_msvc_target(line, targets):
                continue

        return targets

    def _determine_target_type(self, target_name: str, link_type: str) -> str:
        """
        Determine target type from name and linking type.

        Args:
            target_name: Name of the target
            link_type: Type from linking command (executable, static library, shared library)

        Returns:
            Target type: executable, static_library, shared_library, or unknown
        """
        # Check link_type first
        if "executable" in link_type.lower():
            return "executable"
        if "static" in link_type.lower():
            return "static_library"
        if "shared" in link_type.lower():
            return "shared_library"

        # Check file extension
        lower_name = target_name.lower()

        if lower_name.endswith((".exe", "")):  # Unix executables often have no extension
            if not lower_name.endswith((".a", ".so", ".lib", ".dll", ".dylib")):
                return "executable"

        if lower_name.endswith((".a", ".lib")):
            return "static_library"

        if lower_name.endswith((".so", ".dll", ".dylib")):
            return "shared_library"

        return "unknown"

    def _determine_target_type_from_extension(self, extension: str) -> str:
        """
        Determine target type from file extension.

        Args:
            extension: File extension (without dot)

        Returns:
            Target type: executable, static_library, shared_library, or unknown
        """
        extension = extension.lower()

        if extension == "exe":
            return "executable"
        if extension == "lib":
            return "static_library"
        if extension == "dll":
            return "shared_library"

        return "unknown"

    def inspect_build_output(
        self, build_output: str, source_dir: Optional[Union[str, Path]] = None
    ) -> BuildMetadata:
        """
        Perform complete inspection of build output and assemble metadata.

        This method integrates all extraction capabilities into a single pipeline:
        - Project name detection (if source_dir provided)
        - Build target extraction
        - Warning extraction
        - Error extraction

        Args:
            build_output: Complete build output text to analyze
            source_dir: Optional path to source directory for project name detection

        Returns:
            BuildMetadata object with complete inspection results including:
            - project_name: Detected project name (or None)
            - targets: List of built targets
            - warnings: List of compiler warnings
            - errors: List of compilation errors

        Examples:
            >>> inspector = BuildInspector()
            >>> metadata = inspector.inspect_build_output(
            ...     build_output="[1/1] Linking CXX executable myapp",
            ...     source_dir="/path/to/project"
            ... )
            >>> metadata.project_name
            'MyProject'
            >>> len(metadata.targets)
            1
        """
        # Detect project name if source directory provided
        project_name = None
        if source_dir:
            cmakelists_path = Path(source_dir) / "CMakeLists.txt"
            if cmakelists_path.exists():
                project_name = self.detect_project_name(cmakelists_path)

        # Extract all components from build output
        targets = self.extract_targets(build_output)
        warnings = self.extract_warnings(build_output)
        errors = self.extract_errors(build_output)

        # Assemble complete metadata
        return BuildMetadata(
            project_name=project_name,
            targets=targets,
            warnings=warnings,
            errors=errors,
        )
