#!/usr/bin/env python3
"""
Setup git hooks for Anvil development.

This script installs pre-commit hooks that automatically run quality checks
before each commit.

Usage:
    python scripts/setup-git-hooks.py
"""

import stat
import sys
from pathlib import Path


def main():
    """Install git pre-commit hook."""
    # Get repository root (anvil directory)
    repo_root = Path(__file__).parent.parent.resolve()

    # Git hooks directory
    git_hooks_dir = repo_root.parent / ".git" / "hooks"

    if not git_hooks_dir.exists():
        print("Error: Not in a git repository")
        print(f"Expected .git directory at: {git_hooks_dir.parent}")
        return 1

    # Pre-commit hook path
    hook_path = git_hooks_dir / "pre-commit"

    # Pre-commit hook script
    hook_content = f"""#!/bin/sh
# Anvil pre-commit hook
# Automatically runs quality checks before commit

echo "Running Anvil pre-commit checks..."
cd "{repo_root}"
python scripts/pre-commit-check.py

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Pre-commit checks failed!"
    echo "Fix the issues and try again, or use 'git commit --no-verify' to bypass."
    exit $EXIT_CODE
fi

exit 0
"""

    # Check if hook already exists
    if hook_path.exists():
        print(f"Pre-commit hook already exists at: {hook_path}")
        response = input("Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Installation cancelled.")
            return 0

    # Write hook file (with UTF-8 encoding for cross-platform compatibility)
    hook_path.write_text(hook_content, encoding="utf-8")

    # Make executable (Unix-like systems)
    if sys.platform != "win32":
        current_permissions = hook_path.stat().st_mode
        hook_path.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"✓ Pre-commit hook installed at: {hook_path}")
    print("\nThe hook will run automatically before each commit.")
    print("To bypass the hook, use: git commit --no-verify")

    return 0


if __name__ == "__main__":
    sys.exit(main())
