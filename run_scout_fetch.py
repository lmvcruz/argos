#!/usr/bin/env python
"""Run Scout fetch command with token and display Anvil results."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from scout.cli import main

sys.path.insert(0, "d:\\playground\\argos\\scout")

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Get token from environment variables
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN not found in .env file")
    sys.exit(1)

# Run fetch for all workflows
workflows = ["Anvil Tests", "Forge Tests", "Scout Tests", "Verdict Tests"]

print("=" * 80)
print("SCOUT FETCH - Downloading GitHub Actions workflow data")
print("=" * 80)

for workflow in workflows:
    fetch_argv = [
        "scout", "ci", "fetch",
        "--token", token,
        "--repo", "lmvcruz/argos",
        "--workflow", workflow,
        "--db", ".anvil/scout.db",
        "--limit", "5",
        "--verbose"
    ]

    print(f"\n[FETCH] {workflow}")
    print(
        f"Command: scout ci fetch --token *** --repo lmvcruz/argos --workflow '{workflow}' --db .anvil/scout.db --limit 5 --verbose")
    result = main(argv=fetch_argv)
    print(f"Result: return code {result}")

print("\n" + "=" * 80)
print("SCOUT SYNC - Syncing to Anvil database")
print("=" * 80)

sync_argv = [
    "scout", "ci", "sync",
    "--token", token,
    "--repo", "lmvcruz/argos",
    "--db", ".anvil/scout.db",
    "--anvil-db", ".anvil/execution.db",
    "--limit", "5"
]

print(f"\nCommand: scout ci sync --token *** --repo lmvcruz/argos --db .anvil/scout.db --anvil-db .anvil/execution.db --limit 5")
result = main(argv=sync_argv)
print(f"Result: return code {result}")

print("\n" + "=" * 80)
print("ANVIL DATABASE - Full synced data (all fields)")
print("=" * 80)

# Query Anvil database to show comprehensive synced data
try:
    import sqlite3

    conn = sqlite3.connect(".anvil/execution.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the most recent validation run
    cursor.execute("""
        SELECT * FROM validation_runs
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    latest_run = cursor.fetchone()

    if latest_run:
        print(f"\n[VALIDATION RUN - Most Recent]")
        print(f"  ID: {latest_run['id']}")
        print(f"  Timestamp: {latest_run['timestamp']}")
        print(f"  Git Commit: {latest_run['git_commit']}")
        print(f"  Git Branch: {latest_run['git_branch']}")
        print(f"  Incremental: {latest_run['incremental']}")
        print(f"  Passed: {latest_run['passed']}")
        print(f"  Duration: {latest_run['duration_seconds']}s")

        run_id = latest_run['id']

        # Get test case records for this run
        cursor.execute("""
            SELECT * FROM test_case_records
            WHERE run_id = ?
            ORDER BY test_suite, test_name
        """, (run_id,))

        tests = cursor.fetchall()
        if tests:
            print(f"\n[TEST CASE RECORDS] ({len(tests)} tests)")
            passed_count = sum(1 for t in tests if t['passed'])
            skipped_count = sum(1 for t in tests if t['skipped'])
            failed_count = len(tests) - passed_count - skipped_count
            print(
                f"  Summary: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
            print()
            for test in tests:
                status = "PASS" if test['passed'] else "FAIL" if not test['skipped'] else "SKIP"
                duration = f"{test['duration_seconds']:.2f}s" if test['duration_seconds'] else "N/A"
                failure_msg = f" - {test['failure_message']}" if test['failure_message'] else ""
                print(
                    f"    [{status:4}] {test['test_suite']:40} :: {test['test_name']:40} ({duration}){failure_msg}")
        else:
            print(f"\n[TEST CASE RECORDS] No test case records found (0 tests)")

        # Get lint summary (note: lint_summary uses execution_id, not run_id)
        cursor.execute("""
            SELECT * FROM lint_summary
            ORDER BY validator
        """)

        lint_summaries = cursor.fetchall()
        if lint_summaries:
            print(f"\n[LINT SUMMARY] ({len(lint_summaries)} validators)")
            for lint in lint_summaries:
                print(f"  {lint['validator']}:")
                print(f"    Files Scanned: {lint['files_scanned']}")
                print(
                    f"    Total Violations: {lint['total_violations']} (Errors: {lint['errors']}, Warnings: {lint['warnings']}, Info: {lint['info']})")
        else:
            print(f"\n[LINT SUMMARY] No lint summary records found")

        # Get coverage summary
        cursor.execute("""
            SELECT * FROM coverage_summary
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        coverage = cursor.fetchone()
        if coverage:
            print(f"\n[COVERAGE SUMMARY]")
            print(f"  Total Coverage: {coverage['total_coverage']}%")
            print(f"  Files Analyzed: {coverage['files_analyzed']}")
            print(f"  Total Statements: {coverage['total_statements']}")
            print(f"  Covered Statements: {coverage['covered_statements']}")
        else:
            print(f"\n[COVERAGE SUMMARY] No coverage data found")

        # Get lint violations details (sample)
        cursor.execute("""
            SELECT * FROM lint_violations
            ORDER BY file_path, line_number
            LIMIT 10
        """)

        violations = cursor.fetchall()
        if violations:
            cursor.execute("SELECT COUNT(*) as count FROM lint_violations")
            total_violations = cursor.fetchone()['count']
            print(
                f"\n[LINT VIOLATIONS] (showing first 10 of {total_violations})")
            for violation in violations:
                print(
                    f"  {violation['file_path']}:{violation['line_number']}:{violation['column_number']}")
                print(
                    f"    [{violation['severity']}] {violation['code']}: {violation['message']}")

        # Get validator run records for this run
        cursor.execute("""
            SELECT * FROM validator_run_records
            WHERE run_id = ?
            ORDER BY validator_name
        """, (run_id,))

        validators = cursor.fetchall()
        if validators:
            print(f"\n[VALIDATOR RUN RECORDS] ({len(validators)} validators)")
            for validator in validators:
                status = "PASS" if validator['passed'] else "FAIL"
                print(f"  {validator['validator_name']} - [{status}]")
                print(f"    Files Checked: {validator['files_checked']}")
                print(
                    f"    Errors: {validator['error_count']}, Warnings: {validator['warning_count']}")
        else:
            print(f"\n[VALIDATOR RUN RECORDS] No validator records found")

        # Show summary of all runs in database
        print(f"\n[ALL VALIDATION RUNS IN DATABASE]")
        cursor.execute("""
            SELECT COUNT(*) as total_runs FROM validation_runs
        """)

        count = cursor.fetchone()['total_runs']
        print(f"  Total runs in database: {count}")

        cursor.execute("""
            SELECT id, timestamp, git_branch, passed, duration_seconds
            FROM validation_runs
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        all_runs = cursor.fetchall()
        if all_runs:
            print(f"  ID  | Status | Timestamp           | Branch          | Duration")
            print(f"  " + "-" * 70)
            for run in all_runs:
                status = "PASS" if run["passed"] else "FAIL"
                timestamp = run["timestamp"] if run["timestamp"] else "N/A"
                branch = run["git_branch"] if run["git_branch"] else "unknown"
                duration = f"{run['duration_seconds']:.1f}s" if run["duration_seconds"] else "N/A"
                print(
                    f"  {run['id']:3d} | {status:5} | {timestamp:19} | {branch:15} | {duration:8}")
    else:
        print("\n[WARN] No validation runs found in Anvil database")

    conn.close()

except Exception as e:
    import traceback
    print(f"\n[ERROR] Could not query Anvil database: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
