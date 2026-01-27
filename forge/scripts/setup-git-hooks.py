#!/usr/bin/env python
"""
Setup script to install the pre-commit hook for Forge project.

This script copies the pre-commit check script to the git hooks directory
and makes it executable.

Usage:
    python scripts/setup-git-hooks.py
"""

from pathlib import Path
import shutil
import stat


def main():
    """Install the pre-commit hook."""
    # Get paths
    repo_root = Path(__file__).parent.parent
    source_script = repo_root / "scripts" / "pre-commit-check.py"
    hooks_dir = repo_root / ".git" / "hooks"
    target_hook = hooks_dir / "pre-commit"

    # Ensure hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy the script
    print("Installing pre-commit hook...")
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
    import platform

    if platform.system() == "Windows":
        bat_wrapper = hooks_dir / "pre-commit.bat"
        bat_content = (
            "@echo off\n"
            "REM Pre-commit hook wrapper for Windows\n"
            "REM Calls the Python pre-commit check script\n\n"
            'python "%~dp0pre-commit"\n'
            "exit /b %ERRORLEVEL%\n"
        )
        bat_wrapper.write_text(bat_content)
        print(f"  Windows wrapper: {bat_wrapper}")

    print()
    print("✓ Pre-commit hook installed successfully!")
    print("\nThe hook will now run automatically before each commit to check:")
    print("  - Syntax errors (flake8)")
    print("  - Code style (flake8)")
    print("  - Code formatting (black)")
    print("\nTo bypass the hook for a specific commit, use: git commit --no-verify")


if __name__ == "__main__":
    main()
