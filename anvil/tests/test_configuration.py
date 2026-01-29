"""
Test suite for Configuration Manager.

Tests configuration loading, validation, and access according to
Step 1.2 of the implementation plan.
"""

import os
from pathlib import Path

import pytest

from anvil.config.configuration import ConfigurationError, ConfigurationManager


class TestConfigurationLoading:
    """Test configuration file loading."""

    def test_load_complete_config(self):
        """Test loading valid anvil.toml with all options."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        assert config.get("anvil.languages") == ["python", "cpp"]
        assert config.get("anvil.incremental") is True
        assert config.get("anvil.fail_fast") is False
        assert config.get("anvil.parallel") is True
        assert config.get("anvil.max_errors") == 0
        assert config.get("anvil.max_warnings") == 10

    def test_load_minimal_config(self):
        """Test loading minimal anvil.toml (empty file) with defaults."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "minimal.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        # Should apply default values
        assert config.get("anvil.languages") is None  # Auto-detect by default
        assert config.get("anvil.incremental") is True  # Default
        assert config.get("anvil.fail_fast") is False  # Default
        assert config.get("anvil.max_errors") == 0  # Default

    def test_load_invalid_toml_syntax(self):
        """Test loading file with invalid TOML syntax raises error."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "invalid.toml"

        with pytest.raises(ConfigurationError, match="Failed to parse"):
            ConfigurationManager(config_path=str(fixture_path))

    def test_load_nonexistent_file(self):
        """Test loading non-existent file uses defaults."""
        config = ConfigurationManager(config_path="nonexistent.toml")

        # Should use defaults when file doesn't exist
        assert config.get("anvil.incremental") is True
        assert config.get("anvil.fail_fast") is False

    def test_load_from_custom_path(self):
        """Test loading configuration from custom path."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        assert config.get("anvil.languages") == ["python", "cpp"]


class TestValidatorConfiguration:
    """Test retrieving validator-specific configuration."""

    def test_get_validator_config_python_flake8(self):
        """Test get_validator_config for specific validator."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        flake8_config = config.get_validator_config("python", "flake8")

        assert flake8_config["enabled"] is True
        assert flake8_config["max_line_length"] == 100
        assert flake8_config["ignore"] == ["E203", "W503"]

    def test_get_validator_config_cpp_clang_tidy(self):
        """Test get_validator_config for C++ validator."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        clang_tidy_config = config.get_validator_config("cpp", "clang-tidy")

        assert clang_tidy_config["enabled"] is True
        assert clang_tidy_config["checks"] == ["bugprone-*", "modernize-*"]

    def test_get_validator_config_with_defaults(self):
        """Test validator config returns defaults when not specified."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "minimal.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        flake8_config = config.get_validator_config("python", "flake8")

        # Should have default values
        assert "enabled" in flake8_config
        assert "max_line_length" in flake8_config

    def test_get_validator_config_invalid_validator(self):
        """Test invalid validator name raises error."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        with pytest.raises(ConfigurationError, match="Unknown validator"):
            config.get_validator_config("python", "nonexistent")


class TestLanguageConfiguration:
    """Test retrieving language-specific configuration."""

    def test_get_language_config_python(self):
        """Test get_language_config for Python."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        python_config = config.get_language_config("python")

        assert python_config["enabled"] is True
        assert python_config["file_patterns"] == ["**/*.py"]

    def test_get_language_config_cpp(self):
        """Test get_language_config for C++."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        cpp_config = config.get_language_config("cpp")

        assert cpp_config["enabled"] is True
        assert cpp_config["standard"] == "c++17"

    def test_get_language_config_with_defaults(self):
        """Test language config includes defaults."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "minimal.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        python_config = config.get_language_config("python")

        assert "enabled" in python_config
        assert "file_patterns" in python_config


class TestConfigurationValidation:
    """Test configuration value validation."""

    def test_validate_negative_max_errors(self):
        """Test configuration validation (max_errors must be non-negative)."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "invalid_max_errors.toml"

        with pytest.raises(ConfigurationError, match="max_errors must be non-negative"):
            ConfigurationManager(config_path=str(fixture_path))

    def test_validate_zero_complexity(self):
        """Test validation of max_complexity (must be positive)."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "invalid_complexity.toml"

        with pytest.raises(ConfigurationError, match="max_complexity must be positive"):
            ConfigurationManager(config_path=str(fixture_path))


class TestConfigurationInheritance:
    """Test configuration inheritance and merging."""

    def test_validator_inherits_language_defaults(self):
        """Test configuration inheritance (language defaults + validator overrides)."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        # Validator config should include both language-level and validator-level settings
        black_config = config.get_validator_config("python", "black")

        assert black_config["enabled"] is True
        assert black_config["line_length"] == 100

    def test_configuration_merging(self):
        """Test configuration merging (defaults + user config)."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "minimal.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        # Should merge user config (minimal) with defaults
        flake8_config = config.get_validator_config("python", "flake8")

        # Should have defaults
        assert "enabled" in flake8_config
        assert "max_line_length" in flake8_config


class TestEnvironmentVariables:
    """Test environment variable expansion in configuration."""

    def test_expand_environment_variables(self):
        """Test environment variable expansion in config."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "with_env_vars.toml"

        # Set environment variables
        os.environ["PROJECT_NAME"] = "test_project"
        os.environ["MAX_LINE_LENGTH"] = "120"

        try:
            config = ConfigurationManager(config_path=str(fixture_path))

            assert config.get("anvil.project_name") == "test_project"

            flake8_config = config.get_validator_config("python", "flake8")
            assert flake8_config["max_line_length"] == 120

        finally:
            # Clean up environment
            os.environ.pop("PROJECT_NAME", None)
            os.environ.pop("MAX_LINE_LENGTH", None)

    def test_missing_environment_variable(self):
        """Test that missing environment variables raise error."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "with_env_vars.toml"

        # Ensure env vars are not set
        os.environ.pop("PROJECT_NAME", None)
        os.environ.pop("MAX_LINE_LENGTH", None)

        with pytest.raises(ConfigurationError, match="Environment variable.*not set"):
            ConfigurationManager(config_path=str(fixture_path))


class TestConfigurationDefaults:
    """Test default configuration values."""

    def test_default_values_applied(self):
        """Test default values applied when not specified."""
        config = ConfigurationManager()

        # Check default values
        assert config.get("anvil.incremental") is True
        assert config.get("anvil.fail_fast") is False
        assert config.get("anvil.parallel") is True
        assert config.get("anvil.max_errors") == 0

    def test_get_with_default_value(self):
        """Test get() with default value parameter."""
        config = ConfigurationManager()

        # Non-existent key should return default
        assert config.get("nonexistent.key", "default_value") == "default_value"

    def test_get_nested_config(self):
        """Test getting nested configuration values."""
        fixture_path = Path(__file__).parent / "fixtures" / "config" / "complete.toml"
        config = ConfigurationManager(config_path=str(fixture_path))

        # Test nested access
        assert config.get("anvil.python.flake8.max_line_length") == 100
