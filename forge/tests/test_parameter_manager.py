"""
Unit tests for CMake parameter management.

Tests CMake command generation with various parameter combinations.
Following TDD principles - these tests are written before implementation.
"""

from forge.cmake.parameter_manager import CMakeParameterManager
from forge.models.arguments import ForgeArguments


class TestConfigureCommandBasic:
    """Test basic configure command generation."""

    def test_configure_with_minimal_arguments(self, tmp_path):
        """Test configure command with only required arguments."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Should be: cmake <source_dir> -B <build_dir>
        assert "cmake" in command
        assert str(source_dir) in command
        assert "-B" in command
        assert str(build_dir) in command

    def test_configure_with_generator(self, tmp_path):
        """Test configure command with generator specification."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-G", "Ninja"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert "-G" in command
        assert "Ninja" in command

    def test_configure_with_build_type(self, tmp_path):
        """Test configure command with CMAKE_BUILD_TYPE."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DCMAKE_BUILD_TYPE=Release"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert "-DCMAKE_BUILD_TYPE=Release" in command


class TestConfigureCommandWithCMakeArgs:
    """Test configure command with various CMake arguments."""

    def test_configure_with_single_cmake_arg(self, tmp_path):
        """Test configure command with single -D argument."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DUSE_TESTING=ON"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert "-DUSE_TESTING=ON" in command

    def test_configure_with_multiple_cmake_args(self, tmp_path):
        """Test configure command with multiple CMake arguments."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[
                "-DCMAKE_BUILD_TYPE=Debug",
                "-DBUILD_SHARED_LIBS=ON",
                "-DENABLE_TESTS=ON",
            ],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert "-DCMAKE_BUILD_TYPE=Debug" in command
        assert "-DBUILD_SHARED_LIBS=ON" in command
        assert "-DENABLE_TESTS=ON" in command

    def test_configure_with_generator_and_args(self, tmp_path):
        """Test configure with both generator and CMake args."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert "-G" in command
        assert "Ninja" in command
        assert "-DCMAKE_BUILD_TYPE=Release" in command

    def test_configure_preserves_arg_order(self, tmp_path):
        """Test that CMake arguments maintain their order."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DFIRST=1", "-DSECOND=2", "-DTHIRD=3"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Find positions of each argument
        first_pos = command.index("-DFIRST=1")
        second_pos = command.index("-DSECOND=2")
        third_pos = command.index("-DTHIRD=3")

        # Order should be preserved
        assert first_pos < second_pos < third_pos


class TestBuildCommandBasic:
    """Test basic build command generation."""

    def test_build_with_minimal_arguments(self, tmp_path):
        """Test build command with only required arguments."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        # Should be: cmake --build <build_dir>
        assert "cmake" in command
        assert "--build" in command
        assert str(build_dir) in command

    def test_build_with_parallel_jobs(self, tmp_path):
        """Test build command with -j flag for parallel builds."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["-j8"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert "-j8" in command

    def test_build_with_verbose(self, tmp_path):
        """Test build command with verbose flag."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["--verbose"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert "--verbose" in command


class TestBuildCommandWithTarget:
    """Test build command with target specification."""

    def test_build_with_single_target(self, tmp_path):
        """Test build command with --target flag."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["--target", "my_target"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert "--target" in command
        assert "my_target" in command

    def test_build_with_multiple_targets(self, tmp_path):
        """Test build command with multiple targets."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["--target", "target1", "--target", "target2"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert command.count("--target") == 2
        assert "target1" in command
        assert "target2" in command

    def test_build_with_target_and_parallel(self, tmp_path):
        """Test build with both target and parallel jobs."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["--target", "my_lib", "-j4"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert "--target" in command
        assert "my_lib" in command
        assert "-j4" in command


class TestPathHandling:
    """Test path handling in commands."""

    def test_absolute_paths_used(self, tmp_path):
        """Test that absolute paths are used in commands."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Paths should be absolute
        assert str(source_dir.resolve()) in command
        assert str(build_dir.resolve()) in command

    def test_paths_with_spaces(self, tmp_path):
        """Test handling of paths with spaces."""
        source_dir = tmp_path / "source with spaces"
        build_dir = tmp_path / "build dir"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Command should be a list, so paths with spaces are handled correctly
        assert isinstance(command, list)
        # Paths should be in the command as separate elements
        assert any(str(source_dir) in str(part) for part in command)
        assert any(str(build_dir) in str(part) for part in command)


class TestCommandFormat:
    """Test the format of generated commands."""

    def test_configure_command_is_list(self, tmp_path):
        """Test that configure command is returned as a list."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        assert isinstance(command, list)
        assert len(command) > 0
        assert command[0] == "cmake"

    def test_build_command_is_list(self, tmp_path):
        """Test that build command is returned as a list."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        assert isinstance(command, list)
        assert len(command) > 0
        assert command[0] == "cmake"
        assert "--build" in command

    def test_configure_command_structure(self, tmp_path):
        """Test that configure command has correct structure."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-G", "Ninja"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Expected structure: cmake [args] <source> -B <build>
        assert command[0] == "cmake"
        assert "-B" in command
        b_index = command.index("-B")
        # build_dir should come after -B
        assert str(build_dir) in command[b_index + 1]

    def test_build_command_structure(self, tmp_path):
        """Test that build command has correct structure."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["-j4"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        # Expected structure: cmake --build <build_dir> [args]
        assert command[0] == "cmake"
        assert command[1] == "--build"
        assert str(build_dir) in command[2]


class TestEnvironmentHandling:
    """Test environment variable handling in parameters."""

    def test_cmake_args_with_env_var_syntax(self, tmp_path):
        """Test CMake args that reference environment variables."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DCMAKE_PREFIX_PATH=$ENV{MY_PREFIX}"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Environment variable syntax should be preserved
        assert "-DCMAKE_PREFIX_PATH=$ENV{MY_PREFIX}" in command

    def test_build_args_unchanged(self, tmp_path):
        """Test that build args are passed through unchanged."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=["--config", "Release", "-j", "8"],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        # All build args should be present and in order
        assert "--config" in command
        assert "Release" in command
        assert "-j" in command
        assert "8" in command


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_cmake_args(self, tmp_path):
        """Test with empty CMake args list."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Should still generate valid command
        assert isinstance(command, list)
        assert "cmake" in command

    def test_empty_build_args(self, tmp_path):
        """Test with empty build args list."""
        build_dir = tmp_path / "build"
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=None,
            build_dir=build_dir,
            cmake_args=[],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_build_command()

        # Should still generate valid command
        assert isinstance(command, list)
        assert "cmake" in command
        assert "--build" in command

    def test_cmake_args_with_quotes(self, tmp_path):
        """Test CMake args with quoted values."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=['-DCMAKE_CXX_FLAGS="-Wall -Wextra"'],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        command = manager.get_configure_command()

        # Quoted argument should be preserved as single element
        assert any('-DCMAKE_CXX_FLAGS="-Wall -Wextra"' in str(arg) for arg in command)
