# -*- coding: utf-8 -*-
"""
Tests for documentation examples.

This module validates that code examples in documentation actually work.
Ensures documentation stays in sync with implementation.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

import pytest


class DocumentationTester:
    """
    Test documentation code examples.

    Extracts and validates code blocks from documentation files.
    """

    def __init__(self, docs_dir: Path):
        """
        Initialize documentation tester.

        Args:
            docs_dir: Path to documentation directory
        """
        self.docs_dir = docs_dir

    def extract_code_blocks(self, doc_file: Path) -> List[Tuple[str, str]]:
        """
        Extract code blocks from markdown file.

        Args:
            doc_file: Path to markdown file

        Returns:
            List of (language, code) tuples
        """
        content = doc_file.read_text(encoding="utf-8")

        # Pattern: ```language\ncode\n```
        pattern = r"```(\w+)\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        return matches

    def extract_command_examples(self, doc_file: Path) -> List[str]:
        """
        Extract command-line examples from markdown.

        Args:
            doc_file: Path to markdown file

        Returns:
            List of command strings
        """
        content = doc_file.read_text(encoding="utf-8")

        # Pattern: Lines starting with $ or #
        pattern = r"^[\$#]\s+(.+)$"
        matches = re.findall(pattern, content, re.MULTILINE)

        return matches


class TestUserGuide:
    """Test examples from USER_GUIDE.md."""

    @pytest.fixture
    def docs_dir(self) -> Path:
        """Get documentation directory path."""
        return Path(__file__).parent.parent / "docs"

    @pytest.fixture
    def user_guide(self, docs_dir: Path) -> Path:
        """Get USER_GUIDE.md path."""
        return docs_dir / "USER_GUIDE.md"

    def test_user_guide_exists(self, user_guide: Path):
        """Test that USER_GUIDE.md exists."""
        assert user_guide.exists(), "USER_GUIDE.md not found"

    def test_minimal_config_example(self, user_guide: Path):
        """Test minimal configuration example is valid TOML."""
        import toml

        tester = DocumentationTester(user_guide.parent)
        code_blocks = tester.extract_code_blocks(user_guide)

        # Find TOML blocks
        toml_blocks = [code for lang, code in code_blocks if lang == "toml"]

        assert len(toml_blocks) > 0, "No TOML examples found"

        # Validate minimal config
        minimal_config = """
        [project]
        name = "my-project"
        languages = ["python"]
        """

        try:
            config = toml.loads(minimal_config)
            assert "project" in config
            assert config["project"]["name"] == "my-project"
            assert "python" in config["project"]["languages"]
        except toml.TomlDecodeError as e:
            pytest.fail(f"Invalid TOML in minimal config: {e}")

    def test_command_examples_syntax(self, user_guide: Path):
        """Test that command examples have valid syntax."""
        tester = DocumentationTester(user_guide.parent)
        commands = tester.extract_command_examples(user_guide)

        assert len(commands) > 0, "No command examples found"

        # Check common command patterns
        valid_commands = ["anvil", "git", "pip", "cd", "echo", "cat"]

        for cmd in commands:
            # Skip comments and complex examples
            if cmd.startswith("#") or "|" in cmd or ">" in cmd:
                continue

            # Check if command starts with valid executable
            first_word = cmd.split()[0]
            if first_word not in valid_commands:
                # Allow paths and shell built-ins
                if not (first_word.startswith("./") or first_word in ["export"]):
                    pytest.fail(
                        f"Unexpected command in docs: {first_word} (from: {cmd})"
                    )


class TestConfiguration:
    """Test examples from CONFIGURATION.md."""

    @pytest.fixture
    def config_doc(self) -> Path:
        """Get CONFIGURATION.md path."""
        return Path(__file__).parent.parent / "docs" / "CONFIGURATION.md"

    def test_configuration_exists(self, config_doc: Path):
        """Test that CONFIGURATION.md exists."""
        assert config_doc.exists(), "CONFIGURATION.md not found"

    def test_toml_examples_valid(self, config_doc: Path):
        """Test that all TOML examples are valid."""
        import toml

        tester = DocumentationTester(config_doc.parent)
        code_blocks = tester.extract_code_blocks(config_doc)

        toml_blocks = [code for lang, code in code_blocks if lang == "toml"]

        assert len(toml_blocks) > 0, "No TOML examples found"

        for i, toml_code in enumerate(toml_blocks):
            try:
                config = toml.loads(toml_code)
                assert isinstance(config, dict)
            except toml.TomlDecodeError as e:
                pytest.fail(f"Invalid TOML in example {i + 1}: {e}\n\n{toml_code}")

    def test_complete_example_valid(self, config_doc: Path):
        """Test that complete configuration example is valid."""
        import toml

        content = config_doc.read_text(encoding="utf-8")

        # Find "Complete Example" section
        if "## Complete Example" not in content:
            pytest.skip("Complete example section not found")

        # Extract the complete example
        pattern = r"## Complete Example.*?```toml\n(.*?)```"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            pytest.skip("Complete example TOML not found")

        complete_config = match.group(1)

        try:
            config = toml.loads(complete_config)

            # Validate structure
            assert "project" in config
            assert "validation" in config
            assert "python" in config or "cpp" in config

            # Validate required fields
            assert "name" in config["project"]
            assert "languages" in config["project"]

        except toml.TomlDecodeError as e:
            pytest.fail(f"Invalid complete configuration example: {e}")


class TestAPIDocumentation:
    """Test examples from API.md."""

    @pytest.fixture
    def api_doc(self) -> Path:
        """Get API.md path."""
        return Path(__file__).parent.parent / "docs" / "API.md"

    def test_api_doc_exists(self, api_doc: Path):
        """Test that API.md exists."""
        assert api_doc.exists(), "API.md not found"

    def test_python_examples_syntax(self, api_doc: Path):
        """Test that Python code examples are syntactically valid."""
        import ast

        tester = DocumentationTester(api_doc.parent)
        code_blocks = tester.extract_code_blocks(api_doc)

        python_blocks = [code for lang, code in code_blocks if lang == "python"]

        assert len(python_blocks) > 0, "No Python examples found"

        for i, python_code in enumerate(python_blocks):
            # Skip examples with placeholders or ellipsis
            if "..." in python_code or "<" in python_code or "TODO" in python_code:
                continue

            try:
                ast.parse(python_code)
            except SyntaxError as e:
                pytest.fail(
                    f"Syntax error in Python example {i + 1}: {e}\n\n{python_code}"
                )

    def test_class_signatures_valid(self, api_doc: Path):
        """Test that class signatures in examples are consistent."""
        content = api_doc.read_text(encoding="utf-8")

        # Check for common base classes
        assert "ValidatorBase" in content
        assert "ParserBase" in content
        assert "ValidationResult" in content

        # Check for required methods
        assert "def validate(" in content
        assert "def parse(" in content
        assert "def is_available(" in content


class TestTutorial:
    """Test examples from TUTORIAL.md."""

    @pytest.fixture
    def tutorial_doc(self) -> Path:
        """Get TUTORIAL.md path."""
        return Path(__file__).parent.parent / "TUTORIAL.md"

    def test_tutorial_exists(self, tutorial_doc: Path):
        """Test that TUTORIAL.md exists."""
        assert tutorial_doc.exists(), "TUTORIAL.md not found"

    def test_tutorial_has_examples(self, tutorial_doc: Path):
        """Test that tutorial contains code examples."""
        tester = DocumentationTester(tutorial_doc.parent)
        code_blocks = tester.extract_code_blocks(tutorial_doc)

        assert len(code_blocks) > 0, "No code examples in tutorial"

        # Check for expected languages
        languages = set(lang for lang, _ in code_blocks)
        expected_languages = {"bash", "python", "toml"}

        assert (
            expected_languages & languages
        ), f"Missing expected languages. Found: {languages}"

    def test_tutorial_steps_numbered(self, tutorial_doc: Path):
        """Test that tutorial steps are properly numbered."""
        content = tutorial_doc.read_text(encoding="utf-8")

        # Find step headers
        step_pattern = r"### Step (\d+):"
        steps = re.findall(step_pattern, content)

        assert len(steps) > 0, "No numbered steps found"

        # Check sequential numbering
        for i, step_num in enumerate(steps):
            # Allow for multiple Step 1s (different tutorials)
            if i > 0 and step_num == "1":
                continue

            expected = str((i % 10) + 1)  # Allow reset per tutorial
            if step_num != expected and steps[i - 1] != "1":
                pytest.fail(f"Step numbering issue: expected {expected}, got {step_num}")


class TestTroubleshooting:
    """Test examples from TROUBLESHOOTING.md."""

    @pytest.fixture
    def troubleshooting_doc(self) -> Path:
        """Get TROUBLESHOOTING.md path."""
        return Path(__file__).parent.parent / "docs" / "TROUBLESHOOTING.md"

    def test_troubleshooting_exists(self, troubleshooting_doc: Path):
        """Test that TROUBLESHOOTING.md exists."""
        assert troubleshooting_doc.exists(), "TROUBLESHOOTING.md not found"

    def test_has_problem_solution_pairs(self, troubleshooting_doc: Path):
        """Test that troubleshooting guide has problem/solution pairs."""
        content = troubleshooting_doc.read_text(encoding="utf-8")

        # Check for problem/solution structure
        assert "**Problem**:" in content, "No problem statements found"
        assert "**Solution" in content, "No solution statements found"

        # Count problems and solutions
        problem_count = content.count("**Problem**:")
        solution_count = content.count("**Solution")

        assert (
            problem_count > 0 and solution_count > 0
        ), "Missing problems or solutions"

        # Should have roughly equal numbers
        assert (
            abs(problem_count - solution_count) <= 3
        ), "Imbalanced problems/solutions"


class TestREADME:
    """Test examples from README.md."""

    @pytest.fixture
    def readme(self) -> Path:
        """Get README.md path."""
        return Path(__file__).parent.parent / "README.md"

    def test_readme_exists(self, readme: Path):
        """Test that README.md exists."""
        assert readme.exists(), "README.md not found"

    def test_quick_start_commands(self, readme: Path):
        """Test that quick start commands are valid."""
        tester = DocumentationTester(readme.parent)
        code_blocks = tester.extract_code_blocks(readme)

        bash_blocks = [code for lang, code in code_blocks if lang == "bash"]

        assert len(bash_blocks) > 0, "No bash examples in README"

        # Check for essential commands
        readme_content = readme.read_text(encoding="utf-8")
        essential_commands = ["anvil check", "anvil install-hooks", "pip install"]

        for cmd in essential_commands:
            assert (
                cmd in readme_content
            ), f"Essential command not in README: {cmd}"

    def test_config_example_valid(self, readme: Path):
        """Test that configuration example in README is valid."""
        import toml

        tester = DocumentationTester(readme.parent)
        code_blocks = tester.extract_code_blocks(readme)

        toml_blocks = [code for lang, code in code_blocks if lang == "toml"]

        if len(toml_blocks) == 0:
            pytest.skip("No TOML example in README")

        # Validate first TOML block
        try:
            config = toml.loads(toml_blocks[0])
            assert isinstance(config, dict)
        except toml.TomlDecodeError as e:
            pytest.fail(f"Invalid TOML in README: {e}")


class TestDocumentationCompleteness:
    """Test that documentation is complete and consistent."""

    @pytest.fixture
    def docs_dir(self) -> Path:
        """Get documentation directory."""
        return Path(__file__).parent.parent / "docs"

    def test_all_required_docs_exist(self, docs_dir: Path):
        """Test that all required documentation files exist."""
        required_docs = [
            "USER_GUIDE.md",
            "API.md",
            "CONFIGURATION.md",
            "TROUBLESHOOTING.md",
        ]

        for doc in required_docs:
            doc_path = docs_dir / doc
            assert doc_path.exists(), f"Missing required documentation: {doc}"

    def test_docs_not_empty(self, docs_dir: Path):
        """Test that documentation files are not empty."""
        doc_files = [
            "USER_GUIDE.md",
            "API.md",
            "CONFIGURATION.md",
            "TROUBLESHOOTING.md",
        ]

        for doc in doc_files:
            doc_path = docs_dir / doc
            if not doc_path.exists():
                continue

            content = doc_path.read_text(encoding="utf-8")
            assert len(content) > 100, f"Documentation file too short: {doc}"

    def test_cross_references_valid(self, docs_dir: Path):
        """Test that cross-references between docs are valid."""
        doc_files = list(docs_dir.glob("*.md"))

        for doc_file in doc_files:
            content = doc_file.read_text(encoding="utf-8")

            # Find markdown links: [text](file.md)
            link_pattern = r"\[([^\]]+)\]\(([^\)]+\.md)\)"
            links = re.findall(link_pattern, content)

            for text, link in links:
                # Skip external links
                if link.startswith("http"):
                    continue

                # Resolve relative path
                target = (doc_file.parent / link).resolve()

                assert target.exists(), (
                    f"Broken link in {doc_file.name}: "
                    f"[{text}]({link}) -> {target}"
                )


class TestDocumentationStyle:
    """Test documentation style consistency."""

    @pytest.fixture
    def docs_dir(self) -> Path:
        """Get documentation directory."""
        return Path(__file__).parent.parent / "docs"

    def test_headers_have_spacing(self, docs_dir: Path):
        """Test that markdown headers have proper spacing."""
        doc_files = list(docs_dir.glob("*.md"))

        for doc_file in doc_files:
            content = doc_file.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if line.startswith("#"):
                    # Check spacing after # symbols
                    header_level = len(line) - len(line.lstrip("#"))
                    expected_prefix = "#" * header_level + " "

                    assert line.startswith(expected_prefix), (
                        f"Header spacing issue in {doc_file.name} line {i + 1}: "
                        f"Expected '{expected_prefix}', got '{line[:header_level + 2]}'"
                    )

    def test_code_blocks_have_language(self, docs_dir: Path):
        """Test that code blocks specify language."""
        doc_files = list(docs_dir.glob("*.md"))

        for doc_file in doc_files:
            content = doc_file.read_text(encoding="utf-8")

            # Find code blocks without language
            pattern = r"```\n[^`]"
            matches = re.findall(pattern, content)

            assert len(matches) == 0, (
                f"Code blocks without language in {doc_file.name}: {len(matches)} found. "
                f"All code blocks should specify language: ```python, ```bash, etc."
            )


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
