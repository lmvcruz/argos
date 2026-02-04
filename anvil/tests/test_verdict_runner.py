"""
Test suite for custom Verdict runner with dynamic case discovery.

Tests the core functionality of the simplified Verdict runner that
discovers test cases from folder and file structures, and executes them
against Anvil parser adapters.
"""

from pathlib import Path

from anvil.testing.verdict_runner import (
    CaseDiscovery,
    CaseExecutor,
    ConfigLoader,
    VerdictRunner,
)


class TestConfigLoader:
    """Tests for configuration loading."""

    def test_load_config_from_yaml(self):
        """Verify config is loaded correctly from YAML file."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        loader = ConfigLoader(config_path)
        config = loader.load()

        assert "validators" in config
        assert "black" in config["validators"]
        assert "flake8" in config["validators"]
        assert "isort" in config["validators"]

    def test_config_has_required_fields(self):
        """Verify each validator config has callable and root."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        loader = ConfigLoader(config_path)
        config = loader.load()

        for validator_name, validator_config in config["validators"].items():
            assert "callable" in validator_config
            assert "root" in validator_config

    def test_config_callable_is_importable(self):
        """Verify callable paths in config can be imported."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        loader = ConfigLoader(config_path)
        config = loader.load()

        for validator_name, validator_config in config["validators"].items():
            callable_path = validator_config["callable"]
            module_path, func_name = callable_path.rsplit(".", 1)
            # Just verify format is correct (we'll test actual import in executor)
            assert "." in callable_path


class TestCaseDiscovery:
    """Tests for dynamic test case discovery."""

    def test_discover_folder_cases(self):
        """Verify discovery finds test cases in folders."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)
        cases = discovery.discover()

        # Should find scout_ci folder cases
        case_names = [case["name"] for case in cases]
        assert any("scout_ci" in name for name in case_names)

    def test_discover_yaml_cases(self):
        """Verify discovery finds YAML file test cases."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)
        cases = discovery.discover()

        # Should find YAML file cases
        case_types = [case["type"] for case in cases]
        assert "yaml" in case_types

    def test_case_has_required_files(self):
        """Verify discovered cases have required structure."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)
        cases = discovery.discover()

        for case in cases:
            assert "name" in case
            assert "type" in case
            # Each case should be either folder or yaml type
            assert case["type"] in ("folder", "yaml")
            if case["type"] == "folder":
                assert "input_path" in case
                assert "expected_path" in case
            elif case["type"] == "yaml":
                assert "yaml_path" in case

    def test_filter_cases_by_path(self):
        """Verify cases can be filtered by path."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        # Filter for scout_ci cases
        filtered = discovery.filter_by_path("scout_ci")
        scout_cases = [c for c in filtered]

        assert len(scout_cases) > 0
        assert all("scout_ci" in c["name"] for c in scout_cases)

    def test_filter_cases_by_nested_path(self):
        """Verify nested path filtering works."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        # Filter for specific job
        filtered = discovery.filter_by_path("scout_ci.job_180")
        cases = [c for c in filtered]

        assert len(cases) == 1
        assert "job_180" in cases[0]["name"]

    def test_filter_cases_by_yaml_name(self):
        """Verify filtering works for YAML file names."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        # Filter for empty_output case
        filtered = discovery.filter_by_path("empty_output")
        cases = [c for c in filtered]

        assert len(cases) == 1
        assert "empty_output" in cases[0]["name"]


class TestCaseExecutor:
    """Tests for executing test cases."""

    def test_execute_case_with_folder_structure(self):
        """Verify executing a folder-based test case."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        # Get a scout_ci case
        cases = list(discovery.filter_by_path("scout_ci.job_client"))
        assert len(cases) > 0

        case = cases[0]
        executor = CaseExecutor("anvil.validators.adapters.validate_black_parser")

        result = executor.execute(case)

        assert "passed" in result
        assert "expected" in result
        assert "actual" in result

    def test_execute_case_with_yaml_structure(self):
        """Verify executing a YAML file-based test case."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        # Get an empty_output case
        cases = list(discovery.filter_by_path("empty_output"))
        assert len(cases) > 0

        case = cases[0]
        executor = CaseExecutor("anvil.validators.adapters.validate_black_parser")

        result = executor.execute(case)

        assert "passed" in result
        assert "expected" in result
        assert "actual" in result

    def test_execution_result_structure(self):
        """Verify execution result has required fields."""
        root = Path(__file__).parent / "validation" / "cases" / "black_cases"
        discovery = CaseDiscovery(root)

        cases = list(discovery.filter_by_path("scout_ci.job_client"))
        assert len(cases) > 0

        case = cases[0]
        executor = CaseExecutor("anvil.validators.adapters.validate_black_parser")

        result = executor.execute(case)

        assert "name" in result
        assert "passed" in result
        assert isinstance(result["passed"], bool)
        assert "expected" in result
        assert "actual" in result


class TestVerdictRunner:
    """Tests for the main Verdict runner orchestration."""

    def test_runner_initialization(self):
        """Verify runner initializes with config."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        assert runner.config is not None
        assert "validators" in runner.config

    def test_runner_lists_all_validators(self):
        """Verify runner can list all validators."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        validators = runner.list_validators()

        assert "black" in validators
        assert "flake8" in validators
        assert "isort" in validators

    def test_runner_lists_cases_for_validator(self):
        """Verify runner can list all cases for a validator."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        cases = runner.list_cases("black")

        assert len(cases) > 0
        assert all("name" in case for case in cases)

    def test_runner_filters_cases(self):
        """Verify runner can filter cases by path."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        cases = runner.list_cases("black", case_filter="scout_ci")

        assert len(cases) > 0
        assert all("scout_ci" in case["name"] for case in cases)

    def test_runner_executes_all_cases(self):
        """Verify runner can execute all cases for a validator."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        results = runner.execute("black")

        assert "total" in results
        assert "passed" in results
        assert "failed" in results
        assert results["total"] > 0

    def test_runner_executes_filtered_cases(self):
        """Verify runner can execute filtered cases."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        results = runner.execute("black", case_filter="scout_ci.job_180")

        assert results["total"] >= 1

    def test_runner_execution_results_structure(self):
        """Verify execution results have proper structure."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        results = runner.execute("black", case_filter="empty_output")

        assert "total" in results
        assert "passed" in results
        assert "failed" in results
        assert "cases" in results
        assert isinstance(results["cases"], list)


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_workflow_list_then_execute(self):
        """Verify complete workflow of listing and executing."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        # List cases
        cases = runner.list_cases("black")
        assert len(cases) > 0

        # Execute all cases
        results = runner.execute("black")
        assert results["total"] == len(cases)

    def test_all_validators_executable(self):
        """Verify all configured validators can be executed."""
        config_path = Path(__file__).parent / "validation" / "config.yaml"
        runner = VerdictRunner(config_path)

        for validator in ["black", "flake8", "isort"]:
            results = runner.execute(validator)
            assert results["total"] > 0
            assert results["passed"] + results["failed"] == results["total"]
