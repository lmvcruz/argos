"""
Tests for verdict.loader module.

Tests ConfigLoader and TestCaseLoader classes for loading and validating
YAML configuration files and test cases.
"""

from pathlib import Path

import pytest
import yaml

from verdict.loader import ConfigLoader, TestCaseLoader


class TestConfigLoader:
    """Test suite for ConfigLoader class."""

    def test_load_valid_config(self, temp_dir, sample_config_dict):
        """Test loading a valid configuration file."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(sample_config_dict))

        loader = ConfigLoader(config_file)
        config = loader.load()

        assert config == sample_config_dict
        assert "targets" in config
        assert "test_suites" in config

    def test_load_config_missing_file(self, temp_dir):
        """Test loading a non-existent configuration file."""
        config_file = temp_dir / "nonexistent.yaml"

        loader = ConfigLoader(config_file)

        with pytest.raises(FileNotFoundError):
            loader.load()

    def test_load_config_invalid_yaml(self, temp_dir):
        """Test loading a file with invalid YAML syntax."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:\n  - broken")

        loader = ConfigLoader(config_file)

        with pytest.raises(yaml.YAMLError):
            loader.load()

    def test_validate_config_missing_targets(self, temp_dir):
        """Test validation fails when targets section is missing."""
        config = {
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": []}
            ]
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        loader = ConfigLoader(config_file)

        with pytest.raises(ValueError, match="Missing required.*targets"):
            loader.load()

    def test_validate_config_missing_test_suites(self, temp_dir):
        """Test validation fails when test_suites section is missing."""
        config = {
            "targets": {
                "test": {"callable": "test.module.func"}
            }
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        loader = ConfigLoader(config_file)

        with pytest.raises(ValueError, match="Missing required.*test_suites"):
            loader.load()

    def test_validate_config_invalid_target_reference(self, temp_dir, sample_config_dict):
        """Test validation fails when suite references non-existent target."""
        config = sample_config_dict.copy()
        config["test_suites"][0]["target"] = "nonexistent_target"

        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        loader = ConfigLoader(config_file)

        with pytest.raises(ValueError, match="references undefined target"):
            loader.load()

    def test_validate_config_missing_callable(self, temp_dir):
        """Test validation fails when target is missing callable field."""
        config = {
            "targets": {
                "test": {}  # Missing callable
            },
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": []}
            ]
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        loader = ConfigLoader(config_file)

        with pytest.raises(ValueError, match="missing.*callable"):
            loader.load()

    def test_validate_config_empty_test_suites(self, temp_dir):
        """Test validation fails when test_suites is empty."""
        config = {
            "targets": {"test": {"callable": "test.func"}},
            "test_suites": []
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        loader = ConfigLoader(config_file)

        with pytest.raises(ValueError, match="at least one test suite"):
            loader.load()

    def test_get_config_dir(self, temp_dir, sample_config_dict):
        """Test getting the configuration directory path."""
        config_file = temp_dir / "subdir" / "config.yaml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(yaml.dump(sample_config_dict))

        loader = ConfigLoader(config_file)
        config_dir = loader.get_config_dir()

        assert config_dir == config_file.parent
        assert config_dir.name == "subdir"


class TestTestCaseLoader:
    """Test suite for TestCaseLoader class."""

    def test_load_single_file_case(self, temp_dir, sample_test_case_dict):
        """Test loading a single-file test case."""
        case_file = temp_dir / "case1.yaml"
        case_file.write_text(yaml.dump(sample_test_case_dict))

        loader = TestCaseLoader(temp_dir)
        test_case = loader.load_test_case(case_file)

        assert test_case["name"] == sample_test_case_dict["name"]
        assert test_case["input"] == sample_test_case_dict["input"]
        assert test_case["expected"] == sample_test_case_dict["expected"]

    def test_load_folder_case(self, temp_dir):
        """Test loading a folder-based test case."""
        case_dir = temp_dir / "test_case_folder"
        case_dir.mkdir()

        input_file = case_dir / "input.txt"
        input_file.write_text("test input content")

        expected_file = case_dir / "expected_output.yaml"
        expected_file.write_text(yaml.dump({"result": "success", "value": 42}))

        loader = TestCaseLoader(temp_dir)
        test_case = loader.load_test_case(case_dir)

        assert test_case["name"] == "test_case_folder"
        assert test_case["input"]["type"] == "text"
        assert test_case["input"]["content"] == "test input content"
        assert test_case["expected"]["result"] == "success"
        assert test_case["expected"]["value"] == 42

    def test_load_folder_case_missing_input(self, temp_dir):
        """Test loading folder case fails when input.txt is missing."""
        case_dir = temp_dir / "incomplete_case"
        case_dir.mkdir()

        expected_file = case_dir / "expected_output.yaml"
        expected_file.write_text(yaml.dump({"result": "success"}))

        loader = TestCaseLoader(temp_dir)

        with pytest.raises(FileNotFoundError, match="input.txt"):
            loader.load_test_case(case_dir)

    def test_load_folder_case_missing_expected(self, temp_dir):
        """Test loading folder case fails when expected_output.yaml is missing."""
        case_dir = temp_dir / "incomplete_case"
        case_dir.mkdir()

        input_file = case_dir / "input.txt"
        input_file.write_text("test input")

        loader = TestCaseLoader(temp_dir)

        with pytest.raises(FileNotFoundError, match="expected_output.yaml"):
            loader.load_test_case(case_dir)

    def test_load_nonexistent_case(self, temp_dir):
        """Test loading a non-existent test case."""
        loader = TestCaseLoader(temp_dir)

        with pytest.raises(FileNotFoundError):
            loader.load_test_case(temp_dir / "nonexistent.yaml")

    def test_validate_test_case_missing_name(self, temp_dir):
        """Test validation fails when test case is missing name field."""
        invalid_case = {
            "input": {"type": "text", "content": "test"},
            "expected": {"result": "success"}
        }
        case_file = temp_dir / "invalid.yaml"
        case_file.write_text(yaml.dump(invalid_case))

        loader = TestCaseLoader(temp_dir)

        with pytest.raises(ValueError, match="missing.*name"):
            test_case = loader.load_test_case(case_file)
            loader.validate_test_case(test_case)

    def test_validate_test_case_missing_input(self, temp_dir):
        """Test validation fails when test case is missing input field."""
        invalid_case = {
            "name": "Test",
            "expected": {"result": "success"}
        }
        case_file = temp_dir / "invalid.yaml"
        case_file.write_text(yaml.dump(invalid_case))

        loader = TestCaseLoader(temp_dir)

        with pytest.raises(ValueError, match="missing.*input"):
            test_case = loader.load_test_case(case_file)
            loader.validate_test_case(test_case)

    def test_validate_test_case_missing_expected(self, temp_dir):
        """Test validation fails when test case is missing expected field."""
        invalid_case = {
            "name": "Test",
            "input": {"type": "text", "content": "test"}
        }
        case_file = temp_dir / "invalid.yaml"
        case_file.write_text(yaml.dump(invalid_case))

        loader = TestCaseLoader(temp_dir)

        with pytest.raises(ValueError, match="missing.*expected"):
            test_case = loader.load_test_case(case_file)
            loader.validate_test_case(test_case)

    def test_load_case_with_relative_path(self, temp_dir, sample_test_case_dict):
        """Test loading test case with relative path from config directory."""
        subdir = temp_dir / "cases"
        subdir.mkdir()

        case_file = subdir / "case1.yaml"
        case_file.write_text(yaml.dump(sample_test_case_dict))

        loader = TestCaseLoader(temp_dir)
        test_case = loader.load_test_case(Path("cases") / "case1.yaml")

        assert test_case["name"] == sample_test_case_dict["name"]

    def test_load_multiple_cases_from_folder(self, temp_dir):
        """Test loading multiple test cases from a cases folder."""
        cases_dir = temp_dir / "cases"
        cases_dir.mkdir()

        # Create case 1
        case1_dir = cases_dir / "case1"
        case1_dir.mkdir()
        (case1_dir / "input.txt").write_text("input 1")
        (case1_dir / "expected_output.yaml").write_text(yaml.dump({"value": 1}))

        # Create case 2
        case2_dir = cases_dir / "case2"
        case2_dir.mkdir()
        (case2_dir / "input.txt").write_text("input 2")
        (case2_dir / "expected_output.yaml").write_text(yaml.dump({"value": 2}))

        loader = TestCaseLoader(temp_dir)

        case1 = loader.load_test_case(Path("cases") / "case1")
        case2 = loader.load_test_case(Path("cases") / "case2")

        assert case1["expected"]["value"] == 1
        assert case2["expected"]["value"] == 2
