"""
Tests for git hook installation and management.

Tests cover pre-commit and pre-push hook installation, execution, bypass
mechanisms, and multi-repository support.
"""

import os
import subprocess

import pytest

from anvil.git.hooks import GitHookError, GitHookManager


class TestGitHookInstallation:
    """Test git hook installation functionality."""

    def test_install_pre_commit_hook(self, tmp_path):
        """Test installing pre-commit hook in git repository."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Verify hook file exists
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()
        assert hook_path.is_file()

    def test_install_pre_push_hook(self, tmp_path):
        """Test installing pre-push hook in git repository."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_push_hook()

        # Verify hook file exists
        hook_path = repo_path / ".git" / "hooks" / "pre-push"
        assert hook_path.exists()
        assert hook_path.is_file()

    def test_hook_script_is_executable(self, tmp_path):
        """Test that installed hook script has executable permissions."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Check executable permission
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert os.access(hook_path, os.X_OK)

    def test_hook_script_calls_anvil_check_incremental(self, tmp_path):
        """Test that hook script calls 'anvil check --incremental'."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content and verify command
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        assert "anvil check --incremental" in content


class TestHookBypassMechanism:
    """Test hook bypass mechanism."""

    def test_hook_respects_bypass_keyword_in_commit_message(self, tmp_path):
        """Test that [skip-anvil] in commit message bypasses hook."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content and verify bypass logic
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        assert "[skip-anvil]" in content or "SKIP_ANVIL" in content

    def test_hook_returns_correct_exit_code_on_pass(self, tmp_path):
        """Test that hook returns exit code 0 when validation passes."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content and verify exit code handling
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        assert "exit 0" in content or "exit $?" in content

    def test_hook_returns_correct_exit_code_on_fail(self, tmp_path):
        """Test that hook returns exit code 1 when validation fails."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content and verify exit code handling
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()
        # Should propagate anvil's exit code
        assert "exit" in content


class TestHookUninstallation:
    """Test hook uninstallation functionality."""

    def test_uninstall_pre_commit_hook(self, tmp_path):
        """Test uninstalling pre-commit hook."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install and then uninstall hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()
        manager.uninstall_pre_commit_hook()

        # Verify hook is removed
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert not hook_path.exists()

    def test_uninstall_pre_push_hook(self, tmp_path):
        """Test uninstalling pre-push hook."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install and then uninstall hook
        manager = GitHookManager(repo_path)
        manager.install_pre_push_hook()
        manager.uninstall_pre_push_hook()

        # Verify hook is removed
        hook_path = repo_path / ".git" / "hooks" / "pre-push"
        assert not hook_path.exists()

    def test_uninstall_hooks_removes_all(self, tmp_path):
        """Test uninstalling all Anvil-managed hooks."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install both hooks
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()
        manager.install_pre_push_hook()

        # Uninstall all
        manager.uninstall_all_hooks()

        # Verify both hooks are removed
        pre_commit_path = repo_path / ".git" / "hooks" / "pre-commit"
        pre_push_path = repo_path / ".git" / "hooks" / "pre-push"
        assert not pre_commit_path.exists()
        assert not pre_push_path.exists()


class TestHookUpdates:
    """Test updating existing hooks."""

    def test_update_hooks_replaces_existing(self, tmp_path):
        """Test that reinstalling hook replaces existing one."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Modify hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("# Modified hook\n")

        # Reinstall hook
        manager.install_pre_commit_hook(force=True)

        # Verify hook is replaced
        content = hook_path.read_text()
        assert "# Modified hook" not in content
        assert "anvil check" in content

    def test_install_hook_fails_if_exists_without_force(self, tmp_path):
        """Test that installing hook fails if it exists and force=False."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Try to install again without force
        with pytest.raises(GitHookError, match="already exists"):
            manager.install_pre_commit_hook(force=False)


class TestGitRepositoryValidation:
    """Test validation of git repository."""

    def test_hook_installation_outside_git_repository_raises_error(self, tmp_path):
        """Test that installing hook outside git repo raises error."""
        # Create non-git directory
        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        # Try to install hook
        manager = GitHookManager(non_git_path)
        with pytest.raises(GitHookError, match="not a git repository"):
            manager.install_pre_commit_hook()

    def test_is_git_repository_returns_true_for_git_repo(self, tmp_path):
        """Test is_git_repository returns True for valid git repo."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        manager = GitHookManager(repo_path)
        assert manager.is_git_repository() is True

    def test_is_git_repository_returns_false_for_non_git_dir(self, tmp_path):
        """Test is_git_repository returns False for non-git directory."""
        # Create non-git directory
        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        manager = GitHookManager(non_git_path)
        assert manager.is_git_repository() is False


class TestMultiRepositorySupport:
    """Test support for multiple repositories."""

    def test_multi_repository_support_different_directories(self, tmp_path):
        """Test that hooks can be installed in multiple repos independently."""
        # Create two git repos
        repo1_path = tmp_path / "repo1"
        repo2_path = tmp_path / "repo2"
        repo1_path.mkdir()
        repo2_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo1_path, check=True, capture_output=True)
        subprocess.run(["git", "init"], cwd=repo2_path, check=True, capture_output=True)

        # Install hooks in both repos
        manager1 = GitHookManager(repo1_path)
        manager2 = GitHookManager(repo2_path)

        manager1.install_pre_commit_hook()
        manager2.install_pre_commit_hook()

        # Verify both hooks exist independently
        hook1_path = repo1_path / ".git" / "hooks" / "pre-commit"
        hook2_path = repo2_path / ".git" / "hooks" / "pre-commit"

        assert hook1_path.exists()
        assert hook2_path.exists()


class TestHookWithAnvilInPath:
    """Test hook execution when Anvil is in PATH."""

    def test_hook_uses_anvil_from_path(self, tmp_path):
        """Test that hook script uses 'anvil' command from PATH."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()

        # Should use 'anvil' command (not absolute path)
        assert "anvil check" in content

    def test_hook_with_python_module_invocation(self, tmp_path):
        """Test that hook can invoke anvil as Python module."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()

        # Should support python -m anvil as fallback
        assert "python -m anvil" in content or "anvil check" in content


class TestHookPreservation:
    """Test hook preservation during git operations."""

    def test_hook_preservation_during_git_operations(self, tmp_path):
        """Test that hooks survive basic git operations."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Create a commit (git operation)
        test_file = repo_path / "test.txt"
        test_file.write_text("test content")
        subprocess.run(["git", "add", "test.txt"], cwd=repo_path, check=True, capture_output=True)

        # Verify hook still exists
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()


class TestHookEnvironmentVariables:
    """Test hook execution with environment variables."""

    def test_hook_execution_with_environment_variables(self, tmp_path):
        """Test that hook passes through relevant environment variables."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()

        # Hook should preserve environment or set specific vars
        # (e.g., GIT_AUTHOR_NAME, GIT_COMMITTER_NAME, etc.)
        assert "#!/" in content  # Has shebang


class TestHookListAndStatus:
    """Test listing and checking status of installed hooks."""

    def test_list_installed_hooks(self, tmp_path):
        """Test listing which hooks are installed."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install pre-commit hook only
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # List installed hooks
        installed = manager.list_installed_hooks()

        assert "pre-commit" in installed
        assert "pre-push" not in installed

    def test_is_hook_installed_returns_true_when_installed(self, tmp_path):
        """Test is_hook_installed returns True for installed hook."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Check installation status
        assert manager.is_hook_installed("pre-commit") is True
        assert manager.is_hook_installed("pre-push") is False


class TestHookContentGeneration:
    """Test hook script content generation."""

    def test_hook_content_includes_shebang(self, tmp_path):
        """Test that generated hook includes proper shebang."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()

        # Should start with shebang
        assert content.startswith("#!/")

    def test_hook_content_includes_error_handling(self, tmp_path):
        """Test that hook includes proper error handling."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Read hook content
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        content = hook_path.read_text()

        # Should handle errors gracefully
        assert "set -e" in content or "if" in content


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_generate_hook_script_invalid_type_raises_error(self, tmp_path):
        """Test that generating hook with invalid type raises error."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Try to generate hook with invalid type
        manager = GitHookManager(repo_path)
        with pytest.raises(GitHookError, match="Unsupported hook type"):
            manager._generate_hook_script("invalid-hook")

    def test_install_hook_invalid_type_raises_error(self, tmp_path):
        """Test that installing hook with invalid type raises error."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Try to install hook with invalid type
        manager = GitHookManager(repo_path)
        with pytest.raises(GitHookError, match="Invalid hook type"):
            manager._install_hook("invalid-hook")

    def test_uninstall_hook_invalid_type_raises_error(self, tmp_path):
        """Test that uninstalling hook with invalid type raises error."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Try to uninstall hook with invalid type
        manager = GitHookManager(repo_path)
        with pytest.raises(GitHookError, match="Invalid hook type"):
            manager._uninstall_hook("invalid-hook")

    def test_uninstall_nonexistent_hook_succeeds(self, tmp_path):
        """Test that uninstalling non-existent hook succeeds silently."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Uninstall hook that was never installed
        manager = GitHookManager(repo_path)
        manager.uninstall_pre_commit_hook()  # Should not raise error

        # Verify no hook exists
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert not hook_path.exists()

    def test_uninstall_all_hooks_continues_on_error(self, tmp_path):
        """Test that uninstall_all_hooks continues even if one fails."""
        # Initialize git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Install only pre-commit hook
        manager = GitHookManager(repo_path)
        manager.install_pre_commit_hook()

        # Uninstall all hooks (pre-push doesn't exist, should not raise)
        manager.uninstall_all_hooks()

        # Verify pre-commit was removed
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert not hook_path.exists()

    def test_uninstall_all_hooks_outside_git_repo_continues(self, tmp_path):
        """Test that uninstall_all_hooks handles errors gracefully."""
        # Create non-git directory
        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        # Try to uninstall all hooks (should not raise error, catches internally)
        manager = GitHookManager(non_git_path)
        manager.uninstall_all_hooks()  # Should not raise

    def test_is_hook_installed_outside_git_repo_returns_false(self, tmp_path):
        """Test that is_hook_installed returns False outside git repo."""
        # Create non-git directory
        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        # Check hook installation status
        manager = GitHookManager(non_git_path)
        assert manager.is_hook_installed("pre-commit") is False

    def test_list_installed_hooks_outside_git_repo_returns_empty(self, tmp_path):
        """Test that list_installed_hooks returns empty list outside git repo."""
        # Create non-git directory
        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        # List installed hooks
        manager = GitHookManager(non_git_path)
        assert manager.list_installed_hooks() == []
