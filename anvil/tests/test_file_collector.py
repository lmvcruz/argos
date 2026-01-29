"""
Test suite for File Collector & Git Integration.

Tests file collection in full and incremental modes according to
Step 1.4 of the implementation plan.
"""

import subprocess

import pytest

from anvil.core.file_collector import FileCollector, GitError


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository with some files."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create initial files
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("def foo(): pass")
    (tmp_path / "test_main.py").write_text("def test(): pass")

    # Create C++ files
    (tmp_path / "main.cpp").write_text("int main() {}")
    (tmp_path / "utils.hpp").write_text("void foo();")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    return tmp_path


@pytest.fixture
def non_git_repo(tmp_path):
    """Create a temporary directory without git."""
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("def foo(): pass")
    (tmp_path / "main.cpp").write_text("int main() {}")

    return tmp_path


class TestFullModeCollection:
    """Test file collection in full mode."""

    def test_collect_all_python_files(self, git_repo):
        """Test collect all Python files in full mode."""
        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=False)

        assert len(files) == 3
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "utils.py" for f in files)
        assert any(f.name == "test_main.py" for f in files)

    def test_collect_all_cpp_files(self, git_repo):
        """Test collect all C++ files in full mode."""
        collector = FileCollector(git_repo)
        files = collector.collect_files(language="cpp", incremental=False)

        assert len(files) == 2
        assert any(f.name == "main.cpp" for f in files)
        assert any(f.name == "utils.hpp" for f in files)

    def test_collect_all_languages(self, git_repo):
        """Test collect files for all detected languages."""
        collector = FileCollector(git_repo)
        files = collector.collect_files(incremental=False)

        # Should detect both Python and C++
        assert len(files) >= 5

    def test_full_mode_without_git(self, non_git_repo):
        """Test full mode works without git repository."""
        collector = FileCollector(non_git_repo)
        files = collector.collect_files(language="python", incremental=False)

        assert len(files) == 2
        assert any(f.name == "main.py" for f in files)
        assert any(f.name == "utils.py" for f in files)


class TestIncrementalModeCollection:
    """Test file collection in incremental mode."""

    def test_collect_modified_files(self, git_repo):
        """Test collect only modified Python files in incremental mode."""
        # Modify a file
        (git_repo / "main.py").write_text("print('modified')")

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True)

        assert len(files) == 1
        assert files[0].name == "main.py"

    def test_collect_new_untracked_files(self, git_repo):
        """Test git integration handles new untracked files."""
        # Create new file
        (git_repo / "new_file.py").write_text("# new file")

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True)

        assert len(files) == 1
        assert files[0].name == "new_file.py"

    def test_collect_staged_files(self, git_repo):
        """Test collect staged files for pre-commit hook."""
        # Modify and stage a file
        (git_repo / "utils.py").write_text("def foo(): return 42")
        subprocess.run(["git", "add", "utils.py"], cwd=git_repo, check=True, capture_output=True)

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True, staged_only=True)

        assert len(files) == 1
        assert files[0].name == "utils.py"

    def test_collect_both_staged_and_unstaged(self, git_repo):
        """Test collect both staged and unstaged modifications."""
        # Stage one file
        (git_repo / "main.py").write_text("print('staged')")
        subprocess.run(["git", "add", "main.py"], cwd=git_repo, check=True, capture_output=True)

        # Modify another without staging
        (git_repo / "utils.py").write_text("def foo(): return 99")

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True, staged_only=False)

        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "main.py" in file_names
        assert "utils.py" in file_names

    def test_no_modifications_returns_empty(self, git_repo):
        """Test incremental mode returns empty list when no modifications."""
        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True)

        assert len(files) == 0

    def test_handles_deleted_files(self, git_repo):
        """Test git integration handles deleted files."""
        # Delete a file
        (git_repo / "utils.py").unlink()

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=True)

        # Deleted files should not be in the collection
        assert not any(f.name == "utils.py" for f in files)

    def test_incremental_without_git_falls_back_to_full(self, non_git_repo):
        """Test file collection with no git repository falls back to full."""
        collector = FileCollector(non_git_repo)
        files = collector.collect_files(language="python", incremental=True)

        # Should fall back to full mode
        assert len(files) == 2
        assert any(f.name == "main.py" for f in files)


class TestGitIntegration:
    """Test git integration features."""

    def test_detects_uncommitted_changes(self, git_repo):
        """Test git integration detects uncommitted changes."""
        # Modify file
        (git_repo / "main.py").write_text("print('changed')")

        collector = FileCollector(git_repo)
        assert collector.has_uncommitted_changes()

    def test_no_uncommitted_changes_in_clean_repo(self, git_repo):
        """Test clean repository has no uncommitted changes."""
        collector = FileCollector(git_repo)
        assert not collector.has_uncommitted_changes()

    def test_detects_git_repository(self, git_repo):
        """Test detection of git repository."""
        collector = FileCollector(git_repo)
        assert collector.is_git_repository()

    def test_detects_non_git_directory(self, non_git_repo):
        """Test detection of non-git directory."""
        collector = FileCollector(non_git_repo)
        assert not collector.is_git_repository()

    def test_get_changed_files_across_commits(self, git_repo):
        """Test file collection across multiple commits."""
        # Modify and commit
        (git_repo / "main.py").write_text("print('version 2')")
        subprocess.run(["git", "add", "main.py"], cwd=git_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Update main"],
            cwd=git_repo,
            check=True,
            capture_output=True,
        )

        # Get files changed in last commit
        collector = FileCollector(git_repo)
        files = collector.get_changed_files_since_commit("HEAD~1")

        assert len(files) >= 1
        assert any(f.name == "main.py" for f in files)

    def test_empty_repository_returns_no_files(self, tmp_path):
        """Test file collection with empty repository."""
        # Create empty git repo
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        collector = FileCollector(tmp_path)
        files = collector.collect_files(language="python", incremental=False)

        assert len(files) == 0


class TestExclusionPatterns:
    """Test file collection respects exclusion patterns."""

    def test_respects_exclude_patterns(self, git_repo):
        """Test file collection respects exclude patterns."""
        # Create files in excluded directories
        (git_repo / "build").mkdir()
        (git_repo / "build" / "temp.py").write_text("# build file")

        collector = FileCollector(git_repo, exclude_patterns=["build"])
        files = collector.collect_files(language="python", incremental=False)

        # Should not include files from build directory
        assert not any("build" in str(f) for f in files)

    def test_default_exclusions_applied(self, git_repo):
        """Test default exclusion patterns are applied."""
        # Create files in default excluded directories
        (git_repo / "__pycache__").mkdir()
        (git_repo / "__pycache__" / "cache.py").write_text("# cache")

        collector = FileCollector(git_repo)
        files = collector.collect_files(language="python", incremental=False)

        # Should not include __pycache__ files
        assert not any("__pycache__" in str(f) for f in files)


class TestLanguageFiltering:
    """Test language-specific file filtering."""

    def test_filters_by_language(self, git_repo):
        """Test files are filtered by specified language."""
        collector = FileCollector(git_repo)

        python_files = collector.collect_files(language="python", incremental=False)
        cpp_files = collector.collect_files(language="cpp", incremental=False)

        # Verify no overlap
        python_names = {f.name for f in python_files}
        cpp_names = {f.name for f in cpp_files}

        assert "main.py" in python_names
        assert "main.cpp" in cpp_names
        assert "main.cpp" not in python_names
        assert "main.py" not in cpp_names

    def test_collects_multiple_languages(self, git_repo):
        """Test collecting files from multiple languages."""
        collector = FileCollector(git_repo)
        files = collector.collect_files(languages=["python", "cpp"], incremental=False)

        assert len(files) >= 5
        assert any(f.suffix == ".py" for f in files)
        assert any(f.suffix in [".cpp", ".hpp"] for f in files)


class TestErrorHandling:
    """Test error handling in file collector."""

    def test_invalid_language_raises_error(self, git_repo):
        """Test invalid language name raises error."""
        collector = FileCollector(git_repo)

        with pytest.raises(ValueError, match="Unknown language"):
            collector.collect_files(language="rust", incremental=False)

    def test_invalid_commit_ref_raises_error(self, git_repo):
        """Test invalid commit reference raises GitError."""
        collector = FileCollector(git_repo)

        with pytest.raises(GitError):
            collector.get_changed_files_since_commit("nonexistent_commit")

    def test_handles_permission_errors_gracefully(self, tmp_path):
        """Test handles permission errors gracefully."""
        # This test may be platform-specific
        collector = FileCollector(tmp_path)
        # Should not crash, just return empty
        files = collector.collect_files(language="python", incremental=False)
        assert isinstance(files, list)

    def test_git_timeout_handled_in_is_git_repository(self, tmp_path, mocker):
        """Test subprocess timeout is handled in is_git_repository."""
        collector = FileCollector(tmp_path)

        # Mock subprocess.run to raise TimeoutExpired
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        assert collector.is_git_repository() is False

    def test_git_not_found_handled_in_is_git_repository(self, tmp_path, mocker):
        """Test FileNotFoundError is handled in is_git_repository."""
        collector = FileCollector(tmp_path)

        # Mock subprocess.run to raise FileNotFoundError
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError("git not found")

        assert collector.is_git_repository() is False

    def test_has_uncommitted_changes_handles_timeout(self, git_repo, mocker):
        """Test has_uncommitted_changes handles subprocess timeout."""
        collector = FileCollector(git_repo)

        # First call to is_git_repository should succeed, second should timeout
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            mocker.Mock(returncode=0),  # is_git_repository check
            subprocess.TimeoutExpired("git", 10),  # has_uncommitted_changes
        ]

        with pytest.raises(GitError, match="timed out"):
            collector.has_uncommitted_changes()

    def test_has_uncommitted_changes_handles_subprocess_error(self, git_repo, mocker):
        """Test has_uncommitted_changes handles CalledProcessError."""
        collector = FileCollector(git_repo)

        # First call to is_git_repository should succeed, second should fail
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            mocker.Mock(returncode=0),  # is_git_repository check
            subprocess.CalledProcessError(1, "git"),  # has_uncommitted_changes
        ]

        with pytest.raises(GitError, match="Failed to check git status"):
            collector.has_uncommitted_changes()

    def test_get_changed_files_handles_timeout(self, git_repo, mocker):
        """Test get_changed_files_since_commit handles subprocess timeout."""
        collector = FileCollector(git_repo)

        # First call to is_git_repository should succeed, second should timeout
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = [
            mocker.Mock(returncode=0),  # is_git_repository check
            subprocess.TimeoutExpired("git", 10),  # get_changed_files
        ]

        with pytest.raises(GitError, match="timed out"):
            collector.get_changed_files_since_commit()


class TestPerformance:
    """Test performance of file collection."""

    def test_incremental_faster_than_full(self, git_repo):
        """Test incremental mode is faster than full mode for large repos."""
        import time

        # Modify one file
        (git_repo / "main.py").write_text("print('modified')")

        collector = FileCollector(git_repo)

        # Time incremental collection
        start = time.time()
        incremental_files = collector.collect_files(language="python", incremental=True)
        incremental_time = time.time() - start

        # Time full collection
        start = time.time()
        full_files = collector.collect_files(language="python", incremental=False)
        full_time = time.time() - start

        # Incremental should return fewer files
        assert len(incremental_files) < len(full_files)

        # Both should complete quickly (< 1 second)
        assert incremental_time < 1.0
        assert full_time < 1.0


class TestCaching:
    """Test file collection caching behavior."""

    def test_caches_language_detection(self, git_repo):
        """Test language detection is cached."""
        collector = FileCollector(git_repo)

        # First call
        files1 = collector.collect_files(language="python", incremental=False)

        # Second call should use cache
        files2 = collector.collect_files(language="python", incremental=False)

        assert files1 == files2

    def test_cache_invalidated_on_changes(self, git_repo):
        """Test cache is invalidated when files change."""
        collector = FileCollector(git_repo)

        # First collection
        files1 = collector.collect_files(language="python", incremental=True)

        # Modify a file
        (git_repo / "main.py").write_text("print('changed')")

        # Second collection should detect change
        files2 = collector.collect_files(language="python", incremental=True)

        # Results should differ
        assert len(files2) > len(files1)
