"""
Bridge between Scout (CI log extraction) and Anvil (parser capabilities).

This module enables Scout to leverage Anvil's validator parsers without
writing to Anvil's database. Scout extracts validator output from CI logs
and delegates parsing to Anvil's specialized parsers. All results are
stored in Scout's database.

Architecture:
    Scout fetch → GitHub → Scout DB (metadata + raw logs)
    Scout parse → Extract validator output → AnvilBridge (use Anvil parsers) → Scout DB (results)

    Anvil DB: LOCAL executions only
    Scout DB: CI executions only
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import Anvil parsers (lazy loading to avoid hard dependency)
_ANVIL_PARSERS = None


def _get_anvil_parsers():
    """
    Lazy load Anvil parsers to avoid hard dependency.

    Returns:
        Dictionary mapping validator names to parser classes
    """
    global _ANVIL_PARSERS
    if _ANVIL_PARSERS is not None:
        return _ANVIL_PARSERS

    try:
        from anvil.parsers.autoflake_parser import AutoflakeParser
        from anvil.parsers.black_parser import BlackParser
        from anvil.parsers.clang_format_parser import ClangFormatParser
        from anvil.parsers.clang_tidy_parser import ClangTidyParser
        from anvil.parsers.cppcheck_parser import CppcheckParser
        from anvil.parsers.cpplint_parser import CpplintParser
        from anvil.parsers.coverage_parser import CoverageParser
        from anvil.parsers.flake8_parser import Flake8Parser
        from anvil.parsers.gtest_parser import GTestParser
        from anvil.parsers.isort_parser import IsortParser
        from anvil.parsers.pylint_parser import PylintParser
        from anvil.parsers.pytest_parser import PytestParser
        from anvil.parsers.radon_parser import RadonParser
        from anvil.parsers.vulture_parser import VultureParser

        _ANVIL_PARSERS = {
            "black": BlackParser,
            "flake8": Flake8Parser,
            "isort": IsortParser,
            "pylint": PylintParser,
            "pytest": PytestParser,
            "autoflake": AutoflakeParser,
            "vulture": VultureParser,
            "clang-tidy": ClangTidyParser,
            "clang-format": ClangFormatParser,
            "cpplint": CpplintParser,
            "cppcheck": CppcheckParser,
            "gtest": GTestParser,
            "coverage": CoverageParser,
            "radon": RadonParser,
        }
        return _ANVIL_PARSERS

    except ImportError:
        print(
            "Warning: Anvil not installed. Parser functionality disabled.",
            file=sys.stderr,
        )
        print("Install with: pip install -e path/to/anvil", file=sys.stderr)
        return {}


class AnvilBridge:
    """
    Parser adapter bridging Scout CI log extraction and Anvil validator parsers.

    This class DOES NOT write to Anvil's database. It only uses Anvil's
    parsing capabilities to parse validator output extracted from CI logs.
    All parsed results are returned to Scout for storage in Scout DB.

    Usage:
        bridge = AnvilBridge()
        result = bridge.parse_validator_output("black", black_output, files)
        # Scout saves result to Scout DB
    """

    def __init__(self):
        """
        Initialize the AnvilBridge parser adapter.

        No database connections are created. This is a stateless parser adapter.
        """
        self.parsers = _get_anvil_parsers()

    def get_supported_validators(self) -> List[str]:
        """
        Get list of supported validator names.

        Returns:
            List of validator names that can be parsed
        """
        return list(self.parsers.keys())

    def parse_validator_output(
        self,
        validator_name: str,
        output: str,
        files: Optional[List[Path]] = None,
        output_format: str = "text",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Parse validator output using Anvil's specialized parsers.

        This method delegates parsing to Anvil but does NOT write to any database.
        The caller (Scout) is responsible for storing results in Scout DB.

        Args:
            validator_name: Name of validator (black, flake8, pytest, etc.)
            output: Raw output from the validator
            files: List of files that were validated (optional)
            output_format: Output format (text, json, xml)
            **kwargs: Additional parser-specific arguments

        Returns:
            Dictionary with parsed results:
            {
                "validator_name": str,
                "passed": bool,
                "errors": List[Dict],  # Issue dictionaries
                "warnings": List[Dict],  # Issue dictionaries
                "execution_time": float,
                "files_checked": int,
                "metadata": Dict (optional)
            }

        Raises:
            ValueError: If validator is not supported
            Exception: If parsing fails
        """
        if validator_name not in self.parsers:
            raise ValueError(
                f"Unsupported validator: {validator_name}. "
                f"Supported: {', '.join(self.get_supported_validators())}"
            )

        parser_class = self.parsers[validator_name]
        files = files or []

        try:
            # Different parsers have different APIs
            if validator_name == "black":
                result = parser_class.parse_text(
                    output, files, diff_output=kwargs.get("diff_output")
                )
            elif validator_name == "flake8":
                if output_format == "json":
                    result = parser_class.parse_json(output, files)
                else:
                    result = parser_class.parse_text(output, files)
            elif validator_name == "isort":
                result = parser_class.parse_text(
                    output, files, diff_output=kwargs.get("diff_output")
                )
            elif validator_name == "pylint":
                result = parser_class.parse_json(output, files)
            elif validator_name == "pytest":
                result = parser_class.parse_json(
                    output, files, config=kwargs.get("config", {})
                )
            elif validator_name == "autoflake":
                result = parser_class.parse_text(output, files)
            elif validator_name == "vulture":
                result = parser_class.parse_text(output, files)
            elif validator_name == "clang-tidy":
                parser = parser_class()
                result = parser.parse_yaml(output, files)
            elif validator_name == "clang-format":
                parser = parser_class()
                result = parser.parse_output(
                    output, [str(f) for f in files], exit_code=kwargs.get("exit_code", 0)
                )
            elif validator_name == "cpplint":
                parser = parser_class()
                result = parser.parse_output(output, [str(f) for f in files])
            elif validator_name == "cppcheck":
                parser = parser_class()
                result = parser.parse_xml(output, [str(f) for f in files])
            elif validator_name == "gtest":
                parser = parser_class()
                result = parser.parse_output(output, kwargs.get("test_binary", ""))
            elif validator_name == "coverage":
                parser = parser_class()
                result = parser.parse_coverage_xml(output)  # output is XML path
            elif validator_name == "radon":
                metric = kwargs.get("metric", "cc")  # cc, mi, raw
                if metric == "cc":
                    result = parser_class.parse_cc(output, files)
                elif metric == "mi":
                    result = parser_class.parse_mi(output, files)
                else:  # raw
                    result = parser_class.parse_raw(output, files)
            else:
                # Generic fallback (shouldn't happen with current parsers)
                raise ValueError(f"Parser implementation missing for: {validator_name}")

            # Convert ValidationResult to dictionary
            return result.to_dict()

        except Exception as e:
            raise Exception(f"Failed to parse {validator_name} output: {e}") from e

    def parse_ci_log_section(
        self, validator_name: str, log_section: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Parse a section of CI log containing validator output.

        Convenience method that handles empty/None log sections gracefully.

        Args:
            validator_name: Name of validator
            log_section: Extracted section of CI log containing validator output
            **kwargs: Additional parser arguments

        Returns:
            Parsed result dictionary, or None if log section is empty
        """
        if not log_section or not log_section.strip():
            return None

        return self.parse_validator_output(validator_name, log_section, **kwargs)


class AnvilLogExtractor:
    """
    Helper class for extracting validator output from CI logs.

    This class provides utilities to identify and extract validator-specific
    output sections from full CI job logs. Scout uses this to isolate
    validator output before delegating parsing to AnvilBridge.
    """

    # Common validator output patterns
    VALIDATOR_PATTERNS = {
        "black": {
            "start": r"(?:Running|Executing) black",
            "end": r"(?:black.*(?:passed|failed|done)|---)",
        },
        "flake8": {
            "start": r"(?:Running|Executing) flake8",
            "end": r"(?:flake8.*(?:passed|failed|done)|---)",
        },
        "isort": {
            "start": r"(?:Running|Executing) isort",
            "end": r"(?:isort.*(?:passed|failed|done)|---)",
        },
        "pylint": {
            "start": r"(?:Running|Executing) pylint",
            "end": r"(?:Your code has been rated|---)",
        },
        "pytest": {
            "start": r"===+ test session starts ===+",
            "end": r"===+.*(?:passed|failed|error).*in.*===+",
        },
        "autoflake": {
            "start": r"(?:Running|Executing) autoflake",
            "end": r"(?:autoflake.*(?:passed|failed|done)|---)",
        },
        "clang-tidy": {
            "start": r"(?:Running|Executing) clang-tidy",
            "end": r"(?:clang-tidy.*(?:passed|failed|done)|---)",
        },
        "clang-format": {
            "start": r"(?:Running|Executing) clang-format",
            "end": r"(?:clang-format.*(?:passed|failed|done)|---)",
        },
    }

    @staticmethod
    def extract_validator_output(log_content: str, validator_name: str) -> Optional[str]:
        """
        Extract validator-specific output from full CI log.

        Args:
            log_content: Full CI job log content
            validator_name: Name of validator to extract

        Returns:
            Extracted validator output section, or None if not found
        """
        if validator_name not in AnvilLogExtractor.VALIDATOR_PATTERNS:
            return None

        pattern = AnvilLogExtractor.VALIDATOR_PATTERNS[validator_name]
        start_pattern = pattern["start"]
        end_pattern = pattern["end"]

        # Find start marker
        start_match = re.search(start_pattern, log_content, re.IGNORECASE)
        if not start_match:
            return None

        start_pos = start_match.start()

        # Find end marker (search from start position)
        end_match = re.search(end_pattern, log_content[start_pos:], re.IGNORECASE)
        if not end_match:
            # No end marker found, take rest of log
            return log_content[start_pos:]

        end_pos = start_pos + end_match.end()
        return log_content[start_pos:end_pos]

    @staticmethod
    def detect_validators_in_log(log_content: str) -> List[str]:
        """
        Detect which validators ran in the CI log.

        Args:
            log_content: Full CI job log content

        Returns:
            List of detected validator names
        """
        detected = []
        for validator_name, pattern in AnvilLogExtractor.VALIDATOR_PATTERNS.items():
            if re.search(pattern["start"], log_content, re.IGNORECASE):
                detected.append(validator_name)

        return detected
