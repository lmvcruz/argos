"""
Parser resolver for dynamic parser selection based on job names.

Maps GitHub Actions job names to appropriate Anvil parsers using
configurable patterns and supports multiple parsers per job.
"""

import re
from typing import Optional, Union, List
from dataclasses import dataclass


@dataclass
class ParserConfig:
    """Configuration for a job-to-parser mapping."""

    pattern: str
    parser: Optional[str] = None
    parsers: Optional[List[str]] = None
    description: str = ""
    enabled: bool = True

    def get_parser_names(self) -> List[str]:
        """Get list of parser names (single or multiple)."""
        if self.parsers:
            return self.parsers
        elif self.parser:
            return [self.parser]
        return []


class ParserResolver:
    """
    Resolve parser(s) for CI job output based on job name and configuration.

    Supports:
    - Pattern matching (exact or regex)
    - Single parser per job
    - Multiple parsers per job
    - Fallback/default parser
    """

    # Map of parser names to parser classes
    PARSER_MAP = {
        "PytestParser": "anvil.parsers.pytest_parser:PytestParser",
        "Flake8Parser": "anvil.parsers.flake8_parser:Flake8Parser",
        "BlackParser": "anvil.parsers.black_parser:BlackParser",
        "IsortParser": "anvil.parsers.isort_parser:IsortParser",
        "CoverageParser": "anvil.parsers.coverage_parser:CoverageParser",
        "GTestParser": "anvil.parsers.gtest_parser:GTestParser",
        "ClangTidyParser": "anvil.parsers.clang_tidy_parser:ClangTidyParser",
        "CppcheckParser": "anvil.parsers.cppcheck_parser:CppcheckParser",
        "VultureParser": "anvil.parsers.vulture_parser:VultureParser",
        "RadonParser": "anvil.parsers.radon_parser:RadonParser",
        "AutoflakeParser": "anvil.parsers.autoflake_parser:AutoflakeParser",
        "PylintParser": "anvil.parsers.pylint_parser:PylintParser",
        "LintParser": "anvil.parsers.lint_parser:LintParser",
    }

    def __init__(self, config_patterns: List[ParserConfig]):
        """
        Initialize resolver with configuration patterns.

        Args:
            config_patterns: List of ParserConfig objects defining job-to-parser mappings
        """
        self.patterns = config_patterns
        self._parser_cache = {}

    def resolve(self, job_name: str) -> Optional[Union[str, List[str]]]:
        """
        Resolve parser(s) for a given job name.

        Args:
            job_name: GitHub Actions job name (e.g., "test", "coverage", "lint")

        Returns:
            Parser name (str) or list of parser names, or None if no match found

        Example:
            >>> resolver = ParserResolver(patterns)
            >>> resolver.resolve("test")
            'PytestParser'

            >>> resolver.resolve("lint")
            ['Flake8Parser', 'BlackParser', 'IsortParser']
        """
        for config in self.patterns:
            if not config.enabled:
                continue

            # Try to match pattern (supports both exact match and regex)
            try:
                if re.match(config.pattern, job_name):
                    return config.get_parser_names() or None
            except re.error:
                # Fallback to exact match if regex fails
                if config.pattern == job_name:
                    return config.get_parser_names() or None

        return None

    @staticmethod
    def import_parser(parser_name: str):
        """
        Dynamically import and return a parser class.

        Args:
            parser_name: Name of parser (e.g., 'PytestParser')

        Returns:
            Parser class

        Raises:
            ImportError: If parser cannot be imported
            ValueError: If parser name is unknown
        """
        if parser_name not in ParserResolver.PARSER_MAP:
            raise ValueError(f"Unknown parser: {parser_name}")

        module_path, class_name = ParserResolver.PARSER_MAP[parser_name].rsplit(
            ":", 1)

        try:
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Failed to import {parser_name}: {e}")

    def instantiate_parsers(self, job_name: str) -> Optional[Union[object, List[object]]]:
        """
        Resolve and instantiate parser(s) for a job.

        Args:
            job_name: GitHub Actions job name

        Returns:
            Instantiated parser(s) or None if no match

        Example:
            >>> parser = resolver.instantiate_parsers("test")
            >>> isinstance(parser, PytestParser)
            True

            >>> parsers = resolver.instantiate_parsers("lint")
            >>> len(parsers)
            3
        """
        parser_names = self.resolve(job_name)

        if not parser_names:
            return None

        # Handle single parser
        if isinstance(parser_names, str):
            parser_class = self.import_parser(parser_names)
            return parser_class()

        # Handle multiple parsers
        if isinstance(parser_names, list):
            parsers = []
            for name in parser_names:
                parser_class = self.import_parser(name)
                parsers.append(parser_class())
            return parsers

        return None


def load_parser_config_from_yaml(config_path: str) -> ParserResolver:
    """
    Load parser configuration from YAML file.

    Args:
        config_path: Path to parser-config.yaml

    Returns:
        ParserResolver instance

    Example:
        >>> resolver = load_parser_config_from_yaml(".scout/parser-config.yaml")
        >>> parser = resolver.instantiate_parsers("test")
    """
    import yaml

    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    patterns = []
    for job_config in config_dict.get('job_patterns', []):
        patterns.append(ParserConfig(**job_config))

    return ParserResolver(patterns)
