"""
Example: Using AnvilBridge as a parser adapter in Scout.

This example shows how Scout extracts validator output from CI logs
and uses AnvilBridge to parse it with Anvil's parsers, saving results
to Scout DB (not Anvil DB).
"""

from pathlib import Path
from scout.integration.anvil_bridge import AnvilBridge, AnvilLogExtractor


def example_parse_ci_log():
    """
    Example: Extract and parse validator output from CI log.

    Architecture:
        1. Scout fetches CI logs from GitHub → Scout DB
        2. AnvilLogExtractor extracts validator output from full log
        3. AnvilBridge parses output using Anvil parsers
        4. Scout saves parsed results to Scout DB
    """
    # Simulated CI log content
    ci_log = """
    Setting up Python environment...
    Installing dependencies...

    Running black
    All done! ✨ 🍰 ✨
    2 files would be reformatted, 5 files would be left unchanged.

    Running flake8
    ./scout/cli.py:123:80: E501 line too long (85 > 79 characters)
    ./scout/storage.py:45:1: F401 'sys' imported but unused

    Running pytest
    ============================= test session starts =============================
    platform linux -- Python 3.10.0, pytest-7.4.0
    collected 156 items

    tests/test_cli.py .........F.F
    tests/test_storage.py ...

    =========================== 2 failed, 154 passed in 12.34s ===================
    """

    # Step 1: Detect which validators ran
    extractor = AnvilLogExtractor()
    detected_validators = extractor.detect_validators_in_log(ci_log)
    print(f"Detected validators: {detected_validators}")
    # Output: ['black', 'flake8', 'pytest']

    # Step 2: Extract validator-specific output
    black_output = extractor.extract_validator_output(ci_log, "black")
    flake8_output = extractor.extract_validator_output(ci_log, "flake8")
    pytest_output = extractor.extract_validator_output(ci_log, "pytest")

    # Step 3: Parse using AnvilBridge
    bridge = AnvilBridge()

    # Get list of supported validators
    print(f"Supported validators: {bridge.get_supported_validators()}")

    # Parse black output
    if black_output:
        black_result = bridge.parse_ci_log_section("black", black_output)
        print(f"\nBlack result: {black_result['validator_name']}")
        print(f"  Passed: {black_result['passed']}")
        print(f"  Errors: {len(black_result['errors'])}")
        print(f"  Warnings: {len(black_result['warnings'])}")

        # Scout would save black_result to Scout DB here
        # save_to_scout_db(run_id, job_id, "black", black_result)

    # Parse flake8 output
    if flake8_output:
        flake8_result = bridge.parse_ci_log_section("flake8", flake8_output)
        print(f"\nFlake8 result: {flake8_result['validator_name']}")
        print(f"  Passed: {flake8_result['passed']}")
        print(f"  Errors: {len(flake8_result['errors'])}")

        # Scout would save flake8_result to Scout DB here
        # save_to_scout_db(run_id, job_id, "flake8", flake8_result)

    # Parse pytest output
    if pytest_output:
        pytest_result = bridge.parse_ci_log_section(
            "pytest",
            pytest_output,
            files=[Path("tests")],  # Affected files
            config={}  # Pytest config if available
        )
        print(f"\nPytest result: {pytest_result['validator_name']}")
        print(f"  Passed: {pytest_result['passed']}")
        print(f"  Errors: {len(pytest_result['errors'])}")

        # Scout would save pytest_result to Scout DB here
        # save_to_scout_db(run_id, job_id, "pytest", pytest_result)

    print("\n✓ All validator outputs parsed successfully")
    print("✓ Results ready to save to Scout DB")
    print("✗ NO data written to Anvil DB (correct behavior)")


def example_parse_direct():
    """
    Example: Directly parse validator output (without log extraction).

    Use this when you already have isolated validator output.
    """
    bridge = AnvilBridge()

    # Example: Parse black output directly
    black_output = """
    would reformat scout/cli.py
    would reformat scout/storage.py
    2 files would be reformatted, 5 files would be left unchanged.
    """

    files = [Path("scout/cli.py"), Path("scout/storage.py")]
    result = bridge.parse_validator_output(
        validator_name="black",
        output=black_output,
        files=files,
        output_format="text"
    )

    print(f"Validator: {result['validator_name']}")
    print(f"Passed: {result['passed']}")
    print(f"Files checked: {result['files_checked']}")
    print(f"Errors: {len(result['errors'])}")
    print(f"Warnings: {len(result['warnings'])}")

    # Scout saves this to Scout DB
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Example 1: Parse CI log with multiple validators")
    print("=" * 70)
    example_parse_ci_log()

    print("\n" + "=" * 70)
    print("Example 2: Parse validator output directly")
    print("=" * 70)
    example_parse_direct()
