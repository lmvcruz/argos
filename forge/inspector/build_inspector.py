"""
BuildInspector class for inspecting and analyzing build output.

This module provides functionality for:
- Detecting project names from CMakeLists.txt
- Extracting configuration metadata from CMake output
- Parsing compiler warnings and errors
- Identifying build targets
"""

from pathlib import Path
import re
from typing import Optional, Union

from models.metadata import ConfigureMetadata


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
        """Extract build type from configure output."""
        # Pattern: -- Build type: Release
        pattern = r"--\s+Build type:\s+(\w+)"
        match = re.search(pattern, output)
        return match.group(1) if match else None

    def _extract_found_packages(self, output: str) -> list[str]:
        """Extract list of found packages from configure output."""
        # Pattern: -- Found OpenSSL: /path/to/lib (found version "3.0.2")
        # or: -- Found ZLIB: /path/to/lib (found version "1.2.11")
        # or: -- Found Boost: /path/to/config (found version "1.74.0") found components: ...
        # or: -- Found Python3: /path/to/python (found version "3.11.5") found components: Interpreter
        # or: -- Checking for module 'gtk+-3.0'
        # --   Found gtk+-3.0, version 3.24.33  (this is from pkg-config, skip)
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

