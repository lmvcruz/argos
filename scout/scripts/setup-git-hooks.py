#!/usr/bin/env python
"""
Setup script to install the pre-commit hook for Scout project.

This script copies the pre-commit check script to the git hooks directory
and makes it executable.

Usage:
    python scripts/setup-git-hooks.py
"""

from pathlib import Path
import shutil
import stat
import platform


def main():
    """Install the pre-commit hook."""
    # Scout is in a subdirectory, so go up to repo root
    scout_dir = Path(__file__).parent.parent
    repo_root = scout_dir.parent
    source_script = scout_dir / "scripts" / "pre-commit-check.py"
    hooks_dir = repo_root / ".git" / "hooks"
    target_hook = hooks_dir / "pre-commit"

    # Create hooks directory if it doesn't exist
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy the script
    print("Installing pre-commit hook for Scout...")
    print(f"  Source: {source_script}")
    print(f"  Target: {target_hook}")

    shutil.copy2(source_script, target_hook)

    # Make it executable on Unix-like systems
    try:
        current_permissions = target_hook.stat().st_mode
        target_hook.chmod(current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("  Made executable: Yes")
    except Exception as e:
        print(f"  Made executable: Skipped ({e})")

    # On Windows, also create a .bat wrapper that git will execute
    if platform.system() == "Windows":
        bat_wrapper = hooks_dir / "pre-commit.bat"
        bat_content = (
            "@echo off\n"
            "REM Pre-commit hook wrapper for Windows\n"
            "REM Calls the Python pre-commit check script\n\n"
            f'python "{target_hook}" %*\n'
            "exit /b %ERRORLEVEL%\n"
        )

        bat_wrapper.write_text(bat_content, encoding="utf-8")
        print(f"  Created Windows wrapper: {bat_wrapper}")

    print("\n✅ Pre-commit hook installed successfully!")
    print("\nThe hook will run automatically before each commit.")
    print("To bypass the hook temporarily, use: git commit --no-verify")
    print("\nTo test the hook manually, run:")
    print(f"  python {source_script}")


if __name__ == "__main__":
    main()
