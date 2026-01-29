"""
File collection with Git integration.

Collects files for validation in full or incremental modes,
with git integration for detecting changed files.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Set, Union

from anvil.core.language_detector import LanguageDetector


class GitError(Exception):
    """Exception raised for git-related errors."""


class FileCollector:
    """
    Collects files for validation with git integration.

    Supports both full mode (all files) and incremental mode (only changed files).
    Integrates with git to detect modifications, staged files, and commit history.
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        exclude_patterns: Optional[List[str]] = None,
        file_patterns: Optional[dict] = None,
    ):
        """
        Initialize file collector.

        Args:
            root_dir: Root directory to collect files from
            exclude_patterns: Additional patterns to exclude (adds to defaults)
            file_patterns: Custom file patterns by language
        """
        self.root_dir = Path(root_dir)
        self.exclude_patterns = exclude_patterns
        self.file_patterns = file_patterns

        # Initialize language detector
        self.detector = LanguageDetector(
            self.root_dir,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns,
            follow_symlinks=False,
        )

        # Cache for git status
        self._is_git_repo: Optional[bool] = None

    def is_git_repository(self) -> bool:
        """
        Check if root directory is a git repository.

        Returns:
            True if directory is a git repository, False otherwise
        """
        if self._is_git_repo is not None:
            return self._is_git_repo

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            self._is_git_repo = result.returncode == 0
            return self._is_git_repo
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self._is_git_repo = False
            return False

    def has_uncommitted_changes(self) -> bool:
        """
        Check if repository has uncommitted changes.

        Returns:
            True if there are uncommitted changes, False otherwise

        Raises:
            GitError: If not a git repository
        """
        if not self.is_git_repository():
            raise GitError("Not a git repository")

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            return len(result.stdout.strip()) > 0
        except subprocess.CalledProcessError as e:
            raise GitError(f"Failed to check git status: {e}")
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")

    def collect_files(
        self,
        language: Optional[str] = None,
        languages: Optional[List[str]] = None,
        incremental: bool = False,
        staged_only: bool = False,
    ) -> List[Path]:
        """
        Collect files for validation.

        Args:
            language: Single language to collect files for
            languages: Multiple languages to collect files for
            incremental: If True, collect only changed files (requires git)
            staged_only: If True, collect only staged files (requires git and incremental=True)

        Returns:
            List of file paths to validate

        Raises:
            ValueError: If language is unknown
        """
        # Determine which languages to collect
        target_languages = self._resolve_languages(language, languages)

        # Collect files based on mode
        if incremental:
            return self._collect_incremental(target_languages, staged_only)
        else:
            return self._collect_full(target_languages)

    def _resolve_languages(
        self, language: Optional[str], languages: Optional[List[str]]
    ) -> List[str]:
        """
        Resolve which languages to collect files for.

        Args:
            language: Single language
            languages: Multiple languages

        Returns:
            List of language names

        Raises:
            ValueError: If unknown language specified
        """
        if language and languages:
            raise ValueError("Cannot specify both 'language' and 'languages'")

        if language:
            target_languages = [language]
        elif languages:
            target_languages = languages
        else:
            # Auto-detect all languages
            target_languages = self.detector.detect_languages()

        # Validate languages
        known_languages = {"python", "cpp"}
        for lang in target_languages:
            if lang not in known_languages:
                raise ValueError(f"Unknown language: {lang}")

        return target_languages

    def _collect_full(self, languages: List[str]) -> List[Path]:
        """
        Collect all files for specified languages.

        Args:
            languages: Languages to collect files for

        Returns:
            List of all files
        """
        all_files: Set[Path] = set()

        for lang in languages:
            files = self.detector.get_files_for_language(lang)
            all_files.update(files)

        return sorted(all_files)

    def _collect_incremental(self, languages: List[str], staged_only: bool) -> List[Path]:
        """
        Collect only changed files for specified languages.

        Args:
            languages: Languages to collect files for
            staged_only: If True, only collect staged files

        Returns:
            List of changed files
        """
        # Fall back to full mode if not a git repository
        if not self.is_git_repository():
            return self._collect_full(languages)

        # Get changed files from git
        try:
            changed_files = self._get_git_changed_files(staged_only)
        except GitError:
            # Fall back to full mode on error
            return self._collect_full(languages)

        # Filter by language
        filtered_files: Set[Path] = set()

        for file_path in changed_files:
            # Check if file matches any of the target languages
            for lang in languages:
                lang_files = self.detector.get_files_for_language(lang)
                if file_path in lang_files:
                    filtered_files.add(file_path)
                    break

        return sorted(filtered_files)

    def _get_git_changed_files(self, staged_only: bool) -> Set[Path]:
        """
        Get changed files from git.

        Args:
            staged_only: If True, only get staged files

        Returns:
            Set of changed file paths

        Raises:
            GitError: If git command fails
        """
        try:
            if staged_only:
                # Get only staged files
                result = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
            else:
                # Get both staged and unstaged modifications, plus untracked files
                # First get modified/staged files
                result1 = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=ACMR"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )

                result2 = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )

                # Get untracked files
                result3 = subprocess.run(
                    ["git", "ls-files", "--others", "--exclude-standard"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )

                result = type(
                    "Result",
                    (),
                    {"stdout": result1.stdout + result2.stdout + result3.stdout},
                )()

            # Parse output
            changed_files: Set[Path] = set()
            for line in result.stdout.strip().split("\n"):
                if line:
                    file_path = self.root_dir / line
                    # Only include files that exist (exclude deleted files)
                    if file_path.exists() and file_path.is_file():
                        changed_files.add(file_path)

            return changed_files

        except subprocess.CalledProcessError as e:
            raise GitError(f"Git command failed: {e}")
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")

    def get_changed_files_since_commit(self, commit_ref: str = "HEAD~1") -> List[Path]:
        """
        Get files changed since a specific commit.

        Args:
            commit_ref: Git commit reference (default: HEAD~1)

        Returns:
            List of changed file paths

        Raises:
            GitError: If not a git repository or commit ref is invalid
        """
        if not self.is_git_repository():
            raise GitError("Not a git repository")

        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=ACMR", commit_ref],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            changed_files: List[Path] = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    file_path = self.root_dir / line
                    if file_path.exists() and file_path.is_file():
                        changed_files.append(file_path)

            return sorted(changed_files)

        except subprocess.CalledProcessError as e:
            raise GitError(f"Invalid commit reference or git error: {e}")
        except subprocess.TimeoutExpired:
            raise GitError("Git command timed out")
