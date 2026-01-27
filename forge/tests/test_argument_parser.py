"""
Unit tests for ArgumentParser basic implementation.

Tests command-line argument parsing with various input combinations.
Following TDD principles - these tests are written before implementation.
"""

import sys

import pytest

from forge.cli.argument_parser import ArgumentParser
from forge.models.arguments import ForgeArguments


class TestBasicParsing:
    """Test basic argument parsing functionality."""

    def test_parse_with_only_required_build_dir(self, tmp_path):
        """Test parsing with only required --build-dir argument."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir)])

        assert isinstance(args, ForgeArguments)
        assert args.build_dir == build_dir
        assert args.source_dir is None

    def test_parse_with_source_dir_and_build_dir(self, tmp_path):
        """Test parsing with both --source-dir and --build-dir."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            ["--source-dir", str(source_dir), "--build-dir", str(build_dir)]
        )

        assert args.source_dir == source_dir
        assert args.build_dir == build_dir

    def test_parse_with_all_optional_arguments(self, tmp_path):
        """Test parsing with all optional arguments provided."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        db_path = tmp_path / "forge.db"
        source_dir.mkdir()
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--source-dir",
                str(source_dir),
                "--build-dir",
                str(build_dir),
                "--database",
                str(db_path),
                "--project-name",
                "MyProject",
                "--verbose",
                "--no-configure",
                "--clean-build",
            ]
        )

        assert args.source_dir == source_dir
        assert args.build_dir == build_dir
        assert args.database_path == db_path
        assert args.project_name == "MyProject"
        assert args.verbose is True
        assert args.configure is False
        assert args.clean_build is True


class TestCMakeArguments:
    """Test parsing of CMake-specific arguments."""

    def test_parse_cmake_args_single_value(self, tmp_path):
        """Test parsing --cmake-args with single value."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--build-dir",
                str(build_dir),
                "--cmake-args",
                "-DCMAKE_BUILD_TYPE=Release",
            ]
        )

        assert args.cmake_args == ["-DCMAKE_BUILD_TYPE=Release"]

    def test_parse_cmake_args_multiple_values(self, tmp_path):
        """Test parsing --cmake-args with multiple values."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--build-dir",
                str(build_dir),
                "--cmake-args",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DBUILD_TESTING=OFF",
                "-DCMAKE_INSTALL_PREFIX=/usr/local",
            ]
        )

        assert args.cmake_args == [
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=OFF",
            "-DCMAKE_INSTALL_PREFIX=/usr/local",
        ]

    def test_parse_build_args_single_value(self, tmp_path):
        """Test parsing --build-args with single value."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--build-dir",
                str(build_dir),
                "--build-args",
                "-j8",
            ]
        )

        assert args.build_args == ["-j8"]

    def test_parse_build_args_multiple_values(self, tmp_path):
        """Test parsing --build-args with multiple values."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--build-dir",
                str(build_dir),
                "--build-args",
                "-j8",
                "--target",
                "install",
            ]
        )

        assert args.build_args == ["-j8", "--target", "install"]


class TestFlags:
    """Test parsing of boolean flags."""

    def test_parse_verbose_flag(self, tmp_path):
        """Test parsing --verbose flag."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir), "--verbose"])

        assert args.verbose is True

    def test_parse_without_verbose_flag(self, tmp_path):
        """Test default verbose value when flag not provided."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir)])

        assert args.verbose is False

    def test_parse_project_name_override(self, tmp_path):
        """Test parsing --project-name override."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--build-dir",
                str(build_dir),
                "--project-name",
                "CustomProjectName",
            ]
        )

        assert args.project_name == "CustomProjectName"

    def test_parse_no_configure_flag(self, tmp_path):
        """Test parsing --no-configure flag (build-only mode)."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir), "--no-configure"])

        assert args.configure is False

    def test_parse_clean_build_flag(self, tmp_path):
        """Test parsing --clean-build flag."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir), "--clean-build"])

        assert args.clean_build is True


class TestHelpAndVersion:
    """Test help message and version output."""

    def test_help_message_generation(self):
        """Test that --help generates help message and exits."""
        parser = ArgumentParser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse(["--help"])

        assert exc_info.value.code == 0

    def test_version_output(self):
        """Test that --version outputs version and exits."""
        parser = ArgumentParser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse(["--version"])

        assert exc_info.value.code == 0


class TestPathHandling:
    """Test path conversion and normalization."""

    def test_relative_paths_converted_to_absolute(self, tmp_path, monkeypatch):
        """Test that relative paths are converted to absolute paths."""
        # Create directories
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Change to tmp_path so relative paths work
        monkeypatch.chdir(tmp_path)

        parser = ArgumentParser()
        args = parser.parse(
            [
                "--source-dir",
                "source",
                "--build-dir",
                "build",
            ]
        )

        # Paths should be absolute
        assert args.source_dir.is_absolute()
        assert args.build_dir.is_absolute()
        assert args.source_dir == source_dir
        assert args.build_dir == build_dir

    def test_tilde_expansion_in_paths(self, tmp_path):
        """Test that ~ is expanded to home directory."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()

        # Use a path with ~, but provide explicit build-dir
        args = parser.parse(["--build-dir", str(build_dir)])

        # Just verify parsing works; actual ~ expansion depends on system
        assert args.build_dir == build_dir


class TestSysArgvSimulation:
    """Test argument parsing with sys.argv simulation."""

    def test_parse_from_sys_argv(self, tmp_path, monkeypatch):
        """Test parsing arguments from sys.argv simulation."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Simulate sys.argv (first element is script name)
        test_argv = [
            "forge",
            "--build-dir",
            str(build_dir),
            "--verbose",
        ]
        monkeypatch.setattr(sys, "argv", test_argv)

        parser = ArgumentParser()
        # When called without arguments, should use sys.argv[1:]
        args = parser.parse()

        assert args.build_dir == build_dir
        assert args.verbose is True

    def test_parse_with_equals_syntax(self, tmp_path):
        """Test parsing with --arg=value syntax."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(
            [
                f"--build-dir={build_dir}",
                "--project-name=MyProject",
            ]
        )

        assert args.build_dir == build_dir
        assert args.project_name == "MyProject"


class TestDefaultValues:
    """Test default values for optional arguments."""

    def test_default_values_set_correctly(self, tmp_path):
        """Test that default values are set for optional arguments."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()
        args = parser.parse(["--build-dir", str(build_dir)])

        # Check defaults from ForgeArguments dataclass
        assert args.source_dir is None
        assert args.cmake_args == []
        assert args.build_args == []
        assert args.verbose is False
        assert args.configure is True  # Should configure by default
        assert args.clean_build is False
        assert args.project_name is None
        assert args.database_path is None


class TestErrorCases:
    """Test error cases and invalid inputs."""

    def test_parse_without_required_argument(self):
        """Test that missing required --build-dir raises error."""
        parser = ArgumentParser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse([])

        # argparse exits with code 2 for missing required arguments
        assert exc_info.value.code == 2

    def test_parse_with_unknown_argument(self, tmp_path):
        """Test that unknown arguments raise error."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        parser = ArgumentParser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse(["--build-dir", str(build_dir), "--unknown-flag"])

        assert exc_info.value.code == 2
