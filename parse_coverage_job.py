"""
Demonstrate Scout's CILogParser parsing a single job
This is what the backend does internally for job-level parsing
"""
import sys
sys.path.insert(0, 'd:/playground/argos/scout')
sys.path.insert(0, 'd:/playground/argos')

import sqlite3
from pathlib import Path
from scout.parsers.ci_log_parser import CILogParser

# Connect to Scout database
db_path = Path.home() / '.scout' / 'lmvcruz' / 'argos' / 'scout.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get the coverage job log
cursor.execute('SELECT raw_content FROM execution_logs WHERE job_id = 62858077997')
log_content = cursor.fetchone()[0]

# Initialize Scout's parser
parser = CILogParser()

print("=" * 80)
print("SCOUT CILogParser - Coverage Job (62858077997)")
print("=" * 80)

# Parse pytest results
test_results = parser.parse_pytest_log(log_content)
passed = sum(1 for t in test_results if t.get('outcome') == 'passed')
failed = sum(1 for t in test_results if t.get('outcome') == 'failed')
skipped = sum(1 for t in test_results if t.get('outcome') == 'skipped')
errors = sum(1 for t in test_results if t.get('outcome') == 'error')

print(f"\n📊 Test Summary:")
print(f"  Total Tests: {len(test_results)}")
print(f"  ✅ Passed:   {passed}")
print(f"  ❌ Failed:   {failed}")
print(f"  ⊘  Skipped:  {skipped}")
print(f"  ⚠  Errors:   {errors}")

# Parse coverage
coverage = parser.parse_coverage_log(log_content)
print(f"\n📈 Coverage Statistics:")
print(f"  Overall Coverage: {coverage['total_coverage']}%")
print(f"  Total Statements: {coverage['total_statements']}")
print(f"  Missing Lines:    {coverage['total_missing']}")
print(f"  Modules Analyzed: {len(coverage['modules'])}")

# Show some module examples
print(f"\n  Top Modules by Coverage:")
sorted_modules = sorted(coverage['modules'], key=lambda m: m['coverage'], reverse=True)
for module in sorted_modules[:5]:
    print(f"    • {module['name']:50} {module['coverage']:5.1f}%")

# Parse flake8
flake8_issues = parser.parse_flake8_log(log_content)
print(f"\n🔧 Code Quality:")
print(f"  Flake8 Issues: {len(flake8_issues)}")

# Show failed tests
failed_tests = [t for t in test_results if t.get('outcome') in ['failed', 'error']]
print(f"\n❌ Failed Tests ({len(failed_tests)} total) - First 5:")
for test in failed_tests[:5]:
    print(f"  • {test['test_nodeid']}")
    if test.get('error_message'):
        error_preview = test['error_message'][:80] + '...' if len(test['error_message']) > 80 else test['error_message']
        print(f"    Error: {error_preview}")

print("\n" + "=" * 80)
print("This is EXACTLY what the backend does in parse_job_data endpoint!")
print("Backend: lens/lens/backend/scout_ci_endpoints.py:parse_job_data()")
print("=" * 80)

conn.close()
