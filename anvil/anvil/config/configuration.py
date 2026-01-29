"""
Configuration management for Anvil.

Handles loading, validation, and access to configuration from anvil.toml files.
Supports default values, environment variable expansion, and configuration inheritance.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import toml


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""


class ConfigurationManager:
    """
    Manages Anvil configuration from TOML files.

    Loads configuration from anvil.toml, applies defaults, validates values,
    and provides access to configuration settings.
    """

    # Default configuration values
    DEFAULTS = {
        "anvil": {
            "languages": None,  # Auto-detect if not specified
            "incremental": True,
            "fail_fast": False,
            "parallel": True,
            "max_errors": 0,
            "max_warnings": 10,
        },
        "anvil.python": {
            "enabled": True,
            "file_patterns": ["**/*.py"],
        },
        "anvil.cpp": {
            "enabled": True,
            "file_patterns": ["**/*.{cpp,hpp,cc,h,cxx,hxx}"],
            "standard": "c++17",
        },
        # Python validators
        "anvil.python.flake8": {
            "enabled": True,
            "max_line_length": 100,
            "ignore": [],
        },
        "anvil.python.black": {
            "enabled": True,
            "line_length": 100,
        },
        "anvil.python.isort": {
            "enabled": True,
            "profile": "black",
            "line_length": 100,
        },
        "anvil.python.pylint": {
            "enabled": True,
            "max_complexity": 10,
            "disable": [],
        },
        "anvil.python.radon": {
            "enabled": True,
            "max_complexity": 10,
        },
        "anvil.python.vulture": {
            "enabled": True,
            "min_confidence": 80,
        },
        "anvil.python.autoflake": {
            "enabled": True,
            "check_only": True,
        },
        "anvil.python.pytest": {
            "enabled": True,
            "coverage_threshold": 90.0,
        },
        # C++ validators
        "anvil.cpp.clang-tidy": {
            "enabled": True,
            "checks": ["bugprone-*", "modernize-*", "performance-*"],
        },
        "anvil.cpp.clang-format": {
            "enabled": True,
            "style": "Google",
        },
        "anvil.cpp.cppcheck": {
            "enabled": True,
            "enable": ["warning", "style", "performance"],
        },
        "anvil.cpp.cpplint": {
            "enabled": True,
            "filter": [],
        },
        "anvil.cpp.iwyu": {
            "enabled": False,  # Optional, can be slow
        },
        "anvil.cpp.gtest": {
            "enabled": True,
            "test_filter": "*",
        },
    }

    # Known validators by language
    KNOWN_VALIDATORS = {
        "python": ["flake8", "black", "isort", "pylint", "radon", "vulture", "autoflake", "pytest"],
        "cpp": ["clang-tidy", "clang-format", "cppcheck", "cpplint", "iwyu", "gtest"],
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (default: anvil.toml)
        """
        self.config_path = config_path or "anvil.toml"
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load and parse configuration from file."""
        # Start with defaults
        self._config = self._deep_copy_dict(self.DEFAULTS)

        # Load user configuration if file exists
        if Path(self.config_path).exists():
            try:
                # Read file as text first
                with open(self.config_path, "r", encoding="utf-8") as f:
                    toml_text = f.read()

                # Expand environment variables in the text before parsing
                toml_text = self._expand_env_vars_in_text(toml_text)

                # Parse TOML
                user_config = toml.loads(toml_text)

                # Merge user config with defaults
                self._merge_config(self._config, user_config)
            except toml.TomlDecodeError as e:
                raise ConfigurationError(f"Failed to parse configuration file: {e}")

        # Validate configuration
        self._validate_config()

    def _expand_env_vars_in_text(self, text: str) -> str:
        """
        Expand environment variables in TOML text before parsing.

        Args:
            text: TOML file content as text

        Returns:
            Text with expanded environment variables

        Raises:
            ConfigurationError: If environment variable is not set
        """
        # Match ${VAR_NAME} pattern
        matches = re.findall(r"\$\{([^}]+)\}", text)
        for var_name in matches:
            if var_name not in os.environ:
                raise ConfigurationError(f"Environment variable '{var_name}' not set")
            env_value = os.environ[var_name]
            # Try to convert to int if it looks like a number
            try:
                int(env_value)
                # If it's a number, don't quote it in TOML
                text = text.replace(f'"${{{var_name}}}"', env_value)
            except ValueError:
                # If it's not a number, keep the quotes for string
                text = text.replace(f"${{{var_name}}}", env_value)
        return text

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration dictionary (modified in place)
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _validate_config(self):
        """
        Validate configuration values.

        Raises:
            ConfigurationError: If configuration contains invalid values
        """
        # Validate Python validators first (more specific errors)
        if "anvil" in self._config and "python" in self._config["anvil"]:
            python_config = self._config["anvil"]["python"]
            if "pylint" in python_config:
                max_complexity = python_config["pylint"].get("max_complexity")
                if max_complexity is not None and max_complexity <= 0:
                    raise ConfigurationError("max_complexity must be positive")

        # Validate anvil-level settings
        max_errors = self._config.get("anvil", {}).get("max_errors")
        if max_errors is not None and max_errors < 0:
            raise ConfigurationError("max_errors must be non-negative")

    def _deep_copy_dict(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy_dict(value)
            elif isinstance(value, list):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Configuration key in dot notation (e.g., "anvil.python.flake8.enabled")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def get_validator_config(self, language: str, validator: str) -> Dict[str, Any]:
        """
        Get configuration for a specific validator.

        Args:
            language: Language name (e.g., "python", "cpp")
            validator: Validator name (e.g., "flake8", "clang-tidy")

        Returns:
            Validator configuration dictionary

        Raises:
            ConfigurationError: If validator is unknown
        """
        # Validate validator name
        if language not in self.KNOWN_VALIDATORS:
            raise ConfigurationError(f"Unknown language: {language}")
        if validator not in self.KNOWN_VALIDATORS[language]:
            raise ConfigurationError(f"Unknown validator '{validator}' for language '{language}'")

        # Get validator config with defaults
        key = f"anvil.{language}.{validator}"
        validator_config = self.get(key, {})

        # Merge with defaults
        default_key = f"anvil.{language}.{validator}"
        if default_key in self.DEFAULTS:
            merged = self._deep_copy_dict(self.DEFAULTS[default_key])
            merged.update(validator_config)
            return merged

        return validator_config

    def get_language_config(self, language: str) -> Dict[str, Any]:
        """
        Get configuration for a specific language.

        Args:
            language: Language name (e.g., "python", "cpp")

        Returns:
            Language configuration dictionary
        """
        key = f"anvil.{language}"
        language_config = self.get(key, {})

        # Merge with defaults
        default_key = f"anvil.{language}"
        if default_key in self.DEFAULTS:
            merged = self._deep_copy_dict(self.DEFAULTS[default_key])
            merged.update(language_config)
            return merged

        return language_config
