"""
Custom Verdict runner with dynamic case discovery.

This module provides a simplified test discovery and execution framework
that discovers test cases from folder and YAML file structures, and
executes them against configured validator adapters.

Test case structure:
- Folder cases: Any folder containing input.txt and expected_output.yaml
- YAML cases: Any YAML file containing 'input' and 'expected_output' keys

Config structure (YAML):
    validators:
      validator_name:
        callable: module.path.to.adapter_function
        root: path/to/cases
"""

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import yaml


class ConfigLoader:
    """Loads configuration from YAML file."""

    def __init__(self, config_path: Path):
        """
        Initialize config loader.

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)

    def load(self) -> Dict[str, Any]:
        """
        Load and parse config file.

        Returns:
            Configuration dictionary with validators and their settings
        """
        with open(self.config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config


class CaseDiscovery:
    """Discovers test cases from folder and file structures."""

    def __init__(self, root: Path):
        """
        Initialize case discovery.

        Args:
            root: Root directory to discover cases from
        """
        self.root = Path(root)

    def discover(self) -> List[Dict[str, Any]]:
        """
        Discover all test cases under root.

        Returns:
            List of case dictionaries with name, input_path, expected_path
        """
        cases = []

        # Discover folder-based cases
        cases.extend(self._discover_folder_cases())

        # Discover YAML-based cases
        cases.extend(self._discover_yaml_cases())

        return cases

    def _discover_folder_cases(self) -> List[Dict[str, Any]]:
        """
        Discover folder-based test cases.

        A folder is a test case if it contains input.txt and/or expected_output.yaml.
        Uses folder path as case name (relative to root).

        Returns:
            List of folder-based case dictionaries
        """
        cases = []

        for folder in sorted(self.root.rglob("*")):
            if not folder.is_dir():
                continue

            input_file = folder / "input.txt"
            expected_file = folder / "expected_output.yaml"

            # Must have at least one file
            if not input_file.exists() and not expected_file.exists():
                continue

            # Calculate relative path for case name
            relative_path = folder.relative_to(self.root)
            case_name = str(relative_path).replace("\\", ".")

            cases.append(
                {
                    "name": case_name,
                    "type": "folder",
                    "input_path": input_file,
                    "expected_path": expected_file,
                    "folder": folder,
                }
            )

        return cases

    def _discover_yaml_cases(self) -> List[Dict[str, Any]]:
        """
        Discover YAML file-based test cases.

        Each YAML file at root level is a test case.
        Uses filename (without .yaml) as case name.

        Returns:
            List of YAML-based case dictionaries
        """
        cases = []

        for yaml_file in sorted(self.root.glob("*.yaml")):
            case_name = yaml_file.stem

            cases.append(
                {
                    "name": case_name,
                    "type": "yaml",
                    "yaml_path": yaml_file,
                }
            )

        return cases

    def filter_by_path(self, path_filter: str) -> Iterator[Dict[str, Any]]:
        """
        Filter cases by path pattern.

        Supports hierarchical filtering:
        - "scout_ci" matches all cases under scout_ci folder
        - "scout_ci.job_180" matches specific nested case
        - "empty_output" matches YAML file case

        Args:
            path_filter: Case path pattern to filter by

        Yields:
            Matching case dictionaries
        """
        cases = self.discover()

        for case in cases:
            if case["name"] == path_filter:
                yield case
            elif case["name"].startswith(path_filter + "."):
                yield case


class CaseExecutor:
    """Executes test cases against validators."""

    def __init__(self, callable_path: str, working_dir: Optional[Path] = None):
        """
        Initialize executor with callable adapter.

        Args:
            callable_path: Module path to adapter function
                (e.g., 'anvil.validators.adapters.validate_black_parser')
            working_dir: Working directory for relative paths (defaults to current dir)
        """
        self.callable_path = callable_path
        self.working_dir = working_dir or Path(".")
        self._adapter = None

    def _get_adapter(self) -> Any:
        """
        Import and cache adapter callable.

        Returns:
            Adapter function
        """
        if self._adapter is None:
            module_path, func_name = self.callable_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            self._adapter = getattr(module, func_name)
        return self._adapter

    def execute(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test case.

        Args:
            case: Case dictionary with input and expected output

        Returns:
            Result dictionary with passed/failed status and details
        """
        adapter = self._get_adapter()

        # Load input
        if case["type"] == "folder":
            input_text = self._load_file(case["input_path"])
            expected_data = self._load_yaml_file(case["expected_path"])
        else:  # yaml
            yaml_data = self._load_yaml_file(case["yaml_path"])
            input_data = yaml_data.get("input", "")
            # Handle both flat string and nested {type, content} structure
            if isinstance(input_data, dict):
                input_text = input_data.get("content", "")
            else:
                input_text = input_data
            expected_data = yaml_data.get("expected", {})

        # Execute adapter
        actual_data = adapter(input_text)

        # Compare results
        passed = actual_data == expected_data

        return {
            "name": case["name"],
            "passed": passed,
            "expected": expected_data,
            "actual": actual_data,
        }

    def _load_file(self, path: Path) -> str:
        """
        Load text file content.

        Args:
            path: File path

        Returns:
            File content as string, empty string if file doesn't exist
        """
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """
        Load YAML file content.

        Args:
            path: File path

        Returns:
            Parsed YAML as dictionary, empty dict if file doesn't exist
        """
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}


class VerdictRunner:
    """Main runner that orchestrates discovery and execution."""

    def __init__(self, config_path: Path):
        """
        Initialize Verdict runner.

        Args:
            config_path: Path to config.yaml
        """
        self.config_path = Path(config_path)
        self.config = ConfigLoader(config_path).load()
        self.validators = self.config.get("validators", {})

    def list_validators(self) -> List[str]:
        """
        List all configured validators.

        Returns:
            List of validator names
        """
        return list(self.validators.keys())

    def list_cases(self, validator: str, case_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all test cases for a validator.

        Args:
            validator: Validator name
            case_filter: Optional case path pattern to filter by

        Returns:
            List of case dictionaries
        """
        if validator not in self.validators:
            raise ValueError(f"Unknown validator: {validator}")

        validator_config = self.validators[validator]
        root = Path(validator_config["root"])

        # Resolve relative paths from config file directory
        if not root.is_absolute():
            root = self.config_path.parent / root

        discovery = CaseDiscovery(root)

        if case_filter:
            cases = list(discovery.filter_by_path(case_filter))
        else:
            cases = discovery.discover()

        return cases

    def execute(self, validator: str, case_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute test cases for a validator.

        Args:
            validator: Validator name
            case_filter: Optional case path pattern to filter by

        Returns:
            Results dictionary with summary and detailed case results
        """
        if validator not in self.validators:
            raise ValueError(f"Unknown validator: {validator}")

        validator_config = self.validators[validator]
        root = Path(validator_config["root"])

        # Resolve relative paths from config file directory
        if not root.is_absolute():
            root = self.config_path.parent / root

        callable_path = validator_config["callable"]

        discovery = CaseDiscovery(root)
        executor = CaseExecutor(callable_path)

        if case_filter:
            cases = list(discovery.filter_by_path(case_filter))
        else:
            cases = discovery.discover()

        # Execute all cases
        case_results = []
        passed_count = 0
        failed_count = 0

        for case in cases:
            result = executor.execute(case)
            case_results.append(result)

            if result["passed"]:
                passed_count += 1
            else:
                failed_count += 1

        return {
            "validator": validator,
            "total": len(case_results),
            "passed": passed_count,
            "failed": failed_count,
            "cases": case_results,
        }


class VerdictCLI:
    """Command-line interface for Verdict runner."""

    def __init__(self, config_path: Path):
        """
        Initialize CLI.

        Args:
            config_path: Path to config.yaml
        """
        self.runner = VerdictRunner(config_path)

    def parse_args(self, args: List[str]) -> argparse.Namespace:
        """
        Parse command-line arguments.

        Args:
            args: List of command-line arguments

        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description="Verdict - Test case discovery and validation",
            prog="verdict",
        )

        parser.add_argument(
            "--list",
            action="store_true",
            help="List test cases instead of running them",
        )
        parser.add_argument(
            "validator",
            nargs="?",
            help="Validator name (optional)",
        )
        parser.add_argument(
            "--cases",
            help="Case path pattern to filter by (e.g., scout_ci.job_180)",
        )

        parsed = parser.parse_args(args)
        return parsed

    def handle_list(self, validator: Optional[str] = None) -> int:
        """
        Handle --list command.

        Args:
            validator: Optional validator name

        Returns:
            Exit code (0 for success)
        """
        if validator:
            cases = self.runner.list_cases(validator)
            print(f"\n{validator} cases:")
            print("=" * 60)
            for case in cases:
                print(f"  {case['name']}")
        else:
            # List all validators
            validators = self.runner.list_validators()
            print("\nAvailable validators:")
            print("=" * 60)
            for val in validators:
                print(f"  {val}")

        return 0

    def handle_validate(
        self, validator: Optional[str] = None, case_filter: Optional[str] = None
    ) -> int:
        """
        Handle --validate command.

        Args:
            validator: Optional validator name
            case_filter: Optional case path pattern

        Returns:
            Exit code (0 if all passed, 1 if any failed)
        """
        if validator:
            validators = [validator]
        else:
            validators = self.runner.list_validators()

        all_passed = True

        for val in validators:
            results = self.runner.execute(val, case_filter)

            # Print results
            self._print_results(results)

            if results["failed"] > 0:
                all_passed = False

        return 0 if all_passed else 1

    def _print_results(self, results: Dict[str, Any]) -> None:
        """
        Print test results.

        Args:
            results: Results dictionary from execute()
        """
        print(f"\n{'=' * 70}")
        print(f"{results['validator'].upper()}")
        print(f"{'=' * 70}")

        for case in results["cases"]:
            status = "PASS" if case["passed"] else "FAIL"
            print(f"  [{status}] {case['name']}")

            if not case["passed"]:
                print(f"  Expected: {json.dumps(case['expected'], indent=2)[:100]}...")
                print(f"  Got:      {json.dumps(case['actual'], indent=2)[:100]}...")

        print()
        print(
            f"Total: {results['total']} | "
            f"Passed: {results['passed']} | "
            f"Failed: {results['failed']}"
        )

    def run(self, args: List[str]) -> int:
        """
        Run CLI.

        Args:
            args: Command-line arguments

        Returns:
            Exit code
        """
        parsed = self.parse_args(args)

        if parsed.list:
            return self.handle_list(parsed.validator)
        else:
            return self.handle_validate(parsed.validator, parsed.cases)


def main() -> int:
    """Main entry point for verdict CLI."""
    config_path = Path(__file__).parent.parent.parent / "tests" / "validation" / "config.yaml"

    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return 1

    cli = VerdictCLI(config_path)
    return cli.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
