"""
Tests for verdict.runner module.

Tests TestRunner class and TestResult data class for test orchestration.
"""

from unittest.mock import MagicMock, patch

import pytest
import yaml

from verdict.runner import TestResult, TestRunner


class TestTestResult:
    """Test suite for TestResult data class."""

    def test_create_result_pass(self):
        """Test creating a passing test result."""
        result = TestResult(
            test_name="test_case_1", suite_name="suite1", passed=True, differences=[], error=None
        )

        assert result.test_name == "test_case_1"
        assert result.suite_name == "suite1"
        assert result.passed is True
        assert result.error is None
        assert len(result.differences) == 0

    def test_create_result_fail(self):
        """Test creating a failing test result."""
        result = TestResult(
            test_name="test_case_2",
            suite_name="suite1",
            passed=False,
            differences=["Field 'a': expected 1, got 2"],
            error="Value mismatch",
        )

        assert result.test_name == "test_case_2"
        assert result.suite_name == "suite1"
        assert result.passed is False
        assert result.error == "Value mismatch"
        assert len(result.differences) == 1

    def test_result_is_pass(self):
        """Test checking if result is a pass."""
        pass_result = TestResult("test", "suite", True, [], None)
        fail_result = TestResult("test", "suite", False, [], "Error")

        assert pass_result.passed is True
        assert fail_result.passed is False

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = TestResult("test", "suite", True, [], None)
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert "test_name" in result_dict
        assert "suite_name" in result_dict
        assert "passed" in result_dict


class TestTestRunner:
    """Test suite for TestRunner class."""

    def test_create_runner_with_valid_config(self, temp_dir, sample_config_dict):
        """Test creating a TestRunner with valid configuration."""
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(sample_config_dict))

        runner = TestRunner(config_file)

        assert runner.config_path == config_file
        assert runner.config is not None

    def test_create_runner_with_invalid_config(self, temp_dir):
        """Test creating a TestRunner with invalid configuration file."""
        config_file = temp_dir / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            TestRunner(config_file)

    def test_run_single_test_case_pass(self, temp_dir, mock_callable):
        """Test running a single test case that passes."""
        # Create config
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test case
        test_case = {
            "name": "Test case 1",
            "input": {"type": "text", "content": "hello"},
            "expected": {"text": "hello", "length": 5, "dummy": True},
        }
        case_file = temp_dir / "case1.yaml"
        case_file.write_text(yaml.dump(test_case))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].test_name == "Test case 1"

    def test_run_single_test_case_fail(self, temp_dir):
        """Test running a single test case that fails."""
        # Create config
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test case with wrong expected values
        test_case = {
            "name": "Test case 1",
            "input": {"type": "text", "content": "hello"},
            "expected": {"text": "WRONG", "length": 999},
        }
        case_file = temp_dir / "case1.yaml"
        case_file.write_text(yaml.dump(test_case))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 1
        assert results[0].passed is False
        assert len(results[0].differences) > 0

    def test_run_multiple_test_cases(self, temp_dir):
        """Test running multiple test cases."""
        # Create config
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {
                    "name": "suite1",
                    "target": "test",
                    "type": "single_file",
                    "cases": ["case1.yaml", "case2.yaml"],
                }
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test case 1
        test_case1 = {
            "name": "Test case 1",
            "input": {"type": "text", "content": "hello"},
            "expected": {"text": "hello"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case1))

        # Create test case 2
        test_case2 = {
            "name": "Test case 2",
            "input": {"type": "text", "content": "world"},
            "expected": {"text": "world"},
        }
        (temp_dir / "case2.yaml").write_text(yaml.dump(test_case2))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_run_folder_based_test_case(self, temp_dir):
        """Test running a folder-based test case."""
        # Create config
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "cases_in_folder", "folder": "cases"}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create folder-based test case
        case_dir = temp_dir / "cases" / "case1"
        case_dir.mkdir(parents=True)
        (case_dir / "input.txt").write_text("test")
        (case_dir / "expected_output.yaml").write_text(
            yaml.dump({"text": "test", "length": 4, "dummy": True})
        )

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 1
        assert results[0].passed is True

    def test_run_multiple_suites(self, temp_dir):
        """Test running multiple test suites."""
        # Create config with 2 suites
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {
                    "name": "suite1",
                    "target": "test",
                    "type": "single_file",
                    "cases": ["case1.yaml"],
                },
                {
                    "name": "suite2",
                    "target": "test",
                    "type": "single_file",
                    "cases": ["case2.yaml"],
                },
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test cases
        test_case1 = {
            "name": "Suite 1 case",
            "input": {"type": "text", "content": "a"},
            "expected": {"text": "a"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case1))

        test_case2 = {
            "name": "Suite 2 case",
            "input": {"type": "text", "content": "b"},
            "expected": {"text": "b"},
        }
        (temp_dir / "case2.yaml").write_text(yaml.dump(test_case2))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_sequential_execution(self, temp_dir):
        """Test sequential execution (max_workers=1)."""
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {
                    "name": "suite1",
                    "target": "test",
                    "type": "single_file",
                    "cases": ["case1.yaml", "case2.yaml"],
                }
            ],
            "settings": {"max_workers": 1},
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test cases
        for i in range(1, 3):
            test_case = {
                "name": f"Test {i}",
                "input": {"type": "text", "content": f"test{i}"},
                "expected": {"text": f"test{i}"},
            }
            (temp_dir / f"case{i}.yaml").write_text(yaml.dump(test_case))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 2
        assert all(r.passed for r in results)

    def test_parallel_execution(self, temp_dir):
        """Test parallel execution (max_workers>1)."""
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {
                    "name": "suite1",
                    "target": "test",
                    "type": "single_file",
                    "cases": ["case1.yaml", "case2.yaml", "case3.yaml"],
                }
            ],
            "settings": {"max_workers": 2},
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test cases
        for i in range(1, 4):
            test_case = {
                "name": f"Test {i}",
                "input": {"type": "text", "content": f"test{i}"},
                "expected": {"text": f"test{i}"},
            }
            (temp_dir / f"case{i}.yaml").write_text(yaml.dump(test_case))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_test_case_execution_error(self, temp_dir):
        """Test handling of execution errors in test cases."""

        # Create a target that raises an exception
        def failing_callable(input_text: str) -> dict:
            raise RuntimeError("Execution failed")

        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        test_case = {
            "name": "Failing test",
            "input": {"type": "text", "content": "test"},
            "expected": {"result": "success"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Mock the executor to raise exception
        with patch("verdict.runner.TargetExecutor") as mock_executor:
            mock_instance = MagicMock()
            mock_instance.execute_callable.side_effect = RuntimeError("Execution failed")
            mock_executor.return_value = mock_instance

            runner = TestRunner(config_file)
            results = runner.run_all()

            assert len(results) == 1
            assert results[0].passed is False
            assert results[0].error is not None

    def test_empty_test_suite(self, temp_dir):
        """Test behavior with empty test suite (no cases)."""
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "empty_suite", "target": "test", "type": "single_file", "cases": []}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 0

    def test_result_duration_recorded(self, temp_dir):
        """Test that execution duration is recorded for each test."""
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        test_case = {
            "name": "Test",
            "input": {"type": "text", "content": "test"},
            "expected": {"text": "test"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        runner = TestRunner(config_file)
        results = runner.run_all()

        assert len(results) == 1
        assert results[0].passed is True
