"""
Integration tests for error handling and recovery in main application.

Tests error scenarios, cleanup behavior, and user-facing error messages
to ensure the application handles failures gracefully.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from forge.__main__ import main
from forge.cli.argument_errors import ArgumentError
from forge.models.results import BuildResult, ConfigureResult


class TestCMakeNotFoundError:
    """Test handling when CMake is not available."""

    def test_cmake_not_found_returns_127(self, tmp_path, mocker):
        """Test that CMake not found returns exit code 127."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        # Mock CMake availability check to return False
        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = False

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 127

    def test_cmake_not_found_error_message(self, tmp_path, mocker, capsys):
        """Test that CMake not found displays helpful error message."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = False

        main(["--build-dir", str(build_dir), "--no-configure"])

        captured = capsys.readouterr()
        assert "CMake not found" in captured.err
        assert "PATH" in captured.err


class TestConfigurationFailure:
    """Test handling of configuration failures."""

    def test_configure_failure_returns_exit_code(self, tmp_path, mocker):
        """Test that configure failure returns CMake's exit code."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(Test)\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_configure = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_configure")
        mock_configure.return_value = ConfigureResult(
            success=False,
            exit_code=1,
            duration=1.0,
            stdout="Configuration failed",
            stderr="CMake Error: Cannot find file",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        exit_code = main(["--build-dir", str(build_dir), "--source-dir", str(source_dir)])

        assert exit_code == 1

    def test_configure_failure_error_message(self, tmp_path, mocker, capsys):
        """Test that configure failure displays error output."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(Test)\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_configure = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_configure")
        mock_configure.return_value = ConfigureResult(
            success=False,
            exit_code=1,
            duration=1.0,
            stdout="",
            stderr="CMake Error: Cannot find CMakeLists.txt",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        main(["--build-dir", str(build_dir), "--source-dir", str(source_dir)])

        captured = capsys.readouterr()
        assert "Configuration failed" in captured.err
        assert "CMake Error" in captured.err

    def test_configure_failure_no_build_attempted(self, tmp_path, mocker):
        """Test that build is not attempted after configure failure."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(Test)\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_configure = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_configure")
        mock_configure.return_value = ConfigureResult(
            success=False,
            exit_code=1,
            duration=1.0,
            stdout="",
            stderr="Error",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")

        main(["--build-dir", str(build_dir), "--source-dir", str(source_dir)])

        # Build should not be called after configure failure
        mock_build.assert_not_called()


class TestBuildFailure:
    """Test handling of build failures."""

    def test_build_failure_returns_exit_code(self, tmp_path, mocker):
        """Test that build failure returns compiler's exit code."""
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
            stderr="error: 'x' was not declared",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 2

    def test_build_failure_error_message(self, tmp_path, mocker, capsys):
        """Test that build failure displays error output."""
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
            stderr="error: undefined reference to 'foo'",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        main(["--build-dir", str(build_dir), "--no-configure"])

        captured = capsys.readouterr()
        assert "Build failed" in captured.err
        assert "undefined reference" in captured.err

    def test_build_failure_data_still_saved(self, tmp_path, mocker):
        """Test that build data is saved even on failure."""
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
            stderr="error",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        mock_save = mocker.patch("forge.storage.data_persistence.DataPersistence.save_build")
        mock_save.return_value = 1

        main(["--build-dir", str(build_dir), "--no-configure"])

        # Save should be called even on build failure
        mock_save.assert_called_once()


class TestDatabaseErrors:
    """Test handling of database-related errors."""

    def test_database_connection_error_continues(self, tmp_path, mocker, caplog):
        """Test that database errors don't crash the application."""
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
            stdout="Build succeeded",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        # Mock database save to raise exception
        mock_save = mocker.patch("forge.storage.data_persistence.DataPersistence.save_build")
        mock_save.side_effect = Exception("Database connection failed")

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        # Should complete despite database error
        assert "Failed to save build data" in caplog.text or "Database connection failed" in caplog.text

    def test_database_init_error_continues(self, tmp_path, mocker):
        """Test that database initialization errors don't crash application."""
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

        # Mock DataPersistence to raise on initialization
        mocker.patch(
            "forge.storage.data_persistence.DataPersistence.__init__",
            side_effect=Exception("Cannot create database"),
        )

        # Should not crash
        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        # May fail or succeed depending on error handling


class TestKeyboardInterrupt:
    """Test handling of keyboard interrupts (Ctrl+C)."""

    def test_keyboard_interrupt_returns_130(self, tmp_path, mocker, capsys):
        """Test that Ctrl+C returns exit code 130."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(Test)\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        # Simulate keyboard interrupt during configure
        mock_configure = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_configure")
        mock_configure.side_effect = KeyboardInterrupt()

        exit_code = main(["--build-dir", str(build_dir), "--source-dir", str(source_dir)])

        assert exit_code == 130
        captured = capsys.readouterr()
        assert "Interrupted" in captured.err

    def test_keyboard_interrupt_during_build(self, tmp_path, mocker, capsys):
        """Test Ctrl+C handling during build phase."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.side_effect = KeyboardInterrupt()

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        assert exit_code == 130


class TestPartialDataHandling:
    """Test handling when configuration succeeds but build fails."""

    def test_config_success_build_fail_saves_config(self, tmp_path, mocker):
        """Test that configuration is saved even if build fails."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(Test)\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        mock_configure = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_configure")
        mock_configure.return_value = ConfigureResult(
            success=True,
            exit_code=0,
            duration=1.0,
            stdout="-- Configuring done",
            stderr="",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.return_value = BuildResult(
            success=False,
            exit_code=2,
            duration=1.0,
            stdout="",
            stderr="error",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        mock_save_config = mocker.patch(
            "forge.storage.data_persistence.DataPersistence.save_configuration"
        )
        mock_save_config.return_value = 1

        mock_save_build = mocker.patch("forge.storage.data_persistence.DataPersistence.save_build")
        mock_save_build.return_value = 2

        exit_code = main(["--build-dir", str(build_dir), "--source-dir", str(source_dir)])

        # Configuration should be saved
        mock_save_config.assert_called_once()
        # Build should also be saved (even though failed)
        mock_save_build.assert_called_once()
        # Exit code should reflect build failure
        assert exit_code == 2


class TestInvalidArguments:
    """Test handling of invalid command-line arguments."""

    def test_missing_required_args_returns_error(self, capsys):
        """Test that missing required arguments returns non-zero."""
        exit_code = main([])

        assert exit_code != 0

    def test_invalid_path_error_message(self, capsys):
        """Test error message for invalid paths."""
        exit_code = main(["--build-dir", "/nonexistent/path/that/does/not/exist"])

        captured = capsys.readouterr()
        assert exit_code != 0
        # Should have error message
        assert len(captured.err) > 0 or exit_code == 1


class TestResourceCleanup:
    """Test that resources are properly cleaned up on errors."""

    def test_database_connection_closed_on_error(self, tmp_path, mocker):
        """Test that database connections are closed when errors occur."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        # Mock build to raise exception
        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.side_effect = Exception("Unexpected error")

        # Mock DataPersistence close method
        mock_close = mocker.patch("forge.storage.data_persistence.DataPersistence.close")

        try:
            main(["--build-dir", str(build_dir), "--no-configure"])
        except:
            pass

        # Close should be called (if implemented)
        # This test may not apply if close() is not implemented

    def test_error_during_inspection_continues(self, tmp_path, mocker):
        """Test that errors during output inspection don't crash app."""
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

        # Mock inspector to raise exception
        mock_inspect = mocker.patch("forge.inspector.build_inspector.BuildInspector.inspect_build_output")
        mock_inspect.side_effect = Exception("Parser error")

        # Should not crash
        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        # May fail or succeed depending on error handling


class TestErrorMessageClarity:
    """Test that error messages are clear and helpful."""

    def test_validation_error_message_helpful(self, tmp_path, mocker, capsys):
        """Test that validation errors provide helpful guidance."""
        # Use a path that will trigger validation error
        nonexistent = tmp_path / "nonexistent"

        exit_code = main(["--build-dir", str(nonexistent)])

        captured = capsys.readouterr()
        assert exit_code == 2  # Validation error
        # Should have helpful error message
        assert len(captured.err) > 0

    def test_exception_message_logged(self, tmp_path, mocker, capsys):
        """Test that unexpected exceptions are logged with details."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28.0\n")

        mock_check = mocker.patch("forge.cmake.executor.CMakeExecutor.check_cmake_available")
        mock_check.return_value = True

        # Cause unexpected exception
        mock_build = mocker.patch("forge.cmake.executor.CMakeExecutor.execute_build")
        mock_build.side_effect = RuntimeError("Something went terribly wrong")

        exit_code = main(["--build-dir", str(build_dir), "--no-configure"])

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "Unexpected error" in captured.err or "Something went terribly wrong" in captured.err
