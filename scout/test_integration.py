#!/usr/bin/env python
"""
Quick integration test for Scout CLI handlers.

Tests basic functionality of fetch, parse, and sync commands.
"""

import json
import sys
import tempfile
from pathlib import Path

# Import directly from the cli.py file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "cli", Path(__file__).parent / "scout" / "cli.py")
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

handle_fetch_command_v2 = cli.handle_fetch_command_v2
handle_parse_command_v2 = cli.handle_parse_command_v2
handle_sync_command = cli.handle_sync_command


def test_parse_from_file():
    """Test basic parsing from file."""
    print("\n=== Testing Parse from File ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create a test log file
        log_file = tmpdir / "test.log"
        log_file.write_text("""
CI Test Execution Log
[INFO] Starting tests
[PASS] test_feature_1 passed in 0.5s
[PASS] test_feature_2 passed in 0.3s
[FAIL] test_feature_3 failed: AssertionError
[INFO] Execution completed
        """)

        output_file = tmpdir / "parsed.json"

        class Args:
            input = str(log_file)
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = str(output_file)
            save_analysis = False
            ci_db = str(tmpdir / "ci.db")
            analysis_db = str(tmpdir / "analysis.db")
            verbose = True
            quiet = False

        result = handle_parse_command_v2(Args())

        if result == 0:
            print(f"✓ Parse completed successfully")
            if output_file.exists():
                data = json.loads(output_file.read_text())
                print(f"  - Passed: {data['summary']['passed']}")
                print(f"  - Failed: {data['summary']['failed']}")
                print(f"  - Total: {data['summary']['total_items']}")
        else:
            print(f"✗ Parse failed with exit code {result}")

        return result


def test_fetch_to_file():
    """Test basic fetch to file."""
    print("\n=== Testing Fetch to File ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        output_file = tmpdir / "raw.log"

        class Args:
            workflow_name = "test-workflow"
            run_id = 12345
            execution_number = None
            job_id = 67890
            action_name = None
            output = str(output_file)
            save_ci = False
            ci_db = str(tmpdir / "ci.db")
            verbose = True
            quiet = False

        result = handle_fetch_command_v2(Args())

        if result == 0:
            print(f"✓ Fetch completed successfully")
            if output_file.exists():
                content = output_file.read_text()
                print(f"  - Output file created: {len(content)} bytes")
        else:
            print(f"✗ Fetch failed with exit code {result}")

        return result


def test_parse_extract_counts():
    """Test that parse correctly extracts pass/fail counts."""
    print("\n=== Testing Parse Count Extraction ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        log_file = tmpdir / "test.log"
        log_file.write_text("""
[PASS] test_1 passed
[PASS] test_2 passed
[PASS] test_3 passed
[FAIL] test_4 failed
[FAIL] test_5 failed
[PASS] test_6 passed
        """)

        output_file = tmpdir / "parsed.json"

        class Args:
            input = str(log_file)
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = str(output_file)
            save_analysis = False
            ci_db = str(tmpdir / "ci.db")
            analysis_db = str(tmpdir / "analysis.db")
            verbose = False
            quiet = True

        result = handle_parse_command_v2(Args())

        if result == 0:
            data = json.loads(output_file.read_text())

            passed = data['summary']['passed']
            failed = data['summary']['failed']
            total = data['summary']['total_items']

            expected_passed = 4
            expected_failed = 2

            if passed == expected_passed and failed == expected_failed:
                print(f"✓ Counts extracted correctly")
                print(f"  - Passed: {passed} (expected {expected_passed})")
                print(f"  - Failed: {failed} (expected {expected_failed})")
                print(f"  - Total: {total}")
            else:
                print(f"✗ Count mismatch!")
                print(f"  - Passed: {passed} (expected {expected_passed})")
                print(f"  - Failed: {failed} (expected {expected_failed})")
                result = 1
        else:
            print(f"✗ Parse failed with exit code {result}")

        return result


def main():
    """Run all integration tests."""
    print("Scout CLI Integration Tests")
    print("=" * 50)

    results = []

    # Run tests
    results.append(("Parse from File", test_parse_from_file()))
    results.append(("Fetch to File", test_fetch_to_file()))
    results.append(("Parse Count Extraction", test_parse_extract_counts()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")

    passed = sum(1 for _, result in results if result == 0)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result == 0 else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nResult: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
