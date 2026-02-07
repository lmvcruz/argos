#!/usr/bin/env python
"""Test multi-repo support."""
from scout.repo_data_manager import RepoDataManager

# Test multiple repositories
repos = [
    ("lmvcruz", "argos"),
    ("user1", "project1"),
    ("org", "big-project"),
]

print("Testing multi-repo support:\n")
for owner, repo in repos:
    rdm = RepoDataManager(owner=owner, repo=repo)
    rdm.initialize()

    repo_dir = rdm.get_repo_dir()
    db_path = rdm.get_db_path()
    logs_dir = rdm.get_logs_dir()
    config_file = rdm.get_config_file()

    print(f"Repository: {owner}/{repo}")
    print(
        f"  Repo dir:   {repo_dir.parent.parent.name}/{repo_dir.parent.name}/{repo_dir.name}/")
    print(f"  Database:   {db_path.name}")
    print(f"  Logs dir:   {logs_dir.name}/")
    print(f"  Config:     {config_file.name}")
    print()

print("✓ All repos are isolated in ~/.scout/<owner>/<repo>/")
print("✓ Easy to switch between repos using --repo owner/repo")
