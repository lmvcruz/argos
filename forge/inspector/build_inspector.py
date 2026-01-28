"""
BuildInspector class for inspecting and analyzing build output.

This module provides functionality for:
- Detecting project names from CMakeLists.txt
- Extracting configuration metadata from CMake output
- Parsing compiler warnings and errors
- Identifying build targets
"""

import re
from pathlib import Path
from typing import Optional, Union


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
            content = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            # Handle file reading errors
            return None

        # Remove CMake comments (lines starting with #)
        # But preserve the content for multiline matching
        lines = []
        for line in content.splitlines():
            # Remove inline comments (everything after #)
            # But be careful with # inside strings
            if '#' in line:
                # Simple approach: remove from # to end of line
                # This might not handle all edge cases with strings, but works for most
                comment_pos = line.find('#')
                line = line[:comment_pos]
            lines.append(line)

        # Join back into single string for regex matching
        clean_content = '\n'.join(lines)

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
