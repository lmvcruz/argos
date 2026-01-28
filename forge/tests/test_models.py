"""
Unit tests for Forge data models.

Tests data model instantiation, validation, and serialization.
"""

from datetime import datetime
import json
from pathlib import Path

import pytest

from forge.models.arguments import ForgeArguments
from forge.models.metadata import (
    BuildMetadata,
    BuildTarget,
    BuildWarning,
    ConfigureMetadata,
    Error,
)
from forge.models.results import BuildResult, ConfigureResult


class TestForgeArguments:
    """Test ForgeArguments dataclass."""

    def test_create_with_valid_data(self):
        """Test ForgeArguments creation with valid data."""
        args = ForgeArguments(
            source_dir=Path("/path/to/source"),
            build_dir=Path("/path/to/build"),
            cmake_args=["-DCMAKE_BUILD_TYPE=Release"],
            build_args=["-j8"],
            project_name="MyProject",
            server_url="http://localhost:8000",
            verbose=True,
            dry_run=False,
            database_path=Path("/path/to/db.sqlite"),
        )

        assert args.source_dir == Path("/path/to/source")
        assert args.build_dir == Path("/path/to/build")
        assert args.cmake_args == ["-DCMAKE_BUILD_TYPE=Release"]
        assert args.build_args == ["-j8"]
        assert args.project_name == "MyProject"
        assert args.server_url == "http://localhost:8000"
        assert args.verbose is True
        assert args.dry_run is False
        assert args.database_path == Path("/path/to/db.sqlite")

    def test_create_with_minimal_data(self):
        """Test ForgeArguments with only required field."""
        args = ForgeArguments(build_dir=Path("/path/to/build"))

        assert args.build_dir == Path("/path/to/build")
        assert args.source_dir is None
        assert args.cmake_args == []
        assert args.build_args == []
        assert args.project_name is None
        assert args.server_url is None
        assert args.verbose is False
        assert args.dry_run is False
        assert args.database_path is None

    def test_missing_required_field(self):
        """Test ForgeArguments with missing required field raises error."""
        with pytest.raises(TypeError):
            ForgeArguments()

    def test_path_handling_string_conversion(self):
        """Test that string paths are converted to Path objects."""
        args = ForgeArguments(
            build_dir="/path/to/build",
            source_dir="/path/to/source",
        )

        assert isinstance(args.build_dir, Path)
        assert isinstance(args.source_dir, Path)

    def test_to_dict(self):
        """Test conversion to dictionary for JSON serialization."""
        args = ForgeArguments(
            source_dir=Path("/src"),
            build_dir=Path("/build"),
            cmake_args=["-DCMAKE_BUILD_TYPE=Release"],
            project_name="Test",
        )

        result = args.to_dict()

        # Check that paths are converted to strings (actual format depends on OS)
        assert result["source_dir"] == str(Path("/src"))
        assert result["build_dir"] == str(Path("/build"))
        assert result["cmake_args"] == ["-DCMAKE_BUILD_TYPE=Release"]
        assert result["project_name"] == "Test"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "build_dir": "/build",
            "source_dir": "/src",
            "cmake_args": ["-DCMAKE_BUILD_TYPE=Debug"],
            "build_args": ["-j4"],
            "project_name": "FromDict",
            "server_url": None,
            "verbose": True,
            "dry_run": False,
            "database_path": None,
        }

        args = ForgeArguments.from_dict(data)

        assert args.build_dir == Path("/build")
        assert args.source_dir == Path("/src")
        assert args.cmake_args == ["-DCMAKE_BUILD_TYPE=Debug"]
        assert args.project_name == "FromDict"

    def test_json_serialization(self):
        """Test JSON serialization/deserialization roundtrip."""
        original = ForgeArguments(
            source_dir=Path("/src"),
            build_dir=Path("/build"),
            cmake_args=["-DCMAKE_BUILD_TYPE=Release"],
            verbose=True,
        )

        # Serialize to JSON
        json_str = json.dumps(original.to_dict())

        # Deserialize from JSON
        data = json.loads(json_str)
        restored = ForgeArguments.from_dict(data)

        assert restored.source_dir == original.source_dir
        assert restored.build_dir == original.build_dir
        assert restored.cmake_args == original.cmake_args
        assert restored.verbose == original.verbose


class TestConfigureResult:
    """Test ConfigureResult dataclass."""

    def test_create_with_all_fields(self):
        """Test ConfigureResult with all fields populated."""
        start = datetime.now()
        end = datetime.now()

        result = ConfigureResult(
            success=True,
            exit_code=0,
            duration=1.5,
            stdout="Configure output",
            stderr="",
            start_time=start,
            end_time=end,
            cmake_version="3.28.1",
            generator="Unix Makefiles",
            compiler_c="/usr/bin/gcc",
            compiler_cxx="/usr/bin/g++",
            build_type="Release",
        )

        assert result.success is True
        assert result.exit_code == 0
        assert result.duration == 1.5
        assert result.stdout == "Configure output"
        assert result.cmake_version == "3.28.1"
        assert result.generator == "Unix Makefiles"

    def test_create_with_optional_fields_none(self):
        """Test ConfigureResult with optional fields as None."""
        result = ConfigureResult(
            success=False,
            exit_code=1,
            duration=0.5,
            stdout="",
            stderr="Error message",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        assert result.success is False
        assert result.cmake_version is None
        assert result.generator is None
        assert result.compiler_c is None

    def test_json_serialization(self):
        """Test JSON serialization with datetime objects."""
        start = datetime(2026, 1, 27, 10, 0, 0)
        end = datetime(2026, 1, 27, 10, 0, 2)

        result = ConfigureResult(
            success=True,
            exit_code=0,
            duration=2.0,
            stdout="output",
            stderr="",
            start_time=start,
            end_time=end,
            cmake_version="3.28.1",
        )

        data = result.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ConfigureResult.from_dict(restored_data)

        assert restored.success == result.success
        assert restored.duration == result.duration
        assert restored.cmake_version == result.cmake_version


class TestBuildResult:
    """Test BuildResult dataclass."""

    def test_create_with_all_fields(self):
        """Test BuildResult with all fields."""
        start = datetime.now()
        end = datetime.now()

        result = BuildResult(
            success=True,
            exit_code=0,
            duration=10.5,
            stdout="Build output",
            stderr="",
            start_time=start,
            end_time=end,
            warnings_count=5,
            errors_count=0,
            targets_built=["app", "lib"],
        )

        assert result.success is True
        assert result.warnings_count == 5
        assert result.errors_count == 0
        assert result.targets_built == ["app", "lib"]

    def test_create_with_minimal_fields(self):
        """Test BuildResult with minimal required fields."""
        result = BuildResult(
            success=False,
            exit_code=1,
            duration=1.0,
            stdout="",
            stderr="Build failed",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )

        assert result.success is False
        assert result.warnings_count == 0
        assert result.errors_count == 0
        assert result.targets_built == []

    def test_to_dict(self):
        """Test BuildResult to_dict serialization."""
        start = datetime(2024, 1, 15, 10, 30, 0)
        end = datetime(2024, 1, 15, 10, 35, 30)

        result = BuildResult(
            success=True,
            exit_code=0,
            duration=330.5,
            stdout="Build output",
            stderr="",
            start_time=start,
            end_time=end,
            warnings_count=2,
            errors_count=0,
            targets_built=["main", "tests"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert data["exit_code"] == 0
        assert data["duration"] == 330.5
        assert data["stdout"] == "Build output"
        assert data["stderr"] == ""
        assert data["start_time"] == "2024-01-15T10:30:00"
        assert data["end_time"] == "2024-01-15T10:35:30"
        assert data["warnings_count"] == 2
        assert data["errors_count"] == 0
        assert data["targets_built"] == ["main", "tests"]

    def test_from_dict(self):
        """Test BuildResult from_dict deserialization."""
        data = {
            "success": True,
            "exit_code": 0,
            "duration": 100.5,
            "stdout": "Output",
            "stderr": "",
            "start_time": "2024-01-15T10:00:00",
            "end_time": "2024-01-15T10:01:40",
            "warnings_count": 1,
            "errors_count": 0,
            "targets_built": ["app"],
        }

        result = BuildResult.from_dict(data)

        assert result.success is True
        assert result.exit_code == 0
        assert result.duration == 100.5
        assert result.stdout == "Output"
        assert result.start_time == datetime(2024, 1, 15, 10, 0, 0)
        assert result.end_time == datetime(2024, 1, 15, 10, 1, 40)
        assert result.warnings_count == 1
        assert result.targets_built == ["app"]


class TestConfigureMetadata:
    """Test ConfigureMetadata dataclass."""

    def test_create_with_all_fields(self):
        """Test ConfigureMetadata with complete data."""
        metadata = ConfigureMetadata(
            project_name="TestProject",
            cmake_version="3.28.1",
            generator="Ninja",
            compiler_c="/usr/bin/clang",
            compiler_cxx="/usr/bin/clang++",
            build_type="Debug",
            system_name="Linux",
            system_processor="x86_64",
            found_packages=["Boost", "OpenSSL"],
            configuration_options={"CMAKE_CXX_STANDARD": "17"},
        )

        assert metadata.project_name == "TestProject"
        assert metadata.cmake_version == "3.28.1"
        assert metadata.found_packages == ["Boost", "OpenSSL"]
        assert metadata.configuration_options["CMAKE_CXX_STANDARD"] == "17"

    def test_create_with_optional_fields_none(self):
        """Test ConfigureMetadata with optional fields."""
        metadata = ConfigureMetadata(
            project_name=None,
            cmake_version="3.28.1",
            generator="Ninja",
            system_name="Linux",
            system_processor="x86_64",
        )

        assert metadata.project_name is None
        assert metadata.compiler_c is None
        assert metadata.found_packages == []
        assert metadata.configuration_options == {}

    def test_json_serialization(self):
        """Test JSON serialization of metadata."""
        metadata = ConfigureMetadata(
            project_name="Project",
            cmake_version="3.28.1",
            generator="Ninja",
            system_name="Linux",
            system_processor="x86_64",
            found_packages=["Pkg1"],
            configuration_options={"KEY": "value"},
        )

        data = metadata.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = ConfigureMetadata.from_dict(restored_data)

        assert restored.project_name == metadata.project_name
        assert restored.found_packages == metadata.found_packages


class TestBuildMetadata:
    """Test BuildMetadata dataclass."""

    def test_create_with_all_fields(self):
        """Test BuildMetadata with all fields."""
        warnings = [
            BuildWarning(
                file="test.cpp",
                line=10,
                column=5,
                message="unused variable",
                warning_type="unused-variable",
            )
        ]
        errors = [
            Error(
                file="main.cpp",
                line=20,
                column=1,
                message="syntax error",
                error_type="syntax",
            )
        ]

        metadata = BuildMetadata(
            project_name="TestProject",
            targets=[
                BuildTarget(name="app", target_type="executable"),
                BuildTarget(name="lib", target_type="static_library"),
            ],
            warnings=warnings,
            errors=errors,
        )

        assert metadata.project_name == "TestProject"
        assert len(metadata.targets) == 2
        assert len(metadata.warnings) == 1
        assert len(metadata.errors) == 1

    def test_create_with_empty_diagnostics(self):
        """Test BuildMetadata with no warnings or errors."""
        metadata = BuildMetadata(
            project_name="Clean",
            targets=[BuildTarget(name="app", target_type="executable")],
            warnings=[],
            errors=[],
        )

        assert len(metadata.targets) == 1
        assert len(metadata.warnings) == 0
        assert len(metadata.errors) == 0


class TestBuildWarning:
    """Test BuildWarning dataclass."""

    def test_create_with_complete_info(self):
        """Test BuildWarning with all location information."""
        warning = BuildWarning(
            file="source.cpp",
            line=42,
            column=15,
            message="variable 'x' is not used",
            warning_type="unused-variable",
        )

        assert warning.file == "source.cpp"
        assert warning.line == 42
        assert warning.column == 15
        assert warning.message == "variable 'x' is not used"
        assert warning.warning_type == "unused-variable"

    def test_create_with_partial_info(self):
        """Test BuildWarning with partial location information."""
        warning = BuildWarning(
            file=None,
            line=None,
            column=None,
            message="general warning",
            warning_type=None,
        )

        assert warning.file is None
        assert warning.line is None
        assert warning.message == "general warning"

    def test_json_serialization(self):
        """Test BuildWarning JSON serialization."""
        warning = BuildWarning(
            file="test.cpp",
            line=10,
            column=5,
            message="warning message",
            warning_type="test-warning",
        )

        data = warning.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = BuildWarning.from_dict(restored_data)

        assert restored.file == warning.file
        assert restored.line == warning.line
        assert restored.message == warning.message


class TestError:
    """Test Error dataclass."""

    def test_create_with_complete_info(self):
        """Test Error with all location information."""
        error = Error(
            file="main.cpp",
            line=100,
            column=20,
            message="expected ';' before '}'",
            error_type="syntax-error",
        )

        assert error.file == "main.cpp"
        assert error.line == 100
        assert error.column == 20
        assert error.message == "expected ';' before '}'"
        assert error.error_type == "syntax-error"

    def test_create_with_minimal_info(self):
        """Test Error with only message."""
        error = Error(
            file=None,
            line=None,
            column=None,
            message="linker error",
            error_type=None,
        )

        assert error.file is None
        assert error.message == "linker error"

    def test_json_serialization(self):
        """Test Error JSON serialization."""
        error = Error(
            file="error.cpp",
            line=50,
            column=10,
            message="error message",
            error_type="compile-error",
        )

        data = error.to_dict()
        json_str = json.dumps(data)
        restored_data = json.loads(json_str)
        restored = Error.from_dict(restored_data)

        assert restored.file == error.file
        assert restored.line == error.line
        assert restored.message == error.message
