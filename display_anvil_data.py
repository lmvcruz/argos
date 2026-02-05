#!/usr/bin/env python
"""Enhanced Anvil output display script - Fixed version for comprehensive schema queries."""

import sqlite3
from datetime import datetime


def display_anvil_data():
    """Display comprehensive Anvil database data."""

    conn = sqlite3.connect(".anvil/execution.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 100)
    print("ANVIL EXECUTION DATABASE - COMPREHENSIVE DATA DISPLAY")
    print("=" * 100)

    # Table Summary
    print("\n[DATABASE SUMMARY]")
    cursor.execute("SELECT COUNT(*) as count FROM validation_runs")
    validation_runs_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM test_case_records")
    test_case_records_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM lint_summary")
    lint_summary_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM coverage_summary")
    coverage_summary_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM validator_run_records")
    validator_run_records_count = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM file_validation_records")
    file_validation_records_count = cursor.fetchone()['count']

    print(f"  validation_runs:          {validation_runs_count:5} records")
    print(f"  test_case_records:        {test_case_records_count:5} records")
    print(f"  lint_summary:             {lint_summary_count:5} records")
    print(f"  coverage_summary:         {coverage_summary_count:5} records")
    print(
        f"  validator_run_records:    {validator_run_records_count:5} records")
    print(
        f"  file_validation_records:  {file_validation_records_count:5} records")

    # Most Recent Validation Run
    print("\n[MOST RECENT VALIDATION RUN]")
    cursor.execute("""
        SELECT * FROM validation_runs
        ORDER BY id DESC
        LIMIT 1
    """)

    latest_run = cursor.fetchone()

    if latest_run:
        print(f"  Run ID:       {latest_run['id']}")
        print(f"  Timestamp:    {latest_run['timestamp']}")
        print(f"  Git Commit:   {latest_run['git_commit']}")
        print(f"  Git Branch:   {latest_run['git_branch']}")
        print(f"  Incremental:  {latest_run['incremental']}")
        print(
            f"  Status:       {'PASSED' if latest_run['passed'] else 'FAILED'}")
        print(f"  Duration:     {latest_run['duration_seconds']:.1f} seconds")

        run_id = latest_run['id']

        # Test Case Records for this run
        cursor.execute("""
            SELECT * FROM test_case_records
            WHERE run_id = ?
            ORDER BY test_suite, test_name
        """, (run_id,))

        tests = cursor.fetchall()
        if tests:
            print(
                f"\n[TEST CASE RECORDS] for Run {run_id} ({len(tests)} tests)")
            passed_count = sum(1 for t in tests if t['passed'])
            skipped_count = sum(1 for t in tests if t['skipped'])
            failed_count = len(tests) - passed_count - skipped_count
            print(
                f"  Summary: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
            print()
            for i, test in enumerate(tests, 1):
                status = "PASS" if test['passed'] else "FAIL" if not test['skipped'] else "SKIP"
                duration = f"{test['duration_seconds']:.2f}s" if test['duration_seconds'] else "N/A"
                failure = f" - {test['failure_message']}" if test['failure_message'] else ""
                print(f"    {i:3d}. [{status:4}] {test['test_suite']}")
                print(f"         └─ {test['test_name']} ({duration}){failure}")
        else:
            print(
                f"\n[TEST CASE RECORDS] No test case records found for Run {run_id}")

        # Validator Run Records
        cursor.execute("""
            SELECT * FROM validator_run_records
            WHERE run_id = ?
            ORDER BY validator_name
        """, (run_id,))

        validators = cursor.fetchall()
        if validators:
            print(
                f"\n[VALIDATOR RUN RECORDS] for Run {run_id} ({len(validators)} validators)")
            for validator in validators:
                status = "PASS" if validator['passed'] else "FAIL"
                print(f"  {validator['validator_name']:30} [{status:4}]")
                print(f"    Files Checked: {validator['files_checked']}")
                print(
                    f"    Errors: {validator['error_count']:3} | Warnings: {validator['warning_count']:3}")
        else:
            print(
                f"\n[VALIDATOR RUN RECORDS] No validator records found for Run {run_id}")

    # Lint Summary (not filtered by run)
    print("\n[LINT SUMMARY] (across all runs)")
    cursor.execute("""
        SELECT * FROM lint_summary
        ORDER BY validator
    """)

    lint_summaries = cursor.fetchall()
    if lint_summaries:
        print(f"  Found {len(lint_summaries)} lint summary records")
        for lint in lint_summaries:
            print(f"\n  {lint['validator']}")
            print(f"    Files Scanned:     {lint['files_scanned']}")
            print(f"    Total Violations:  {lint['total_violations']}")
            print(f"    Errors:            {lint['errors']}")
            print(f"    Warnings:          {lint['warnings']}")
            print(f"    Info:              {lint['info']}")
    else:
        print("  No lint summary records found")

    # Coverage Summary
    print("\n[COVERAGE SUMMARY] (across all runs)")
    cursor.execute("""
        SELECT * FROM coverage_summary
        ORDER BY timestamp DESC
        LIMIT 5
    """)

    coverage_records = cursor.fetchall()
    if coverage_records:
        print(
            f"  Found {len(coverage_records)} coverage summary records (showing most recent 5)")
        for cov in coverage_records:
            print(f"\n  Execution: {cov['execution_id']}")
            print(f"    Timestamp:          {cov['timestamp']}")
            print(f"    Total Coverage:     {cov['total_coverage']}%")
            print(f"    Files Analyzed:     {cov['files_analyzed']}")
            print(
                f"    Covered Statements: {cov['covered_statements']}/{cov['total_statements']}")
    else:
        print("  No coverage summary records found")

    # All Validation Runs Summary
    print("\n[ALL VALIDATION RUNS] (summary table, most recent 15)")
    cursor.execute("""
        SELECT id, timestamp, git_branch, passed, duration_seconds
        FROM validation_runs
        ORDER BY id DESC
        LIMIT 15
    """)

    all_runs = cursor.fetchall()
    if all_runs:
        print(f"\n  ID  | Status | Timestamp           | Branch          | Duration")
        print(f"  " + "-" * 70)
        for run in all_runs:
            status = "PASS" if run["passed"] else "FAIL"
            timestamp = run["timestamp"] if run["timestamp"] else "N/A"
            branch = run["git_branch"] if run["git_branch"] else "unknown"
            duration = f"{run['duration_seconds']:.1f}s" if run["duration_seconds"] else "N/A"
            print(
                f"  {run['id']:3d} | {status:5} | {timestamp:19} | {branch:15} | {duration:8}")

    conn.close()

    print("\n" + "=" * 100)
    print("END OF ANVIL DATABASE DISPLAY")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    display_anvil_data()
