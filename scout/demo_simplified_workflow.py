#!/usr/bin/env python
"""
Scout Simplified Workflow Demo

This script demonstrates the simplified Scout workflow:
1. scout fetch --workflow "Anvil Tests" --last 5 --output test_executions.json
2. scout parse --input test_executions.json --output parsed_results.json
3. scout ci show --run-id <run_id>
"""

import subprocess
import json
import sys
from pathlib import Path

print("\n" + "=" * 70)
print("SCOUT SIMPLIFIED WORKFLOW DEMO")
print("=" * 70)

# Step 1: Fetch the last 5 executions
print("\n" + "-" * 70)
print("STEP 1: Fetch the last 5 executions")
print("-" * 70)
print('\nCommand: scout fetch --workflow "Anvil Tests" --last 5 --output test_executions.json')
print()

result = subprocess.run(
    [
        sys.executable,
        "scout/cli.py",
        "fetch",
        "--workflow",
        "Anvil Tests",
        "--last",
        "5",
        "--output",
        "test_executions.json",
    ],
    cwd=".",
)

if result.returncode != 0:
    print("Error: fetch command failed")
    sys.exit(1)

# Load and display the fetched data
with open("test_executions.json") as f:
    fetch_data = json.load(f)

print("\n" + "-" * 70)
print("Fetched Data Summary:")
print("-" * 70)
for i, run in enumerate(fetch_data["runs"], 1):
    icon = "✓" if run["conclusion"] == "success" else "✗"
    duration_min = run["duration_seconds"] // 60
    duration_sec = run["duration_seconds"] % 60
    print(
        f"{i}. {icon} Run {run['run_id']} - {run['conclusion']}"
        f" ({duration_min}m {duration_sec}s)"
    )
    print(f"   Commit: {run['commit_sha'][:8]}")
    print(f"   Started: {run['started_at']}")

# Step 2: Parse the fetched data
print("\n" + "-" * 70)
print("STEP 2: Parse the fetched execution data")
print("-" * 70)
print('\nCommand: scout parse --input test_executions.json --output parsed_results.json')
print()

result = subprocess.run(
    [
        sys.executable,
        "scout/cli.py",
        "parse",
        "--input",
        "test_executions.json",
        "--output",
        "parsed_results.json",
        "--db",
        "scout.db",
    ],
    cwd=".",
)

if result.returncode != 0:
    print("Error: parse command failed")
    sys.exit(1)

# Load and display the parsed results
with open("parsed_results.json") as f:
    parse_results = json.load(f)

print("\n" + "-" * 70)
print("Parsed Results Summary:")
print("-" * 70)
print(f"Executions processed: {parse_results['executions_processed']}")
print(f"Executions stored: {parse_results['executions_stored']}")
print(f"Database: {parse_results['database']}")

# Step 3: Show details for one execution
print("\n" + "-" * 70)
print("STEP 3: Show execution details")
print("-" * 70)

# Get the first (most recent) failure
failure_run = None
for run in fetch_data["runs"]:
    if run["conclusion"] == "failure":
        failure_run = run
        break

if failure_run:
    print(
        f'\nCommand: scout ci show --run-id {failure_run["run_id"]}'
    )
    print()
    result = subprocess.run(
        [
            sys.executable,
            "scout/cli.py",
            "ci",
            "show",
            "--run-id",
            str(failure_run["run_id"]),
            "--db",
            "scout.db",
        ],
        cwd=".",
    )

print("\n" + "=" * 70)
print("✓ Scout simplified workflow demo completed!")
print("=" * 70)
print("\nKey takeaway:")
print("  The new 'scout fetch' and 'scout parse' commands provide a")
print("  simplified workflow for fetching and analyzing CI executions.")
print("\nUsage:")
print('  scout fetch --workflow "Workflow Name" --last N --output file.json')
print("  scout parse --input file.json --output results.json")
print("  scout ci show --run-id <run_id> --db scout.db")
print()
