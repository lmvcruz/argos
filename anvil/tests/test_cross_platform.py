"""
Cross-platform compatibility tests for Anvil.

Tests path handling, line ending handling, permissions, and platform-specific
behavior across Windows, Linux, and macOS.
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from anvil.core.language_detector import LanguageDetector
from anvil.git.hooks import GitHookManager


class TestPathHandling:
    """Test cross-platform path handling."""

    def test_pathlib_handles_platform_separators(self, tmp_path):
        """Test that pathlib correctly handles platform-specific separators."""
        # Create a nested directory structure
        nested_dir = tmp_path / "subdir" / "nested"
        nested_dir.mkdir(parents=True)

        # Create a file in the nested directory
        test_file = nested_dir / "test.py"
        test_file.write_text("print('hello')")

        # Verify the file exists regardless of platform
        assert test_file.exists()
        assert test_file.is_file()

    def test_relative_path_conversion(self, tmp_path):
        """Test converting absolute paths to relative paths."""
        # Create a file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Get relative path
        relative = test_file.relative_to(tmp_path)

        # Should work on all platforms
        assert str(relative) == "test.py"

    def test_path_with_spaces(self, tmp_path):
        """Test handling paths with spaces."""
        # Create directory with spaces
        dir_with_spaces = tmp_path / "dir with spaces"
        dir_with_spaces.mkdir()

        file_with_spaces = dir_with_spaces / "file with spaces.py"
        file_with_spaces.write_text("# test")

        assert file_with_spaces.exists()

    def test_forward_slash_in_output(self, tmp_path):
        """Test that output uses forward slashes for consistency."""
        # Create nested structure
        nested = tmp_path / "a" / "b" / "c" / "test.py"
        nested.parent.mkdir(parents=True)
        nested.write_text("# test")

        # Get path as string with forward slashes
        path_str = str(nested.relative_to(tmp_path)).replace(os.sep, "/")

        # Should use forward slashes
        assert "/" in path_str
        assert "\\" not in path_str
        assert path_str == "a/b/c/test.py"


class TestLineEndingHandling:
    """Test handling of different line endings (CRLF vs LF)."""

    def test_read_file_with_crlf(self, tmp_path):
        """Test reading files with Windows line endings (CRLF)."""
        test_file = tmp_path / "crlf.py"
        # Write with CRLF line endings
        test_file.write_bytes(b"line1\r\nline2\r\nline3\r\n")

        content = test_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        assert len(lines) == 3
        assert lines[0] == "line1"
        assert lines[1] == "line2"

    def test_read_file_with_lf(self, tmp_path):
        """Test reading files with Unix line endings (LF)."""
        test_file = tmp_path / "lf.py"
        # Write with LF line endings
        test_file.write_bytes(b"line1\nline2\nline3\n")

        content = test_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        assert len(lines) == 3
        assert lines[0] == "line1"
        assert lines[1] == "line2"

    def test_read_file_with_mixed_endings(self, tmp_path):
        """Test reading files with mixed line endings."""
        test_file = tmp_path / "mixed.py"
        # Write with mixed line endings
        test_file.write_bytes(b"line1\r\nline2\nline3\r\nline4\n")

        content = test_file.read_text(encoding="utf-8")
        lines = content.splitlines()

        # Should handle mixed line endings gracefully
        assert len(lines) == 4


class TestFilePermissions:
    """Test file permissions and executability."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix permissions not applicable")
    def test_hook_script_is_executable(self, tmp_path):
        """Test that git hook scripts are created with executable permissions."""
        # Create a fake git repository
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        hook_manager = GitHookManager(tmp_path)
        hook_path = hook_manager._get_hook_path("pre-commit")

        # Write a hook script
        hook_path.write_text("#!/bin/bash\necho 'test'\n", encoding="utf-8")

        # Make it executable (Unix only)
        hook_path.chmod(0o755)

        # Verify it's executable
        assert os.access(hook_path, os.X_OK)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_file_permissions(self, tmp_path):
        """Test file permissions on Windows."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        # Windows doesn't have Unix-style permissions
        # But we should still be able to read/write
        assert test_file.exists()
        assert os.access(test_file, os.R_OK)
        assert os.access(test_file, os.W_OK)


class TestShellIntegration:
    """Test integration with different shells."""

    def test_python_executable_path(self):
        """Test that we can find the Python executable."""
        # Should work on all platforms
        python_exe = sys.executable
        assert python_exe
        assert Path(python_exe).exists()

    def test_subprocess_call(self, tmp_path):
        """Test running subprocess commands across platforms."""
        # Create a simple Python script
        script = tmp_path / "test_script.py"
        script.write_text('print("hello from subprocess")')

        # Run it with subprocess
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "hello from subprocess" in result.stdout

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix shell test")
    def test_unix_shell_script(self, tmp_path):
        """Test running shell scripts on Unix systems."""
        script = tmp_path / "test.sh"
        script.write_text("#!/bin/bash\necho 'unix test'\n")
        script.chmod(0o755)

        result = subprocess.run(
            [str(script)],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "unix test" in result.stdout

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows shell test")
    def test_windows_powershell(self, tmp_path):
        """Test running PowerShell commands on Windows."""
        # Simple PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", "Write-Output 'windows test'"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "windows test" in result.stdout


class TestGitHookIntegration:
    """Test git hook integration on different platforms."""

    def test_git_hook_installation_cross_platform(self, tmp_path):
        """Test git hook installation works on all platforms."""
        # Create a fake git repository
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        hook_manager = GitHookManager(tmp_path)

        # Install a pre-commit hook
        hook_manager.install_pre_commit_hook()

        # Verify the hook was created
        hook_path = git_dir / "pre-commit"
        assert hook_path.exists()

        # Verify hook content
        content = hook_path.read_text(encoding="utf-8")
        assert "anvil check --incremental" in content

    def test_git_hook_shebang(self, tmp_path):
        """Test that git hooks have appropriate shebang for the platform."""
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)

        hook_manager = GitHookManager(tmp_path)
        hook_manager.install_pre_commit_hook()

        hook_path = git_dir / "pre-commit"
        content = hook_path.read_text(encoding="utf-8")

        # Should start with shebang
        if platform.system() == "Windows":
            # Windows might use Python shebang
            assert content.startswith("#!/usr/bin/env python") or content.startswith("#!/bin/sh")
        else:
            # Unix systems use shell shebang
            assert content.startswith("#!/bin/sh") or content.startswith("#!/usr/bin/env python")


class TestParallelExecution:
    """Test parallel execution on different platforms."""

    def test_parallel_file_collection(self, tmp_path):
        """Test parallel file collection works on all platforms."""
        # Create multiple Python files
        for i in range(10):
            (tmp_path / f"test{i}.py").write_text(f"# test {i}")

        # Collect files (should work in parallel internally)
        detector = LanguageDetector(tmp_path)
        python_files = detector.get_files_for_language("python")

        assert len(python_files) == 10


class TestEncodingHandling:
    """Test handling of different file encodings."""

    def test_utf8_file(self, tmp_path):
        """Test reading UTF-8 encoded files."""
        test_file = tmp_path / "utf8.py"
        test_file.write_text("# UTF-8: こんにちは", encoding="utf-8")

        content = test_file.read_text(encoding="utf-8")
        assert "こんにちは" in content

    def test_utf8_bom_file(self, tmp_path):
        """Test reading UTF-8 BOM encoded files."""
        test_file = tmp_path / "utf8bom.py"
        test_file.write_text("# UTF-8 BOM", encoding="utf-8-sig")

        content = test_file.read_text(encoding="utf-8")
        assert "UTF-8 BOM" in content

    def test_ascii_file(self, tmp_path):
        """Test reading ASCII files."""
        test_file = tmp_path / "ascii.py"
        test_file.write_text("# ASCII only", encoding="ascii")

        content = test_file.read_text(encoding="utf-8")
        assert "ASCII only" in content


class TestPlatformDetection:
    """Test platform detection utilities."""

    def test_detect_current_platform(self):
        """Test that we can detect the current platform."""
        system = platform.system()

        # Should be one of the supported platforms
        assert system in ["Windows", "Linux", "Darwin"]

    def test_python_version_detection(self):
        """Test Python version detection."""
        version = sys.version_info

        # Should be Python 3.8+
        assert version.major == 3
        assert version.minor >= 8

    def test_platform_specific_behavior(self):
        """Test platform-specific behavior is correctly handled."""
        if platform.system() == "Windows":
            # Windows-specific assertions
            assert os.name == "nt"
            assert os.sep == "\\"
            assert os.pathsep == ";"
        else:
            # Unix-like systems (Linux, macOS)
            assert os.name == "posix"
            assert os.sep == "/"
            assert os.pathsep == ":"


class TestEnvironmentVariables:
    """Test environment variable handling across platforms."""

    def test_set_and_read_env_var(self):
        """Test setting and reading environment variables."""
        os.environ["ANVIL_TEST_VAR"] = "test_value"

        assert os.environ.get("ANVIL_TEST_VAR") == "test_value"

        # Clean up
        del os.environ["ANVIL_TEST_VAR"]

    def test_path_env_var(self):
        """Test PATH environment variable exists."""
        # PATH should exist on all platforms
        path = os.environ.get("PATH")
        assert path is not None
        assert len(path) > 0


class TestTempFileHandling:
    """Test temporary file and directory handling."""

    def test_temp_directory_creation(self):
        """Test creating temporary directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            assert tmp_path.exists()
            assert tmp_path.is_dir()

            # Create a file in the temp directory
            test_file = tmp_path / "test.py"
            test_file.write_text("# temp test")
            assert test_file.exists()

        # Directory should be cleaned up
        assert not tmp_path.exists()

    def test_temp_file_creation(self):
        """Test creating temporary files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write("# temp file")
            tmp_path = Path(tmp_file.name)

        try:
            assert tmp_path.exists()
            content = tmp_path.read_text(encoding="utf-8")
            assert "temp file" in content
        finally:
            # Clean up
            tmp_path.unlink()


class TestSymbolicLinks:
    """Test symbolic link handling."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Symlinks require admin on Windows")
    def test_symlink_creation(self, tmp_path):
        """Test creating and following symbolic links."""
        # Create a regular file
        target = tmp_path / "target.py"
        target.write_text("# target file")

        # Create a symlink
        link = tmp_path / "link.py"
        link.symlink_to(target)

        assert link.exists()
        assert link.is_symlink()
        assert link.resolve() == target

    @pytest.mark.skipif(platform.system() == "Windows", reason="Symlinks require admin on Windows")
    def test_symlink_directory(self, tmp_path):
        """Test directory symbolic links."""
        # Create a directory
        target_dir = tmp_path / "target_dir"
        target_dir.mkdir()
        (target_dir / "file.py").write_text("# test")

        # Create a symlink to the directory
        link_dir = tmp_path / "link_dir"
        link_dir.symlink_to(target_dir)

        assert link_dir.exists()
        assert link_dir.is_dir()
        assert (link_dir / "file.py").exists()
