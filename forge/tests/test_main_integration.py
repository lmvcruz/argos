"""
Integration tests for main application entry point.

Tests the complete application workflow from command line to database,
integrating all components: argument parsing, CMake execution, output
inspection, and data persistence.
"""

from datetime import datetime
from pathlib import Path

import pytest

from forge.__main__ import main
from forge.models.results import BuildResult, ConfigureResult


class TestBasicWorkflow:
    """Test basic workflow functionality."""

    def test_build_only_workflow(self, tmp_path, mocker):
        """Test build-only mode using --no-configure flag."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Create CMakeCache.txt to indicate pre-configured project
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        # Mock CMake availability check
        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        # Mock build execution
        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")

        mock_build.return_value = BuildResult(
            success=True,
            exit_code=0,
            duration=2.5,
            stdout="Build output",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        # Execute with --no-configure
        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 0
        mock_build.assert_called_once()

    def test_invalid_arguments_returns_error(self):
        """Test that missing required arguments causes error."""
        exit_code = main([])
        assert exit_code != 0

    def test_cmake_not_found_returns_error(self, tmp_path, mocker):
        """Test behavior when CMake is not found."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = False

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        # Should return error when CMake not found
        assert exit_code != 0


class TestExitCodes:
    """Test exit code propagation."""

    def test_successful_build_returns_zero(self, tmp_path, mocker):
        """Test that successful build returns exit code 0."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.return_value = BuildResult(
            success=True,
            exit_code=0,
            duration=1.0,
            stdout="",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 0

    def test_failed_build_returns_nonzero(self, tmp_path, mocker):
        """Test that failed build returns non-zero exit code."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.return_value = BuildResult(
            success=False,
            exit_code=2,
            duration=1.0,
            stdout="",
            stderr="Build failed",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 2


class TestVerboseMode:
    """Test verbose output mode."""

    def test_verbose_mode_works(self, tmp_path, mocker):
        """Test that verbose mode can be enabled."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.return_value = BuildResult(
            success=True,
            exit_code=0,
            duration=1.0,
            stdout="Build output",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        exit_code = main(["--build-dir", str(build_dir), "--no-configure", "--verbose"])

        assert exit_code == 0
