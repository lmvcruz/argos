"""
Configuration and test case loading from YAML files.

This module handles loading of Verdict configuration files and test cases
from both single-file and folder-based formats.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigLoader:
    """
    Loads and validates Verdict configuration files.

    The configuration file defines test suites, targets, and execution settings.
    """

    def __init__(self, config_path: Path):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dictionary with configuration data

        Raises:
            ValueError: If configuration format is invalid
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ValueError(f"Invalid configuration format in {self.config_path}")

        self._validate_config(config)
        return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration structure.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Check for required top-level keys
        if "test_suites" not in config:
            raise ValueError("Configuration must contain 'test_suites'")

        if "targets" not in config:
            raise ValueError("Configuration must contain 'targets'")

        # Validate test suites
        test_suites = config["test_suites"]
        if not isinstance(test_suites, list):
            raise ValueError("'test_suites' must be a list")

        for suite in test_suites:
            self._validate_test_suite(suite)

        # Validate targets
        targets = config["targets"]
        if not isinstance(targets, dict):
            raise ValueError("'targets' must be a dictionary")

        for target_id, target_config in targets.items():
            self._validate_target(target_id, target_config)

    def _validate_test_suite(self, suite: Dict[str, Any]) -> None:
        """
        Validate test suite configuration.

        Args:
            suite: Test suite dictionary

        Raises:
            ValueError: If suite configuration is invalid
        """
        required_fields = ["name", "target", "type"]
        for field in required_fields:
            if field not in suite:
                raise ValueError(f"Test suite missing required field: {field}")

        suite_type = suite["type"]
        if suite_type == "cases_in_folder":
            if "folder" not in suite:
                raise ValueError(
                    f"Test suite '{suite['name']}' with type 'cases_in_folder' "
                    "must have 'folder' field"
                )
        elif suite_type == "single_file":
            if "file" not in suite:
                raise ValueError(
                    f"Test suite '{suite['name']}' with type 'single_file' "
                    "must have 'file' field"
                )
        else:
            raise ValueError(
                f"Invalid test suite type '{suite_type}' for suite '{suite['name']}'. "
                "Must be 'cases_in_folder' or 'single_file'"
            )

    def _validate_target(self, target_id: str, target_config: Dict[str, Any]) -> None:
        """
        Validate target configuration.

        Args:
            target_id: Target identifier
            target_config: Target configuration dictionary

        Raises:
            ValueError: If target configuration is invalid
        """
        if not isinstance(target_config, dict):
            raise ValueError(f"Target '{target_id}' configuration must be a dictionary")

        if "callable" not in target_config:
            raise ValueError(f"Target '{target_id}' must have 'callable' field")

        callable_path = target_config["callable"]
        if not isinstance(callable_path, str):
            raise ValueError(f"Target '{target_id}' callable must be a string")

        # Verify it has at least one dot (module.function format)
        if "." not in callable_path:
            raise ValueError(
                f"Target '{target_id}' callable must be in format 'module.path.function', "
                f"got: {callable_path}"
            )


class TestCaseLoader:
    """
    Loads test cases from files and folders.

    Supports both single-file YAML format and folder-based format.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize test case loader.

        Args:
            base_path: Base directory for resolving relative paths (default: current directory)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def load_single_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load test cases from a single YAML file.

        File format:
            input: |
              <input text>
            expected:
              field1: value1
              field2: value2

        Args:
            file_path: Path to YAML file

        Returns:
            List of test case dictionaries

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Test case file not found: {full_path}")

        with open(full_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid test case format in {full_path}")

        if "input" not in data or "expected" not in data:
            raise ValueError(f"Test case in {full_path} must have 'input' and 'expected' fields")

        return [
            {
                "name": full_path.stem,
                "input": data["input"],
                "expected": data["expected"],
            }
        ]

    def load_cases_from_folder(self, folder_path: Path) -> List[Dict[str, Any]]:
        """
        Load test cases from a folder.

        Folder structure:
            folder/
              case_01/
                input.txt
                expected_output.yaml
              case_02/
                input.txt
                expected_output.yaml

        Args:
            folder_path: Path to folder containing test cases

        Returns:
            List of test case dictionaries

        Raises:
            FileNotFoundError: If folder doesn't exist
            ValueError: If folder format is invalid
        """
        full_path = self._resolve_path(folder_path)
        if not full_path.exists():
            raise FileNotFoundError(f"Test case folder not found: {full_path}")

        if not full_path.is_dir():
            raise ValueError(f"Path is not a directory: {full_path}")

        test_cases = []

        # Find all subdirectories (each is a test case)
        for case_dir in sorted(full_path.iterdir()):
            if not case_dir.is_dir():
                continue

            input_file = case_dir / "input.txt"
            expected_file = case_dir / "expected_output.yaml"

            if not input_file.exists():
                raise ValueError(f"Missing input.txt in {case_dir}")

            if not expected_file.exists():
                raise ValueError(f"Missing expected_output.yaml in {case_dir}")

            # Load input text
            with open(input_file, "r", encoding="utf-8") as f:
                input_text = f.read()

            # Load expected output
            with open(expected_file, "r", encoding="utf-8") as f:
                expected_data = yaml.safe_load(f)

            if not isinstance(expected_data, dict):
                raise ValueError(f"Invalid expected_output.yaml format in {case_dir}")

            test_cases.append(
                {
                    "name": case_dir.name,
                    "input": input_text,
                    "expected": expected_data,
                }
            )

        if not test_cases:
            raise ValueError(f"No test cases found in {full_path}")

        return test_cases

    def _resolve_path(self, path: Path) -> Path:
        """
        Resolve path relative to base path.

        Args:
            path: Path to resolve

        Returns:
            Absolute path
        """
        path = Path(path)
        if path.is_absolute():
            return path
        return (self.base_path / path).resolve()
