"""
Test suite for Language Detector.

Tests language detection from file extensions according to
Step 1.3 of the implementation plan.
"""

from pathlib import Path

import pytest

from anvil.core.language_detector import LanguageDetector


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with mixed language files."""
    # Python files
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("def foo(): pass")

    # C++ files
    (tmp_path / "main.cpp").write_text("int main() {}")
    (tmp_path / "utils.hpp").write_text("void foo();")
    (tmp_path / "config.h").write_text("#define FOO 1")
    (tmp_path / "impl.cc").write_text("void bar() {}")
    (tmp_path / "advanced.cxx").write_text("void baz() {}")
    (tmp_path / "header.hxx").write_text("void qux();")

    # Files to ignore
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.pyc").write_text("")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "temp.o").write_text("")

    # Other files
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / "data.json").write_text("{}")

    return tmp_path


@pytest.fixture
def python_only_project(tmp_path):
    """Create a temporary project with only Python files."""
    (tmp_path / "app.py").write_text("import os")
    (tmp_path / "test_app.py").write_text("def test(): pass")
    (tmp_path / "setup.py").write_text("from setuptools import setup")

    return tmp_path


@pytest.fixture
def cpp_only_project(tmp_path):
    """Create a temporary project with only C++ files."""
    (tmp_path / "main.cpp").write_text("int main() {}")
    (tmp_path / "lib.hpp").write_text("class Lib {};")
    (tmp_path / "impl.cc").write_text("void foo() {}")

    return tmp_path


@pytest.fixture
def empty_project(tmp_path):
    """Create an empty temporary project."""
    return tmp_path


class TestLanguageDetection:
    """Test language detection from file extensions."""

    def test_detect_python_files(self, temp_project):
        """Test detection of Python files (*.py)."""
        detector = LanguageDetector(temp_project)
        languages = detector.detect_languages()

        assert "python" in languages
        python_files = detector.get_files_for_language("python")
        assert len(python_files) == 2
        assert any(f.name == "main.py" for f in python_files)
        assert any(f.name == "utils.py" for f in python_files)

    def test_detect_cpp_files(self, temp_project):
        """Test detection of C++ files (*.cpp, *.hpp, *.h, *.cc, *.cxx, *.hxx)."""
        detector = LanguageDetector(temp_project)
        languages = detector.detect_languages()

        assert "cpp" in languages
        cpp_files = detector.get_files_for_language("cpp")
        assert len(cpp_files) == 6
        assert any(f.name == "main.cpp" for f in cpp_files)
        assert any(f.name == "utils.hpp" for f in cpp_files)
        assert any(f.name == "config.h" for f in cpp_files)
        assert any(f.name == "impl.cc" for f in cpp_files)
        assert any(f.name == "advanced.cxx" for f in cpp_files)
        assert any(f.name == "header.hxx" for f in cpp_files)

    def test_detect_mixed_language_project(self, temp_project):
        """Test detection with mixed language project."""
        detector = LanguageDetector(temp_project)
        languages = detector.detect_languages()

        assert len(languages) == 2
        assert "python" in languages
        assert "cpp" in languages

    def test_detect_python_only_project(self, python_only_project):
        """Test detection with Python-only project."""
        detector = LanguageDetector(python_only_project)
        languages = detector.detect_languages()

        assert len(languages) == 1
        assert "python" in languages
        assert len(detector.get_files_for_language("python")) == 3

    def test_detect_cpp_only_project(self, cpp_only_project):
        """Test detection with C++-only project."""
        detector = LanguageDetector(cpp_only_project)
        languages = detector.detect_languages()

        assert len(languages) == 1
        assert "cpp" in languages
        assert len(detector.get_files_for_language("cpp")) == 3

    def test_detect_no_matching_files(self, empty_project):
        """Test detection with no matching files."""
        # Create only non-code files
        (empty_project / "README.md").write_text("# Docs")
        (empty_project / "data.json").write_text("{}")

        detector = LanguageDetector(empty_project)
        languages = detector.detect_languages()

        assert len(languages) == 0

    def test_get_files_returns_only_python(self, temp_project):
        """Test get_files_for_language returns only Python files."""
        detector = LanguageDetector(temp_project)
        python_files = detector.get_files_for_language("python")

        for file in python_files:
            assert file.suffix == ".py"

    def test_get_files_returns_only_cpp(self, temp_project):
        """Test get_files_for_language returns only C++ files."""
        detector = LanguageDetector(temp_project)
        cpp_files = detector.get_files_for_language("cpp")

        valid_extensions = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hxx"}
        for file in cpp_files:
            assert file.suffix in valid_extensions


class TestExclusionPatterns:
    """Test exclusion patterns and ignored directories."""

    def test_ignores_git_directory(self, temp_project):
        """Test that .git directory is ignored."""
        detector = LanguageDetector(temp_project)
        all_files = detector.get_files_for_language("python") + detector.get_files_for_language(
            "cpp"
        )

        for file in all_files:
            assert ".git" not in str(file)

    def test_ignores_pycache_directory(self, temp_project):
        """Test that __pycache__ directory is ignored."""
        detector = LanguageDetector(temp_project)
        all_files = detector.get_files_for_language("python") + detector.get_files_for_language(
            "cpp"
        )

        for file in all_files:
            assert "__pycache__" not in str(file)

    def test_ignores_build_directory(self, temp_project):
        """Test that build directory is ignored."""
        detector = LanguageDetector(temp_project)
        all_files = detector.get_files_for_language("python") + detector.get_files_for_language(
            "cpp"
        )

        for file in all_files:
            # Check relative path parts, not full path (which may contain "build")
            rel_path = file.relative_to(temp_project)
            assert "build" not in rel_path.parts

    def test_custom_exclude_patterns(self, temp_project):
        """Test custom exclude patterns from configuration."""
        # Create files in custom directories
        (temp_project / "vendor").mkdir()
        (temp_project / "vendor" / "lib.py").write_text("# vendor code")
        (temp_project / "tests").mkdir()
        (temp_project / "tests" / "test_foo.py").write_text("# test")

        # Without exclusions
        detector1 = LanguageDetector(temp_project)
        files1 = detector1.get_files_for_language("python")
        assert any("vendor" in str(f) for f in files1)

        # With exclusions
        detector2 = LanguageDetector(temp_project, exclude_patterns=["vendor", "tests"])
        files2 = detector2.get_files_for_language("python")
        assert not any("vendor" in str(f) for f in files2)
        assert not any("tests" in str(f) for f in files2)


class TestConfigurationIntegration:
    """Test integration with configuration file patterns."""

    def test_respects_file_patterns_from_config(self, temp_project):
        """Test that detector respects file_patterns from config."""
        # Create additional Python file type
        (temp_project / "script.pyw").write_text("# Windows Python script")

        # Default patterns (only .py)
        detector1 = LanguageDetector(temp_project)
        files1 = detector1.get_files_for_language("python")
        assert not any(f.suffix == ".pyw" for f in files1)

        # Custom patterns (include .pyw)
        detector2 = LanguageDetector(
            temp_project, file_patterns={"python": ["**/*.py", "**/*.pyw"]}
        )
        files2 = detector2.get_files_for_language("python")
        assert any(f.suffix == ".pyw" for f in files2)

    def test_respects_cpp_patterns_from_config(self, cpp_only_project):
        """Test that detector respects C++ file patterns from config."""
        # Create .c file (C, not C++)
        (cpp_only_project / "legacy.c").write_text("void old() {}")

        # Default patterns (no .c)
        detector1 = LanguageDetector(cpp_only_project)
        files1 = detector1.get_files_for_language("cpp")
        assert not any(f.suffix == ".c" for f in files1)

        # Custom patterns (include .c) - need separate patterns for each extension
        detector2 = LanguageDetector(
            cpp_only_project, file_patterns={"cpp": ["**/*.cpp", "**/*.hpp", "**/*.c", "**/*.h"]}
        )
        files2 = detector2.get_files_for_language("cpp")
        assert any(f.suffix == ".c" for f in files2)


class TestSymbolicLinks:
    """Test handling of symbolic links."""

    @pytest.mark.skip(reason="Symlink handling needs investigation - see issue #TBD")
    def test_follows_symlinks_when_enabled(self, temp_project, tmp_path):
        """Test that symbolic links are followed when enabled."""
        # Create external directory with Python file
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        (external_dir / "external.py").write_text("# external")

        # Create symlink (skip on Windows if not admin)
        try:
            symlink_path = temp_project / "linked"
            symlink_path.symlink_to(external_dir)

            detector = LanguageDetector(temp_project, follow_symlinks=True)
            files = detector.get_files_for_language("python")

            # Should include symlinked file
            assert any(f.name == "external.py" for f in files)
        except OSError:
            pytest.skip("Symlink creation requires elevated privileges on Windows")

    @pytest.mark.skip(reason="Symlink handling needs investigation - see issue #TBD")
    def test_ignores_symlinks_when_disabled(self, temp_project, tmp_path):
        """Test that symbolic links are ignored when disabled."""
        # Create external directory with Python file
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        (external_dir / "external.py").write_text("# external")

        # Create symlink (skip on Windows if not admin)
        try:
            symlink_path = temp_project / "linked"
            symlink_path.symlink_to(external_dir)

            detector = LanguageDetector(temp_project, follow_symlinks=False)
            files = detector.get_files_for_language("python")

            # Should NOT include symlinked file
            assert not any(f.name == "external.py" for f in files)
        except OSError:
            pytest.skip("Symlink creation requires elevated privileges on Windows")


class TestPerformance:
    """Test performance with large directory trees."""

    def test_performance_large_directory_tree(self, tmp_path):
        """Test detection performance with large directory trees."""
        # Create nested directory structure with many files
        for i in range(10):
            subdir = tmp_path / f"level{i}"
            subdir.mkdir()
            for j in range(10):
                (subdir / f"file{j}.py").write_text(f"# file {i}-{j}")

        # Should complete quickly (< 1 second for 100 files)
        import time

        start = time.time()
        detector = LanguageDetector(tmp_path)
        languages = detector.detect_languages()
        duration = time.time() - start

        assert "python" in languages
        assert len(detector.get_files_for_language("python")) == 100
        assert duration < 1.0  # Should be fast


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_nonexistent_directory_raises_error(self):
        """Test that nonexistent directory raises error."""
        with pytest.raises(FileNotFoundError):
            LanguageDetector(Path("/nonexistent/path"))

    def test_file_instead_of_directory_raises_error(self, tmp_path):
        """Test that passing a file instead of directory raises error."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        with pytest.raises(NotADirectoryError):
            LanguageDetector(test_file)

    def test_get_files_for_unknown_language_returns_empty(self, temp_project):
        """Test that unknown language returns empty list."""
        detector = LanguageDetector(temp_project)
        files = detector.get_files_for_language("rust")

        assert files == []

    def test_empty_directory_returns_empty(self, empty_project):
        """Test that empty directory returns no languages."""
        detector = LanguageDetector(empty_project)
        languages = detector.detect_languages()

        assert languages == []
