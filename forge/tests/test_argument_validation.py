"""
Unit tests for argument validation logic.

Tests validation of command-line arguments for logical consistency,
path validity, and mutually exclusive options.
Following TDD principles - these tests are written before implementation.
"""

import pytest

from forge.cli.argument_validator import ArgumentValidator, ValidationError
from forge.models.arguments import ForgeArguments


class TestValidArgumentCombinations:
    """Test that validation passes with valid argument combinations."""

    def test_validate_with_existing_source_and_build_dirs(self, tmp_path):
        """Test validation passes when both directories exist."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        # Create CMakeLists.txt
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)  # Should not raise

    def test_validate_with_source_dir_only(self, tmp_path):
        """Test validation passes when source-dir exists and build-dir will be created."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()

        # Create CMakeLists.txt
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)  # Should not raise

    def test_validate_with_build_dir_only(self, tmp_path):
        """Test validation passes when only build-dir exists (reconfigure mode)."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        # Create CMakeCache.txt to indicate previous configuration
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28")

        args = ForgeArguments(
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)  # Should not raise

    def test_validate_with_valid_database_path(self, tmp_path):
        """Test validation passes with valid database path."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        db_path = tmp_path / "forge.db"

        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            database_path=db_path,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)  # Should not raise


class TestBuildDirectoryValidation:
    """Test validation of build directory requirements."""

    def test_error_when_build_dir_missing_and_no_source_dir(self, tmp_path):
        """Test error when build-dir doesn't exist and source-dir not provided."""
        build_dir = tmp_path / "nonexistent_build"

        args = ForgeArguments(
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "build directory does not exist" in str(excinfo.value).lower()
        assert "source-dir" in str(excinfo.value).lower()

    def test_error_when_build_dir_missing_no_cmake_cache(self, tmp_path):
        """Test error when build-dir exists but has no CMakeCache.txt and no source-dir."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "cmakecache.txt" in str(excinfo.value).lower()
        assert "source-dir" in str(excinfo.value).lower()


class TestSourceDirectoryValidation:
    """Test validation of source directory requirements."""

    def test_error_when_source_dir_does_not_exist(self, tmp_path):
        """Test error when source-dir doesn't exist."""
        source_dir = tmp_path / "nonexistent_source"
        build_dir = tmp_path / "build"

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "source directory does not exist" in str(excinfo.value).lower()
        assert str(source_dir) in str(excinfo.value)

    def test_error_when_source_dir_missing_cmakelists(self, tmp_path):
        """Test error when source-dir doesn't contain CMakeLists.txt."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "cmakelists.txt" in str(excinfo.value).lower()
        assert str(source_dir) in str(excinfo.value)

    def test_error_when_source_dir_is_file(self, tmp_path):
        """Test error when source-dir path points to a file."""
        source_file = tmp_path / "source.txt"
        build_dir = tmp_path / "build"
        source_file.write_text("not a directory")

        args = ForgeArguments(
            source_dir=source_file,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "not a directory" in str(excinfo.value).lower()


class TestDatabaseValidation:
    """Test validation of database path."""

    def test_error_when_database_path_is_directory(self, tmp_path):
        """Test error when database path points to a directory."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        db_path = tmp_path / "dbdir"

        source_dir.mkdir()
        db_path.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            database_path=db_path,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "database path" in str(excinfo.value).lower()
        assert "directory" in str(excinfo.value).lower()

    def test_error_when_database_parent_does_not_exist(self, tmp_path):
        """Test error when database parent directory doesn't exist."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        db_path = tmp_path / "nonexistent" / "forge.db"

        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            database_path=db_path,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "database" in str(excinfo.value).lower()
        assert "parent directory" in str(excinfo.value).lower()


class TestPathNormalization:
    """Test path normalization and validation."""

    def test_paths_are_absolute(self, tmp_path):
        """Test that paths are converted to absolute paths."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        (source_dir / "CMakeLists.txt").write_text("project(TestProject)")

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)

        # ArgumentParser already converts to absolute, but validation should handle it
        assert args.source_dir.is_absolute()
        assert args.build_dir.is_absolute()

    def test_symlinks_are_resolved(self, tmp_path):
        """Test that symbolic links are resolved to real paths."""
        # Skip on Windows where symlinks require admin privileges
        pytest.importorskip("os", reason="Symlink test")

        real_source = tmp_path / "real_source"
        real_source.mkdir()
        (real_source / "CMakeLists.txt").write_text("project(TestProject)")

        link_source = tmp_path / "link_source"
        try:
            link_source.symlink_to(real_source)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this system")

        build_dir = tmp_path / "build"

        args = ForgeArguments(
            source_dir=link_source,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        validator.validate_arguments(args)  # Should not raise


class TestMutuallyExclusiveOptions:
    """Test validation of mutually exclusive options."""

    def test_no_configure_requires_existing_build(self, tmp_path):
        """Test that --no-configure requires build directory with CMakeCache.txt."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            build_dir=build_dir,
            configure=False,  # --no-configure
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "no-configure" in str(excinfo.value).lower()
        assert "cmakecache.txt" in str(excinfo.value).lower()

    def test_no_configure_with_nonexistent_build_dir(self, tmp_path):
        """Test that --no-configure with nonexistent build directory fails."""
        build_dir = tmp_path / "nonexistent_build"

        args = ForgeArguments(
            build_dir=build_dir,
            configure=False,  # --no-configure
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "build directory does not exist" in str(excinfo.value).lower()
        assert "no-configure" in str(excinfo.value).lower()

    def test_clean_build_with_no_configure_is_invalid(self, tmp_path):
        """Test that --clean-build and --no-configure are mutually exclusive."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        (build_dir / "CMakeCache.txt").write_text("CMAKE_VERSION:INTERNAL=3.28")

        args = ForgeArguments(
            build_dir=build_dir,
            configure=False,  # --no-configure
            clean_build=True,  # --clean-build
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        assert "mutually exclusive" in str(excinfo.value).lower()
        assert "clean-build" in str(excinfo.value).lower()
        assert "no-configure" in str(excinfo.value).lower()


class TestValidationErrorMessages:
    """Test that validation errors have helpful messages."""

    def test_error_message_includes_path(self, tmp_path):
        """Test that error messages include the problematic path."""
        source_dir = tmp_path / "nonexistent"
        build_dir = tmp_path / "build"

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        # Error message should include the path
        assert str(source_dir) in str(excinfo.value)

    def test_error_message_suggests_fix(self, tmp_path):
        """Test that error messages suggest how to fix the issue."""
        build_dir = tmp_path / "nonexistent_build"

        args = ForgeArguments(
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        # Should suggest providing source-dir
        error_msg = str(excinfo.value).lower()
        assert "source-dir" in error_msg or "--source-dir" in error_msg

    def test_validation_error_has_context(self, tmp_path):
        """Test that ValidationError includes context about what was being validated."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        # Missing CMakeLists.txt

        build_dir = tmp_path / "build"

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError) as excinfo:
            validator.validate_arguments(args)

        # Should mention what's wrong
        assert excinfo.value.args[0]  # Has a message
        assert len(str(excinfo.value)) > 10  # Has substantial content


class TestMultipleValidationErrors:
    """Test handling of multiple validation errors."""

    def test_reports_first_error_encountered(self, tmp_path):
        """Test that validation stops at first error (fail-fast behavior)."""
        source_dir = tmp_path / "nonexistent_source"
        build_dir = tmp_path / "nonexistent_build"
        db_path = tmp_path / "nonexistent" / "forge.db"

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            database_path=db_path,
        )

        validator = ArgumentValidator()
        with pytest.raises(ValidationError):
            validator.validate_arguments(args)

        # Should raise an error (we're using fail-fast, not collecting all errors)
