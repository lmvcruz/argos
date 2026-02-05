#!/usr/bin/env python
"""
Comprehensive end-to-end test for Scout v2 handlers.

Tests the complete pipeline: fetch -> save -> parse -> save-analysis.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Import the CLI module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "cli", Path(__file__).parent / "scout" / "cli.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

handle_fetch_command_v2 = cli.handle_fetch_command_v2
handle_parse_command_v2 = cli.handle_parse_command_v2
handle_sync_command = cli.handle_sync_command


def test_full_pipeline():
    """Test complete fetch -> parse -> save pipeline."""
    print("\n" + "=" * 60)
    print("FULL PIPELINE TEST: fetch -> save-ci -> parse -> save-analysis")
    print("=" * 60)

    tmpdir = tempfile.mkdtemp()
    try:
        tmpdir = Path(tmpdir)

        # Stage 1: Fetch
        print("\n[Stage 1] Fetch - Download logs from GitHub")
        print("-" * 60)

        fetch_output = tmpdir / "raw_log.txt"

        class FetchArgs:
            workflow_name = "ci-tests"
            run_id = 54321
            execution_number = None
            job_id = 11111
            action_name = None
            output = str(fetch_output)
            save_ci = True
            ci_db = str(tmpdir / "ci.db")
            verbose = True
            quiet = False

        result = handle_fetch_command_v2(FetchArgs())
        if result != 0:
            print(f"[X] Fetch failed with exit code {result}")
            return False
        print(f"[OK] Fetch succeeded")

        # Stage 2: Parse
        print("\n[Stage 2] Parse - Transform logs via Anvil")
        print("-" * 60)

        parse_output = tmpdir / "parsed.json"

        class ParseArgs:
            input = str(fetch_output)
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = str(parse_output)
            save_analysis = True
            ci_db = str(tmpdir / "ci.db")
            analysis_db = str(tmpdir / "analysis.db")
            verbose = True
            quiet = False

        result = handle_parse_command_v2(ParseArgs())
        if result != 0:
            print(f"[X] Parse failed with exit code {result}")
            return False
        print(f"[OK] Parse succeeded")

        # Verify parsed output
        if parse_output.exists():
            data = json.loads(parse_output.read_text())
            print(f"  - Passed tests: {data['summary']['passed']}")
            print(f"  - Failed tests: {data['summary']['failed']}")
            print(f"  - Total items: {data['summary']['total_items']}")

        # Stage 3: Sync (with skip flags)
        print("\n[Stage 3] Sync - Complete pipeline orchestration")
        print("-" * 60)

        class SyncArgs:
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            fetch_all = False
            fetch_last = 1
            filter_workflow = None
            skip_fetch = True  # Skip fetch, use existing data
            skip_save_ci = False
            skip_parse = False
            skip_save_analysis = False
            ci_db = str(tmpdir / "ci.db")
            analysis_db = str(tmpdir / "analysis.db")
            verbose = True
            quiet = False

        result = handle_sync_command(SyncArgs())
        if result != 0:
            print(f"[X] Sync failed with exit code {result}")
            return False
        print(f"[OK] Sync succeeded")

        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    """Run all comprehensive tests."""
    print("\n" + "=" * 60)
    print("SCOUT V2 COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Full Pipeline", test_full_pipeline()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status}: {name}")

    print(f"\nResult: {passed}/{total} test suites passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
