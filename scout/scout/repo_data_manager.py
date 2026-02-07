"""
Repository data manager for Scout.

This module manages the storage and configuration for repo-specific data,
allowing Scout to support multiple repositories on the same machine.

Each repository gets its own directory structure:
    ~/.scout/<owner>/<repo>/
    ├── scout.db              (SQLite database)
    ├── .scoutrc              (Config file with credentials)
    └── logs/                 (Raw CI logs)
"""

import json
from pathlib import Path
from typing import Dict, Optional


class RepoDataManager:
    """
    Manages repo-specific data storage and configuration.

    Organizes Scout data by repository, allowing multi-repo support
    and easy switching between projects.

    Args:
        owner: GitHub repository owner (username or organization)
        repo: GitHub repository name

    Examples:
        >>> rdm = RepoDataManager(owner="lmvcruz", repo="argos")
        >>> rdm.get_repo_dir()
        PosixPath('/home/user/.scout/lmvcruz/argos')
        >>> rdm.get_db_path()
        PosixPath('/home/user/.scout/lmvcruz/argos/scout.db')
    """

    def __init__(self, owner: str, repo: str):
        """
        Initialize repository data manager.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
        """
        self.owner = owner
        self.repo = repo
        self._repo_dir = None

    @property
    def repo_dir(self) -> Path:
        """
        Get the repository data directory.

        Returns:
            Path to ~/.scout/<owner>/<repo>/
        """
        if self._repo_dir is None:
            scout_base = Path.home() / ".scout"
            self._repo_dir = scout_base / self.owner / self.repo
            self._repo_dir.mkdir(parents=True, exist_ok=True)
        return self._repo_dir

    def get_repo_dir(self) -> Path:
        """
        Get the repository data directory.

        Returns:
            Path to ~/.scout/<owner>/<repo>/
        """
        return self.repo_dir

    def get_db_path(self) -> Path:
        """
        Get the database file path for this repository.

        Returns:
            Path to scout.db
        """
        return self.repo_dir / "scout.db"

    def get_logs_dir(self) -> Path:
        """
        Get the logs directory for this repository.

        Returns:
            Path to logs/ directory
        """
        logs_dir = self.repo_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def get_config_file(self) -> Path:
        """
        Get the configuration file path for this repository.

        Returns:
            Path to .scoutrc configuration file
        """
        return self.repo_dir / ".scoutrc"

    def load_config(self) -> Dict:
        """
        Load configuration from the repository's .scoutrc file.

        Returns:
            Configuration dictionary (empty dict if file doesn't exist)
        """
        config_file = self.get_config_file()
        if config_file.exists():
            with open(config_file, "r") as f:
                return json.load(f)
        return {}

    def save_config(self, config: Dict) -> None:
        """
        Save configuration to the repository's .scoutrc file.

        Args:
            config: Configuration dictionary to save
        """
        config_file = self.get_config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_config_value(self, key: str, default=None):
        """
        Get a configuration value from .scoutrc.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self.load_config()
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set_config_value(self, key: str, value) -> None:
        """
        Set a configuration value in .scoutrc.

        Args:
            key: Configuration key (supports dot notation)
            value: Configuration value
        """
        config = self.load_config()
        keys = key.split(".")
        cfg = config
        for k in keys[:-1]:
            if k not in cfg:
                cfg[k] = {}
            cfg = cfg[k]
        cfg[keys[-1]] = value
        self.save_config(config)

    def initialize(self) -> None:
        """
        Initialize the repository data directory.

        Creates necessary subdirectories and empty config file if needed.
        """
        # Ensure directories exist
        self.get_logs_dir()

        # Create default config if it doesn't exist
        config_file = self.get_config_file()
        if not config_file.exists():
            default_config = {
                "owner": self.owner,
                "repo": self.repo,
                "token": None,  # User can set this
            }
            self.save_config(default_config)

    def get_log_file_path(self, run_id: str, job_id: str) -> Path:
        """
        Get the log file path for a specific job.

        Args:
            run_id: Workflow run ID
            job_id: Workflow job ID

        Returns:
            Path to run_<run_id>/job_<job_id>.log
        """
        logs_dir = self.get_logs_dir()
        run_dir = logs_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir / f"job_{job_id}.log"

    def get_log_metadata_path(self, run_id: str, job_id: str) -> Path:
        """
        Get the metadata file path for a specific job's log.

        Args:
            run_id: Workflow run ID
            job_id: Workflow job ID

        Returns:
            Path to run_<run_id>/job_<job_id>.meta
        """
        logs_dir = self.get_logs_dir()
        run_dir = logs_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir / f"job_{job_id}.meta"

    def __repr__(self) -> str:
        """Get string representation."""
        return f"RepoDataManager({self.owner}/{self.repo})"
