"""
Language detection based on file extensions.

Scans project directories to identify Python and C++ files,
with support for custom patterns, exclusions, and symlink handling.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set


class LanguageDetector:
    """
    Detects programming languages in a project based on file extensions.

    Scans a directory tree to identify Python and C++ files, respecting
    exclusion patterns and optional configuration overrides.
    """

    # Default file patterns for each language
    DEFAULT_PATTERNS = {
        "python": ["**/*.py"],
        "cpp": ["**/*.cpp", "**/*.hpp", "**/*.h", "**/*.cc", "**/*.cxx", "**/*.hxx"],
    }

    # Default directories to exclude from scanning
    DEFAULT_EXCLUDES = [
        ".git",
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
        ".tox",
        ".venv",
        "venv",
        "node_modules",
    ]

    def __init__(
        self,
        root_dir: Path,
        file_patterns: Optional[Dict[str, List[str]]] = None,
        exclude_patterns: Optional[List[str]] = None,
        follow_symlinks: bool = False,
    ):
        """
        Initialize language detector.

        Args:
            root_dir: Root directory to scan for source files
            file_patterns: Custom file patterns by language (overrides defaults)
            exclude_patterns: Additional patterns to exclude (adds to defaults)
            follow_symlinks: Whether to follow symbolic links

        Raises:
            FileNotFoundError: If root_dir does not exist
            NotADirectoryError: If root_dir is not a directory
        """
        self.root_dir = Path(root_dir)

        # Validate root directory
        if not self.root_dir.exists():
            raise FileNotFoundError(f"Directory not found: {root_dir}")
        if not self.root_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {root_dir}")

        # Set file patterns (use defaults if not provided)
        self.file_patterns = file_patterns or self.DEFAULT_PATTERNS

        # Combine default and custom exclusions
        self.exclude_patterns = set(self.DEFAULT_EXCLUDES)
        if exclude_patterns:
            self.exclude_patterns.update(exclude_patterns)

        self.follow_symlinks = follow_symlinks

        # Cache for detected files
        self._file_cache: Dict[str, List[Path]] = {}

    def detect_languages(self) -> List[str]:
        """
        Detect which languages are present in the project.

        Scans the directory tree and identifies languages based on
        file extensions found.

        Returns:
            List of detected language names (e.g., ["python", "cpp"])
        """
        detected = []

        for language in self.file_patterns.keys():
            files = self.get_files_for_language(language)
            if files:
                detected.append(language)

        return detected

    def get_files_for_language(self, language: str) -> List[Path]:
        """
        Get all files for a specific language.

        Args:
            language: Language name (e.g., "python", "cpp")

        Returns:
            List of Path objects for files of the specified language
        """
        # Check cache first
        if language in self._file_cache:
            return self._file_cache[language]

        # Return empty list if language not configured
        if language not in self.file_patterns:
            return []

        files: Set[Path] = set()

        # Use os.walk to control symlink following
        for dirpath, dirnames, filenames in os.walk(
            self.root_dir, followlinks=self.follow_symlinks
        ):
            dir_path = Path(dirpath)

            # Filter out excluded directories in-place to prevent descent
            dirnames[:] = [d for d in dirnames if not self._should_exclude_dir(dir_path / d)]

            # Check each file against the patterns
            for filename in filenames:
                file_path = dir_path / filename

                # Check if file matches any pattern for this language
                if self._matches_pattern(file_path, language):
                    # Additional check: ensure it's a file (not broken symlink)
                    if file_path.is_file():
                        files.add(file_path)

        # Convert to sorted list and cache
        result = sorted(files)
        self._file_cache[language] = result

        return result

    def _matches_pattern(self, file_path: Path, language: str) -> bool:
        """
        Check if file matches any pattern for the specified language.

        Args:
            file_path: File path to check
            language: Language name

        Returns:
            True if file matches any pattern, False otherwise
        """
        for pattern in self.file_patterns[language]:
            # Convert glob pattern to suffix match for efficiency
            # Patterns like "**/*.py" -> ".py", "**/*.cpp" -> ".cpp"
            if pattern.startswith("**/"):
                suffix = pattern[3:]  # Remove "**/
                if suffix.startswith("*"):
                    suffix = suffix[1:]  # Remove "*"
                if file_path.name.endswith(suffix.lstrip("*")):
                    return True
            else:
                # For more complex patterns, use match (less efficient)
                if file_path.match(pattern):
                    return True

        return False

    def _should_exclude_dir(self, dir_path: Path) -> bool:
        """
        Check if a directory should be excluded from scanning.

        Args:
            dir_path: Directory path to check

        Returns:
            True if directory should be excluded, False otherwise
        """
        dir_name = dir_path.name

        for pattern in self.exclude_patterns:
            # Simple pattern matching
            if dir_name == pattern or dir_name.startswith(pattern.rstrip("*")):
                return True

        return False

    def _should_exclude(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded based on exclusion patterns.

        Args:
            file_path: File path to check

        Returns:
            True if file should be excluded, False otherwise
        """
        # Get path relative to root
        try:
            rel_path = file_path.relative_to(self.root_dir)
        except ValueError:
            # File is outside root directory (symlink?)
            return True

        # Check each part of the path against exclusion patterns
        parts = rel_path.parts

        for pattern in self.exclude_patterns:
            # Simple pattern matching (exact match or in path)
            for part in parts:
                if part == pattern or part.startswith(pattern.rstrip("*")):
                    return True

        return False
