"""
Unit tests for parameter addition and override functionality.

Tests dynamic parameter addition, override behavior, and precedence rules.
Following TDD principles - these tests are written before implementation.
"""

from forge.models.arguments import ForgeArguments
from forge.cmake.parameter_manager import CMakeParameterManager


class TestParameterAddition:
    """Test adding new parameters programmatically."""

    def test_add_new_cmake_parameter(self, tmp_path):
        """Test adding a new CMake parameter that wasn't in original args."""
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
        manager.add_parameter("BUILD_TESTING", "ON")

        command = manager.get_configure_command()
        assert "-DBUILD_TESTING=ON" in command

    def test_add_multiple_parameters(self, tmp_path):
        """Test adding multiple parameters programmatically."""
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
        manager.add_parameter("BUILD_TESTING", "ON")
        manager.add_parameter("ENABLE_DOCS", "OFF")
        manager.add_parameter("USE_OPENSSL", "ON")

        command = manager.get_configure_command()
        assert "-DBUILD_TESTING=ON" in command
        assert "-DENABLE_DOCS=OFF" in command
        assert "-DUSE_OPENSSL=ON" in command

    def test_add_parameter_with_d_prefix(self, tmp_path):
        """Test that -D prefix is added automatically if not present."""
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
        # Add without -D prefix
        manager.add_parameter("MY_PARAM", "value")

        command = manager.get_configure_command()
        # Should have -D prefix in command
        assert "-DMY_PARAM=value" in command

    def test_add_parameter_preserves_existing_args(self, tmp_path):
        """Test that adding parameters preserves original cmake_args."""
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
        manager.add_parameter("EXTRA_PARAM", "value")

        command = manager.get_configure_command()
        # Original args should still be present
        assert "-G" in command
        assert "Ninja" in command
        assert "-DCMAKE_BUILD_TYPE=Release" in command
        # New parameter should be added
        assert "-DEXTRA_PARAM=value" in command


class TestParameterOverride:
    """Test overriding existing parameters."""

    def test_override_existing_parameter(self, tmp_path):
        """Test overriding a parameter that was in original args."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DCMAKE_BUILD_TYPE=Debug"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        manager.add_parameter("CMAKE_BUILD_TYPE", "Release")

        command = manager.get_configure_command()
        # Should only have the new value, not both
        assert "-DCMAKE_BUILD_TYPE=Release" in command
        assert "-DCMAKE_BUILD_TYPE=Debug" not in command

    def test_override_multiple_times(self, tmp_path):
        """Test overriding the same parameter multiple times."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DVALUE=1"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        manager.add_parameter("VALUE", "2")
        manager.add_parameter("VALUE", "3")

        command = manager.get_configure_command()
        # Should have only the final value
        assert "-DVALUE=3" in command
        assert "-DVALUE=1" not in command
        assert "-DVALUE=2" not in command

    def test_programmatic_overrides_cli(self, tmp_path):
        """Test that programmatic parameters override CLI args."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DUSE_FEATURE=OFF"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        # Programmatically override
        manager.add_parameter("USE_FEATURE", "ON")

        command = manager.get_configure_command()
        assert "-DUSE_FEATURE=ON" in command
        assert "-DUSE_FEATURE=OFF" not in command


class TestGetParameters:
    """Test retrieving all parameters."""

    def test_get_parameters_returns_dict(self, tmp_path):
        """Test that get_parameters() returns a dictionary."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DPARAM1=value1"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        params = manager.get_parameters()

        assert isinstance(params, dict)
        assert "PARAM1" in params
        assert params["PARAM1"] == "value1"

    def test_get_parameters_includes_added_params(self, tmp_path):
        """Test that get_parameters() includes programmatically added params."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DPARAM1=value1"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        manager.add_parameter("PARAM2", "value2")
        manager.add_parameter("PARAM3", "value3")

        params = manager.get_parameters()
        assert len(params) == 3
        assert params["PARAM1"] == "value1"
        assert params["PARAM2"] == "value2"
        assert params["PARAM3"] == "value3"

    def test_get_parameters_reflects_overrides(self, tmp_path):
        """Test that get_parameters() shows overridden values."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DPARAM=old_value"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        manager.add_parameter("PARAM", "new_value")

        params = manager.get_parameters()
        # Should only have the new value
        assert params["PARAM"] == "new_value"
        assert len(params) == 1

    def test_get_parameters_handles_generator_args(self, tmp_path):
        """Test that get_parameters() handles non -D args correctly."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-G", "Ninja", "-DPARAM=value"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        params = manager.get_parameters()

        # Should only include -D parameters
        assert "PARAM" in params
        assert params["PARAM"] == "value"
        # Generator args are not parameters
        assert "G" not in params
        assert "Ninja" not in params


class TestSpecialCharacters:
    """Test handling of special characters in parameter values."""

    def test_parameter_with_spaces(self, tmp_path):
        """Test parameter value with spaces."""
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
        manager.add_parameter("MY_STRING", "hello world")

        command = manager.get_configure_command()
        # Value with spaces should be in command
        assert any("MY_STRING=hello world" in str(arg) for arg in command)

    def test_parameter_with_quotes(self, tmp_path):
        """Test parameter value with quotes."""
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
        manager.add_parameter("QUOTED_VALUE", '"quoted string"')

        params = manager.get_parameters()
        assert params["QUOTED_VALUE"] == '"quoted string"'

    def test_parameter_with_equals_sign(self, tmp_path):
        """Test parameter value containing equals sign."""
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
        manager.add_parameter("COMPLEX_VALUE", "key=value")

        params = manager.get_parameters()
        assert params["COMPLEX_VALUE"] == "key=value"

    def test_parameter_with_path_separators(self, tmp_path):
        """Test parameter value with path separators."""
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
        manager.add_parameter("INSTALL_PREFIX", "/usr/local/bin")

        params = manager.get_parameters()
        assert params["INSTALL_PREFIX"] == "/usr/local/bin"


class TestEnvironmentVariables:
    """Test environment variable handling in parameters."""

    def test_parameter_with_env_var_syntax(self, tmp_path):
        """Test parameter using CMake environment variable syntax."""
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
        manager.add_parameter("PREFIX_PATH", "$ENV{MY_PREFIX}/lib")

        params = manager.get_parameters()
        # Should preserve environment variable syntax
        assert params["PREFIX_PATH"] == "$ENV{MY_PREFIX}/lib"

    def test_add_parameter_preserves_env_syntax_from_cli(self, tmp_path):
        """Test that env var syntax from CLI is preserved after adding params."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-DPATH=$ENV{HOME}/tools"],
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        manager.add_parameter("OTHER_PARAM", "value")

        params = manager.get_parameters()
        # Original env var syntax should be preserved
        assert params["PATH"] == "$ENV{HOME}/tools"
        assert params["OTHER_PARAM"] == "value"


class TestParameterFormatting:
    """Test parameter formatting with -D prefix."""

    def test_parameter_has_d_prefix_in_command(self, tmp_path):
        """Test that parameters have -D prefix in generated commands."""
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
        manager.add_parameter("PARAM1", "value1")
        manager.add_parameter("PARAM2", "value2")

        command = manager.get_configure_command()
        # All parameters should have -D prefix
        assert "-DPARAM1=value1" in command
        assert "-DPARAM2=value2" in command

    def test_empty_value_parameter(self, tmp_path):
        """Test parameter with empty value."""
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
        manager.add_parameter("EMPTY_PARAM", "")

        command = manager.get_configure_command()
        # Should include parameter even with empty value
        assert "-DEMPTY_PARAM=" in command

    def test_boolean_style_parameters(self, tmp_path):
        """Test parameters with boolean-like values (ON/OFF)."""
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
        manager.add_parameter("OPTION_A", "ON")
        manager.add_parameter("OPTION_B", "OFF")
        manager.add_parameter("OPTION_C", "YES")
        manager.add_parameter("OPTION_D", "NO")

        params = manager.get_parameters()
        assert params["OPTION_A"] == "ON"
        assert params["OPTION_B"] == "OFF"
        assert params["OPTION_C"] == "YES"
        assert params["OPTION_D"] == "NO"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_add_parameter_to_empty_args(self, tmp_path):
        """Test adding parameters when cmake_args is empty."""
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
        manager.add_parameter("FIRST_PARAM", "value")

        params = manager.get_parameters()
        assert len(params) == 1
        assert params["FIRST_PARAM"] == "value"

    def test_get_parameters_when_no_params(self, tmp_path):
        """Test get_parameters() when no -D parameters exist."""
        source_dir = tmp_path / "source"
        build_dir = tmp_path / "build"
        source_dir.mkdir()
        build_dir.mkdir()

        args = ForgeArguments(
            source_dir=source_dir,
            build_dir=build_dir,
            cmake_args=["-G", "Ninja"],  # Only generator, no -D params
            build_args=[],
        )

        manager = CMakeParameterManager(args)
        params = manager.get_parameters()

        assert isinstance(params, dict)
        assert len(params) == 0

    def test_parameter_name_case_sensitivity(self, tmp_path):
        """Test that parameter names are case-sensitive."""
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
        manager.add_parameter("MyParam", "value1")
        manager.add_parameter("MYPARAM", "value2")
        manager.add_parameter("myparam", "value3")

        params = manager.get_parameters()
        # Should have all three as separate parameters
        assert len(params) == 3
        assert params["MyParam"] == "value1"
        assert params["MYPARAM"] == "value2"
        assert params["myparam"] == "value3"
