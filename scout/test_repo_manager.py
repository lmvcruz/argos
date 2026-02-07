#!/usr/bin/env python
"""Test the repo-specific database paths."""
import sys
import argparse
from scout.cli import get_db_path, get_repo_data_manager

# Test 1: Default repo-specific path
print("Test 1: Default repo-specific database path")
args = argparse.Namespace(repo="lmvcruz/argos", token=None, db=None)
db_path = get_db_path(args)
print(f"  DB path: {db_path}")
assert ".scout" in db_path
assert "lmvcruz" in db_path
assert "argos" in db_path
print("  ✓ PASS")

# Test 2: Custom DB path overrides default
print("\nTest 2: Custom --db path overrides default")
args = argparse.Namespace(repo="lmvcruz/argos",
                          token=None, db="/custom/path/scout.db")
db_path = get_db_path(args)
print(f"  DB path: {db_path}")
assert db_path == "/custom/path/scout.db"
print("  ✓ PASS")

# Test 3: RepoDataManager paths
print("\nTest 3: RepoDataManager path structure")
rdm = get_repo_data_manager(args)
repo_dir = rdm.get_repo_dir()
db_path = rdm.get_db_path()
logs_dir = rdm.get_logs_dir()
config_file = rdm.get_config_file()

print(f"  Repo dir: {repo_dir}")
print(f"  DB path: {db_path}")
print(f"  Logs dir: {logs_dir}")
print(f"  Config file: {config_file}")

assert "lmvcruz" in str(repo_dir) and "argos" in str(repo_dir)
assert "scout.db" in str(db_path)
assert "logs" in str(logs_dir)
assert ".scoutrc" in str(config_file)
print("  ✓ PASS")

print("\n✓ All tests passed!")
