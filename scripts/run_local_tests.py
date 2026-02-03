"""
Run local tests with automatic history tracking.

This script runs pytest tests and automatically records execution history
and coverage data to enable local vs CI comparisons in Lens.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project roots to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import (
    ExecutionDatabase,
    ExecutionHistory,
    CoverageHistory,
    CoverageSummary,
    LintViolation,
    LintSummary,
)
from anvil.core.statistics_calculator import StatisticsCalculator
from anvil.parsers.coverage_parser import CoverageParser
from anvil.parsers.lint_parser import LintParser


def parse_pytest_json(json_file: Path):
    """Parse pytest --json-report output."""
    import json

    with open(json_file) as f:
        data = json.load(f)

    results = []
    for test in data.get('tests', []):
        results.append({
            'entity_id': test['nodeid'],
            'status': test['outcome'].upper(),  # passed -> PASSED
            'duration': test.get('duration', 0.0)
        })

    return results


def detect_coverage_files(pytest_args):
    """
    Detect if coverage is being generated and find coverage.xml file.

    Args:
        pytest_args: List of pytest arguments

    Returns:
        Path to coverage.xml if found, None otherwise
    """
    # Check if --cov arguments are present
    has_cov = any(arg.startswith('--cov') for arg in pytest_args)

    if not has_cov:
        return None

    # Look for coverage.xml in common locations
    search_paths = [
        project_root / 'coverage.xml',
        project_root / 'forge' / 'coverage.xml',
        project_root / 'anvil' / 'coverage.xml',
        project_root / 'scout' / 'coverage.xml',
    ]

    for path in search_paths:
        if path.exists():
            # Check if file was modified recently (within last 60 seconds)
            import time
            if time.time() - path.stat().st_mtime < 60:
                return path

    return None


def store_coverage_data(db, execution_id, coverage_file, space, timestamp):
    """
    Parse and store coverage data in database.

    Args:
        db: ExecutionDatabase instance
        execution_id: Execution ID string
        coverage_file: Path to coverage.xml
        space: Execution space (local/ci)
        timestamp: Execution timestamp

    Returns:
        Number of files with coverage data stored
    """
    parser = CoverageParser()

    try:
        coverage_data = parser.parse_coverage_xml(str(coverage_file))
    except Exception as e:
        print(f"   ⚠️  Failed to parse coverage: {e}")
        return 0

    # Store coverage summary
    summary = CoverageSummary(
        execution_id=execution_id,
        timestamp=timestamp,
        total_coverage=coverage_data.total_coverage,
        files_analyzed=coverage_data.files_analyzed,
        total_statements=coverage_data.total_statements,
        covered_statements=coverage_data.covered_statements,
        space=space,
        metadata={'source': 'run_local_tests.py', 'coverage_file': str(coverage_file)},
    )
    db.insert_coverage_summary(summary)

    # Store per-file coverage
    files_stored = 0
    for file_cov in coverage_data.file_coverage:
        history = CoverageHistory(
            execution_id=execution_id,
            file_path=file_cov.file_path,
            timestamp=timestamp,
            total_statements=file_cov.total_statements,
            covered_statements=file_cov.covered_statements,
            coverage_percentage=file_cov.coverage_percentage,
            missing_lines=file_cov.missing_lines,
            space=space,
        )
        db.insert_coverage_history(history)
        files_stored += 1

    return files_stored


def run_flake8_scan(project_paths=None):
    """
    Run flake8 scan on project files.

    Args:
        project_paths: List of paths to scan (default: forge, anvil, scout)

    Returns:
        Tuple of (output_text, return_code)
    """
    if project_paths is None:
        project_paths = ['forge', 'anvil', 'scout']

    # Find which paths exist
    existing_paths = [p for p in project_paths if Path(p).exists()]

    if not existing_paths:
        return None, 1

    try:
        result = subprocess.run(
            ['flake8'] + existing_paths,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        return result.stdout + result.stderr, result.returncode
    except FileNotFoundError:
        print("   ⚠️  flake8 not found - skipping lint scan")
        return None, 1


def run_black_check(project_paths=None):
    """
    Run black --check on project files.

    Args:
        project_paths: List of paths to check (default: forge, anvil, scout)

    Returns:
        Tuple of (output_text, return_code)
    """
    if project_paths is None:
        project_paths = ['forge', 'anvil', 'scout']

    existing_paths = [p for p in project_paths if Path(p).exists()]

    if not existing_paths:
        return None, 1

    try:
        result = subprocess.run(
            ['black', '--check'] + existing_paths,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        return result.stdout + result.stderr, result.returncode
    except FileNotFoundError:
        print("   ⚠️  black not found - skipping formatting check")
        return None, 1


def run_isort_check(project_paths=None):
    """
    Run isort --check-only on project files.

    Args:
        project_paths: List of paths to check (default: forge, anvil, scout)

    Returns:
        Tuple of (output_text, return_code)
    """
    if project_paths is None:
        project_paths = ['forge', 'anvil', 'scout']

    existing_paths = [p for p in project_paths if Path(p).exists()]

    if not existing_paths:
        return None, 1

    try:
        result = subprocess.run(
            ['isort', '--check-only'] + existing_paths,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        return result.stdout + result.stderr, result.returncode
    except FileNotFoundError:
        print("   ⚠️  isort not found - skipping import check")
        return None, 1


def store_lint_data(db, execution_id, lint_output, validator, space, timestamp):
    """
    Parse and store lint data in database.

    Args:
        db: ExecutionDatabase instance
        execution_id: Unique execution identifier
        lint_output: Raw output from lint tool
        validator: Name of validator (flake8, black, isort)
        space: Execution space (local or ci)
        timestamp: Execution timestamp

    Returns:
        Number of violations stored
    """
    parser = LintParser()

    # Parse based on validator type
    if validator == 'flake8':
        lint_data = parser.parse_flake8_output(lint_output, project_root)
    elif validator == 'black':
        lint_data = parser.parse_black_output(lint_output, project_root)
    elif validator == 'isort':
        lint_data = parser.parse_isort_output(lint_output, project_root)
    else:
        return 0

    # Store lint summary
    summary = LintSummary(
        execution_id=f"{execution_id}-{validator}",
        timestamp=timestamp,
        validator=validator,
        files_scanned=lint_data.files_scanned,
        total_violations=lint_data.total_violations,
        errors=lint_data.errors,
        warnings=lint_data.warnings,
        info=lint_data.info,
        by_code=lint_data.by_code,
        space=space,
        metadata={'source': 'run_local_tests.py'},
    )
    db.insert_lint_summary(summary)

    # Store individual violations
    violations_stored = 0
    for file_viols in lint_data.file_violations:
        for viol in file_viols.violations:
            violation = LintViolation(
                execution_id=f"{execution_id}-{validator}",
                file_path=file_viols.file_path,
                line_number=viol['line_number'],
                column_number=viol.get('column_number'),
                severity=viol['severity'],
                code=viol['code'],
                message=viol['message'],
                validator=validator,
                timestamp=timestamp,
                space=space,
            )
            db.insert_lint_violation(violation)
            violations_stored += 1

    return violations_stored


def main():
    """Run tests with history tracking."""
    import argparse

    # Use parse_known_args to allow pytest arguments
    parser = argparse.ArgumentParser(
        description='Run local tests with history tracking',
        epilog='All unknown arguments are passed to pytest'
    )
    parser.add_argument('--db', default='.anvil/history.db', help='Database path')
    parser.add_argument('--space', default='local', help='Execution space')

    args, pytest_args = parser.parse_known_args()

    print("=" * 80)
    print("RUNNING LOCAL TESTS WITH HISTORY TRACKING")
    print("=" * 80)

    # Prepare pytest command with JSON reporter
    json_report = project_root / '.pytest_cache' / f'report-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    json_report.parent.mkdir(parents=True, exist_ok=True)

    pytest_cmd = [
        'python', '-m', 'pytest',
        '--json-report',
        f'--json-report-file={json_report}',
        '--json-report-indent=2'
    ] + (pytest_args if pytest_args else [])

    print(f"\n1. Running pytest: {' '.join(pytest_cmd)}")

    # Run pytest
    result = subprocess.run(pytest_cmd, cwd=project_root)

    if not json_report.exists():
        print(f"\n⚠️  JSON report not found at {json_report}")
        print("   Install pytest-json-report: pip install pytest-json-report")
        return result.returncode

    print(f"\n2. Parsing test results from {json_report}")

    try:
        test_results = parse_pytest_json(json_report)
        print(f"   Found {len(test_results)} test results")
    except Exception as e:
        print(f"   ❌ Error parsing results: {e}")
        return 1

    if not test_results:
        print("   ℹ️  No test results to record")
        return result.returncode

    # Store in database
    print(f"\n3. Storing results in {args.db}")
    db = ExecutionDatabase(args.db)

    execution_id = f"local-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now()

    for test_result in test_results:
        history = ExecutionHistory(
            execution_id=execution_id,
            entity_id=test_result['entity_id'],
            entity_type='test',
            timestamp=timestamp,
            status=test_result['status'],
            duration=test_result.get('duration'),
            space=args.space,
            metadata={
                'source': 'run_local_tests.py',
                'pytest_args': ' '.join(pytest_args) if pytest_args else 'default'
            }
        )
        db.insert_execution_history(history)

    print(f"   ✓ Stored {len(test_results)} test results")

    # Update statistics
    print("\n4. Updating statistics...")
    calculator = StatisticsCalculator(db)
    stats = calculator.calculate_all_stats(entity_type='test', window=None)

    for stat in stats:
        db.update_entity_statistics(stat)

    print(f"   ✓ Updated statistics for {len(stats)} entities")

    # Check for coverage data
    coverage_file = detect_coverage_files(pytest_args if pytest_args else [])
    coverage_summary = None

    if coverage_file:
        print(f"\n5. Processing coverage data from {coverage_file}")
        files_stored = store_coverage_data(db, execution_id, coverage_file, args.space, timestamp)
        print(f"   ✓ Stored coverage for {files_stored} files")

        # Get coverage summary
        summaries = db.get_coverage_summary(execution_id=execution_id)
        if summaries:
            coverage_summary = summaries[0]
            print(f"   📊 Overall coverage: {coverage_summary.total_coverage:.2f}%")
    else:
        if any('--cov' in arg for arg in (pytest_args or [])):
            print(f"\n⚠️  Coverage requested but no coverage.xml found")
            print("   Make sure to include: --cov-report=xml")

    # Run lint checks
    print("\n6. Running code quality checks...")
    lint_summaries = {}

    # Run flake8
    flake8_output, flake8_code = run_flake8_scan()
    if flake8_output:
        violations = store_lint_data(db, execution_id, flake8_output, 'flake8', args.space, timestamp)
        lint_summaries['flake8'] = violations
        print(f"   ✓ flake8: {violations} violations found")

    # Run black
    black_output, black_code = run_black_check()
    if black_output and 'would reformat' in black_output:
        violations = store_lint_data(db, execution_id, black_output, 'black', args.space, timestamp)
        lint_summaries['black'] = violations
        print(f"   ✓ black: {violations} formatting issues found")

    # Run isort
    isort_output, isort_code = run_isort_check()
    if isort_output and 'ERROR:' in isort_output:
        violations = store_lint_data(db, execution_id, isort_output, 'isort', args.space, timestamp)
        lint_summaries['isort'] = violations
        print(f"   ✓ isort: {violations} import issues found")

    if not lint_summaries:
        print("   ✓ No code quality issues found")

    db.close()

    # Summary
    print("\n" + "=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Execution ID: {execution_id}")
    print(f"  Tests Run: {len(test_results)}")
    print(f"  Space: {args.space}")
    print(f"  Database: {args.db}")

    passed = sum(1 for r in test_results if r['status'] == 'PASSED')
    failed = sum(1 for r in test_results if r['status'] == 'FAILED')
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if coverage_summary:
        print(f"  Coverage: {coverage_summary.total_coverage:.2f}%")

    if lint_summaries:
        print(f"  Code Quality:")
        total_violations = sum(lint_summaries.values())
        for validator, count in lint_summaries.items():
            print(f"    {validator}: {count} issues")
        print(f"    Total: {total_violations} issues")

    print("\n📊 View results:")
    print(f"  cd lens")
    print(f"  python -m lens report test-execution --db ../{args.db} --format html")
    if coverage_file:
        print(f"  python -m lens report coverage --db ../{args.db} --format html")
    if lint_summaries:
        print(f"  python ../scripts/generate_quality_report.py --db {args.db} --format html")
    print()

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
