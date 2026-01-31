"""
Git hook installation and management for Anvil.

Provides functionality to install, uninstall, and manage git hooks
that integrate Anvil validation into git workflows.
"""

import stat
from pathlib import Path
from typing import List


class GitHookError(Exception):
    """Exception raised for git hook operations."""


class GitHookManager:
    """
    Manage git hooks for Anvil validation.

    Handles installation, uninstallation, and configuration of pre-commit
    and pre-push hooks that run Anvil validation checks.

    Args:
        repo_path: Path to the git repository

    Raises:
        GitHookError: If operations fail or repository is invalid
    """

    HOOK_TYPES = ["pre-commit", "pre-push"]
    BYPASS_KEYWORDS = ["[skip-anvil]", "[skip anvil]", "SKIP_ANVIL"]

    def __init__(self, repo_path: Path):
        """
        Initialize GitHookManager for a repository.

        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = Path(repo_path)
        self.hooks_dir = self.repo_path / ".git" / "hooks"

    def is_git_repository(self) -> bool:
        """
        Check if the path is a valid git repository.

        Returns:
            True if path is a git repository, False otherwise
        """
        git_dir = self.repo_path / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def _validate_repository(self) -> None:
        """
        Validate that the path is a git repository.

        Raises:
            GitHookError: If path is not a git repository
        """
        if not self.is_git_repository():
            raise GitHookError(
                f"'{self.repo_path}' is not a git repository. " "Initialize with 'git init' first."
            )

    def _generate_hook_script(self, hook_type: str) -> str:
        """
        Generate the hook script content.

        Args:
            hook_type: Type of hook ('pre-commit' or 'pre-push')

        Returns:
            Hook script content as string
        """
        if hook_type == "pre-commit":
            script = """#!/bin/sh
# Anvil pre-commit hook
# This hook runs Anvil validation before allowing commits

# Check for bypass keywords in commit message
if [ -n "$ANVIL_SKIP" ] || \\
    git log -1 --pretty=%B 2>/dev/null | grep -qE '\\[skip[- ]anvil\\]|SKIP_ANVIL'; then
    echo "Anvil validation skipped (bypass keyword detected)"
    exit 0
fi

# Run Anvil incremental validation
echo "Running Anvil validation..."

# Try direct command first, fall back to Python module
if command -v anvil >/dev/null 2>&1; then
    anvil check --incremental
    exit $?
else
    python -m anvil check --incremental
    exit $?
fi
"""
        elif hook_type == "pre-push":
            script = """#!/bin/sh
# Anvil pre-push hook
# This hook runs Anvil validation before allowing pushes

# Check for bypass environment variable
if [ -n "$ANVIL_SKIP" ]; then
    echo "Anvil validation skipped (ANVIL_SKIP set)"
    exit 0
fi

# Run Anvil full validation
echo "Running Anvil validation before push..."

# Try direct command first, fall back to Python module
if command -v anvil >/dev/null 2>&1; then
    anvil check
    exit $?
else
    python -m anvil check
    exit $?
fi
"""
        else:
            raise GitHookError(f"Unsupported hook type: {hook_type}")

        return script

    def _make_executable(self, file_path: Path) -> None:
        """
        Make a file executable.

        Args:
            file_path: Path to the file to make executable
        """
        # Add execute permission for owner, group, and others
        current_permissions = file_path.stat().st_mode
        file_path.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def _install_hook(self, hook_type: str, force: bool = False) -> None:
        """
        Install a git hook.

        Args:
            hook_type: Type of hook ('pre-commit' or 'pre-push')
            force: If True, overwrite existing hook

        Raises:
            GitHookError: If hook installation fails
        """
        self._validate_repository()

        if hook_type not in self.HOOK_TYPES:
            raise GitHookError(f"Invalid hook type: {hook_type}")

        hook_path = self.hooks_dir / hook_type

        # Check if hook already exists
        if hook_path.exists() and not force:
            raise GitHookError(
                f"Hook '{hook_type}' already exists at {hook_path}. " "Use force=True to overwrite."
            )

        # Ensure hooks directory exists
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write hook script
        script_content = self._generate_hook_script(hook_type)
        hook_path.write_text(script_content, encoding="utf-8")

        # Make hook executable
        self._make_executable(hook_path)

    def install_pre_commit_hook(self, force: bool = False) -> None:
        """
        Install pre-commit hook.

        Args:
            force: If True, overwrite existing hook

        Raises:
            GitHookError: If installation fails
        """
        self._install_hook("pre-commit", force=force)

    def install_pre_push_hook(self, force: bool = False) -> None:
        """
        Install pre-push hook.

        Args:
            force: If True, overwrite existing hook

        Raises:
            GitHookError: If installation fails
        """
        self._install_hook("pre-push", force=force)

    def _uninstall_hook(self, hook_type: str) -> None:
        """
        Uninstall a git hook.

        Args:
            hook_type: Type of hook ('pre-commit' or 'pre-push')

        Raises:
            GitHookError: If hook uninstallation fails
        """
        self._validate_repository()

        if hook_type not in self.HOOK_TYPES:
            raise GitHookError(f"Invalid hook type: {hook_type}")

        hook_path = self.hooks_dir / hook_type

        if hook_path.exists():
            hook_path.unlink()

    def uninstall_pre_commit_hook(self) -> None:
        """
        Uninstall pre-commit hook.

        Raises:
            GitHookError: If uninstallation fails
        """
        self._uninstall_hook("pre-commit")

    def uninstall_pre_push_hook(self) -> None:
        """
        Uninstall pre-push hook.

        Raises:
            GitHookError: If uninstallation fails
        """
        self._uninstall_hook("pre-push")

    def uninstall_all_hooks(self) -> None:
        """
        Uninstall all Anvil-managed hooks.

        Raises:
            GitHookError: If uninstallation fails
        """
        for hook_type in self.HOOK_TYPES:
            try:
                self._uninstall_hook(hook_type)
            except GitHookError:
                # Continue uninstalling other hooks even if one fails
                pass

    def is_hook_installed(self, hook_type: str) -> bool:
        """
        Check if a specific hook is installed.

        Args:
            hook_type: Type of hook ('pre-commit' or 'pre-push')

        Returns:
            True if hook is installed, False otherwise
        """
        if not self.is_git_repository():
            return False

        hook_path = self.hooks_dir / hook_type
        return hook_path.exists()

    def list_installed_hooks(self) -> List[str]:
        """
        List all installed Anvil hooks.

        Returns:
            List of installed hook types
        """
        if not self.is_git_repository():
            return []

        installed = []
        for hook_type in self.HOOK_TYPES:
            if self.is_hook_installed(hook_type):
                installed.append(hook_type)

        return installed
