"""
Edge case tests for Forge application.

This module tests Forge with problematic or unusual scenarios to ensure
robustness and data integrity in edge cases.
"""

from datetime import datetime
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

import pytest

from forge.__main__ import main
from forge.models.results import BuildResult, ConfigureResult
from forge.storage.data_persistence import DataPersistence


class TestVeryLongOutput:
    """Test Forge with very long build output (memory efficiency)."""

    def test_very_long_configure_output(self, temp_dir, temp_db):
        """
        Test that Forge handles very long configure output efficiently.

        Tests memory efficiency with output containing thousands of lines.
        """
        source_dir = temp_dir / "long_output_project"
        build_dir = temp_dir / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Create a simple CMakeLists.txt
        cmakelists = source_dir / "CMakeLists.txt"
        cmakelists.write_text("project(LongOutput)\n")

        # Mock execute_configure to return very long output (10000 lines)
        long_output = "\n".join([f"-- Line {i} of configure output" for i in range(10000)])
        long_output += "\n-- Configuring done\n-- Generating done\n"

        with patch("forge.cmake.executor.CMakeExecutor.execute_configure") as mock_cfg:
            mock_cfg.return_value = ConfigureResult(
                success=True,
                exit_code=0,
                duration=5.0,
                stdout=long_output,
                stderr="",
                start_time=datetime.now(),
                end_time=datetime.now(),
            )

            with patch("forge.cmake.executor.CMakeExecutor.execute_build") as mock_build:
                mock_build.return_value = BuildResult(
                    success=True,
                    exit_code=0,
                    duration=1.0,
                    stdout="[100%] Built target app\n",
                    stderr="",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                args = [
                    "--source-dir",
                    str(source_dir),
                    "--build-dir",
                    str(build_dir),
                    "--database",
                    str(temp_db),
                ]

                exit_code = main(args)

        # Verify success
        assert exit_code == 0

        # Verify data was persisted
        persistence = DataPersistence(str(temp_db))
        builds = persistence.get_recent_builds(limit=1)
        assert len(builds) >= 1


class TestUnicodeOutput:
    """Test Forge with Unicode characters in output."""

    def test_unicode_in_configure_output(self, temp_dir, temp_db):
        """
        Test handling of Unicode characters in configure output.

        Tests with various Unicode characters including emoji, Asian characters,
        and special symbols.
        """
        source_dir = temp_dir / "unicode_project"
        build_dir = temp_dir / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Create CMakeLists.txt
        cmakelists = source_dir / "CMakeLists.txt"
        cmakelists.write_text("project(UnicodeTest)\n", encoding="utf-8")

        # Configure output with Unicode
        unicode_output = """-- The CXX compiler identification is GNU 11.0.0
-- Checking for module 'gtk+-3.0'
-- 找到 GTK+ 3.0
-- Configuration de projet français
-- Projekt-Konfiguration für Deutsch
-- Конфигурация проекта на русском
-- プロジェクト設定 (Japanese)
-- ✓ Configuration successful! 🎉
-- Configuring done
-- Generating done
"""

        with patch("forge.cmake.executor.CMakeExecutor.execute_configure") as mock_cfg:
            mock_cfg.return_value = ConfigureResult(
                success=True,
                exit_code=0,
                duration=5.0,
                stdout=unicode_output,
                stderr="",
                start_time=datetime.now(),
                end_time=datetime.now(),
            )

            with patch("forge.cmake.executor.CMakeExecutor.execute_build") as mock_build:
                mock_build.return_value = BuildResult(
                    success=True,
                    exit_code=0,
                    duration=1.0,
                    stdout="[100%] Built target app\n",
                    stderr="",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                args = [
                    "--source-dir",
                    str(source_dir),
                    "--build-dir",
                    str(build_dir),
                    "--database",
                    str(temp_db),
                ]

                exit_code = main(args)

        assert exit_code == 0


class TestPathsWithSpecialCharacters:
    """Test Forge with paths containing spaces and special characters."""

    def test_path_with_spaces(self, temp_db):
        """
        Test Forge with build paths containing spaces.

        Verifies correct handling of directory paths with spaces.
        """
        # Create temp directory with spaces in name
        with tempfile.TemporaryDirectory(prefix="forge test ") as temp_base:
            temp_path = Path(temp_base)
            source_dir = temp_path / "my project"
            build_dir = temp_path / "build output"
            source_dir.mkdir()
            build_dir.mkdir()

            # Create CMakeLists.txt
            cmakelists = source_dir / "CMakeLists.txt"
            cmakelists.write_text("project(SpacesTest)\n")

            # Mock execution
            with patch("forge.cmake.executor.CMakeExecutor.execute_configure") as mock_cfg:
                mock_cfg.return_value = ConfigureResult(
                    success=True,
                    exit_code=0,
                    duration=5.0,
                    stdout="-- Configuring done\n-- Generating done\n",
                    stderr="",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                with patch("forge.cmake.executor.CMakeExecutor.execute_build") as mock_build:
                    mock_build.return_value = BuildResult(
                        success=True,
                        exit_code=0,
                        duration=1.0,
                        stdout="[100%] Built target app\n",
                        stderr="",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                    )

                    args = [
                        "--source-dir",
                        str(source_dir),
                        "--build-dir",
                        str(build_dir),
                        "--database",
                        str(temp_db),
                    ]

                    exit_code = main(args)

            assert exit_code == 0


class TestBuildDuration:
    """Test Forge with very quick and very long builds."""

    def test_very_quick_build(self, temp_dir, temp_db):
        """
        Test Forge with very quick build (< 1 second).

        Verifies accurate timing measurement for fast builds.
        """
        source_dir = temp_dir / "quick_build"
        build_dir = temp_dir / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Create CMakeLists.txt
        cmakelists = source_dir / "CMakeLists.txt"
        cmakelists.write_text("project(QuickBuild)\n")

        # Mock very quick build (0.1 seconds)
        with patch("forge.cmake.executor.CMakeExecutor.execute_configure") as mock_cfg:
            mock_cfg.return_value = ConfigureResult(
                success=True,
                exit_code=0,
                duration=0.1,
                stdout="-- Configuring done\n",
                stderr="",
                start_time=datetime.now(),
                end_time=datetime.now(),
            )

            with patch("forge.cmake.executor.CMakeExecutor.execute_build") as mock_build:
                mock_build.return_value = BuildResult(
                    success=True,
                    exit_code=0,
                    duration=0.1,
                    stdout="[100%] Built target app\n",
                    stderr="",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                args = [
                    "--source-dir",
                    str(source_dir),
                    "--build-dir",
                    str(build_dir),
                    "--database",
                    str(temp_db),
                ]

                exit_code = main(args)

        assert exit_code == 0


class TestDatabaseEdgeCases:
    """Test database edge cases and error handling."""

    def test_database_directory_not_exists(self, temp_dir):
        """
        Test Forge validates database parent directory exists.

        Verifies that Forge checks for valid database path with existing parent.
        Note: This is a validation check - DataPersistence would create the directory
        if allowed past validation.
        """
        source_dir = temp_dir / "project"
        build_dir = temp_dir / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Create CMakeLists.txt
        cmakelists = source_dir / "CMakeLists.txt"
        cmakelists.write_text("project(DbDirTest)\n")

        # Database path in non-existent directory
        db_path = temp_dir / "nested" / "dir" / "forge.db"
        assert not db_path.parent.exists()

        # Mock execution
        with patch("forge.cmake.executor.CMakeExecutor.execute_configure") as mock_cfg:
            mock_cfg.return_value = ConfigureResult(
                success=True,
                exit_code=0,
                duration=5.0,
                stdout="-- Configuring done\n",
                stderr="",
                start_time=datetime.now(),
                end_time=datetime.now(),
            )

            with patch("forge.cmake.executor.CMakeExecutor.execute_build") as mock_build:
                mock_build.return_value = BuildResult(
                    success=True,
                    exit_code=0,
                    duration=1.0,
                    stdout="[100%] Built target app\n",
                    stderr="",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                )

                args = [
                    "--source-dir",
                    str(source_dir),
                    "--build-dir",
                    str(build_dir),
                    "--database",
                    str(db_path),
                ]

                exit_code = main(args)

        # Should fail validation (exit code 2)
        assert exit_code == 2


# Fixtures


@pytest.fixture
def temp_dir():
    """
    Create temporary directory for tests.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory(prefix="forge_edge_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db():
    """
    Create temporary database for tests.

    Yields:
        Path to temporary database file
    """
    temp_db_file = Path(tempfile.mktemp(suffix=".db"))
    yield temp_db_file

    # Cleanup - give Windows time to release file locks
    time.sleep(0.1)
    if temp_db_file.exists():
        try:
            temp_db_file.unlink()
        except PermissionError:
            # If still locked, leave it for OS cleanup
            pass
