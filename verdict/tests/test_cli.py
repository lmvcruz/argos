"""
Tests for verdict.cli module.

Tests CLI interface and command-line argument parsing.
"""

import sys
from unittest.mock import patch

import pytest
import yaml

from verdict.cli import main


class TestCLI:
    """Test suite for CLI interface."""

    def test_main_with_valid_config(self, temp_dir):
        """Test main function with valid configuration."""
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
            "name": "Test",
            "input": {"type": "text", "content": "hello"},
            "expected": {"text": "hello"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI
        with patch.object(sys, "argv", ["verdict", "run", "--config", str(config_file)]):
            exit_code = main()

        assert exit_code == 0

    def test_main_with_failing_tests(self, temp_dir):
        """Test main function with failing tests."""
        # Create config
        config = {
            "targets": {"test": {"callable": "tests.conftest.dummy_callable"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create failing test case
        test_case = {
            "name": "Failing test",
            "input": {"type": "text", "content": "hello"},
            "expected": {"text": "WRONG"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI
        with patch.object(sys, "argv", ["verdict", "run", "--config", str(config_file)]):
            exit_code = main()

        assert exit_code == 1

    def test_main_with_missing_config(self):
        """Test main function with missing configuration file."""
        with patch.object(sys, "argv", ["verdict", "run", "--config", "nonexistent.yaml"]):
            exit_code = main()

        assert exit_code == 2

    def test_main_with_json_format(self, temp_dir):
        """Test main function with JSON output format."""
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
            "name": "Test",
            "input": {"type": "text", "content": "test"},
            "expected": {"text": "test"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI with JSON format
        with patch.object(
            sys, "argv", ["verdict", "run", "--config", str(config_file), "--format", "json"]
        ):
            exit_code = main()

        assert exit_code == 0

    def test_main_with_no_color(self, temp_dir):
        """Test main function with --no-color flag."""
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
            "name": "Test",
            "input": {"type": "text", "content": "test"},
            "expected": {"text": "test"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI with --no-color
        with patch.object(
            sys, "argv", ["verdict", "run", "--config", str(config_file), "--no-color"]
        ):
            exit_code = main()

        assert exit_code == 0

    def test_main_with_custom_workers(self, temp_dir):
        """Test main function with custom worker count."""
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

        # Create test cases
        for i in range(1, 3):
            test_case = {
                "name": f"Test {i}",
                "input": {"type": "text", "content": f"test{i}"},
                "expected": {"text": f"test{i}"},
            }
            (temp_dir / f"case{i}.yaml").write_text(yaml.dump(test_case))

        # Run CLI with custom workers
        with patch.object(
            sys, "argv", ["verdict", "run", "--config", str(config_file), "--workers", "2"]
        ):
            exit_code = main()

        assert exit_code == 0

    def test_cli_help_message(self):
        """Test CLI help message."""
        with patch.object(sys, "argv", ["verdict", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0

    def test_cli_version(self):
        """Test CLI version flag (if implemented)."""
        # This test assumes --version flag is implemented
        # If not, this test can be skipped or modified
        with patch.object(sys, "argv", ["verdict", "--version"]):
            with pytest.raises(SystemExit):
                # Version command should exit
                main()

    def test_cli_invalid_command(self):
        """Test CLI with invalid command."""
        with patch.object(sys, "argv", ["verdict", "invalid-command"]):
            with pytest.raises(SystemExit):
                main()

    def test_cli_missing_config_argument(self):
        """Test CLI run command without --config argument."""
        with patch.object(sys, "argv", ["verdict", "run"]):
            with pytest.raises(SystemExit):
                main()

    def test_cli_invalid_format(self, temp_dir):
        """Test CLI with invalid format value."""
        # Create a dummy config file
        config_file = temp_dir / "config.yaml"
        config_file.write_text("targets: {}\ntest_suites: []")

        with patch.object(
            sys, "argv", ["verdict", "run", "--config", str(config_file), "--format", "invalid"]
        ):
            with pytest.raises(SystemExit):
                main()

    def test_main_exception_handling(self, temp_dir):
        """Test main function handles exceptions gracefully."""
        # Create invalid config (will cause error during execution)
        config = {
            "targets": {"test": {"callable": "nonexistent.module.func"}},
            "test_suites": [
                {"name": "suite1", "target": "test", "type": "single_file", "cases": ["case1.yaml"]}
            ],
        }
        config_file = temp_dir / "config.yaml"
        config_file.write_text(yaml.dump(config))

        # Create test case
        test_case = {"name": "Test", "input": {"type": "text", "content": "test"}, "expected": {}}
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI (should handle exception)
        with patch.object(sys, "argv", ["verdict", "run", "--config", str(config_file)]):
            exit_code = main()

        assert exit_code == 2

    def test_cli_output_capture(self, temp_dir, capsys):
        """Test that CLI produces output."""
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
            "name": "Test",
            "input": {"type": "text", "content": "test"},
            "expected": {"text": "test"},
        }
        (temp_dir / "case1.yaml").write_text(yaml.dump(test_case))

        # Run CLI
        with patch.object(sys, "argv", ["verdict", "run", "--config", str(config_file)]):
            main()

        captured = capsys.readouterr()
        # Should have some output
        assert len(captured.out) > 0 or len(captured.err) > 0

    def test_cli_no_command(self):
        """Test CLI with no command shows help."""
        with patch.object(sys, "argv", ["verdict"]):
            exit_code = main()

        assert exit_code == 2

    def test_cli_invalid_config_file(self):
        """Test CLI with non-existent config file."""
        with patch.object(sys, "argv", ["verdict", "run", "--config", "nonexistent.yaml"]):
            exit_code = main()

        assert exit_code == 2
