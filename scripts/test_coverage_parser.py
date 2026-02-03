"""
Test the coverage parser with actual coverage.xml file.
"""

import sys
from pathlib import Path

# Add anvil to path
anvil_path = Path(__file__).parent.parent / "anvil"
sys.path.insert(0, str(anvil_path))

from anvil.parsers.coverage_parser import CoverageParser

def main():
    """Test coverage parser."""
    coverage_file = "forge/coverage.xml"

    if not Path(coverage_file).exists():
        print(f"❌ Coverage file not found: {coverage_file}")
        print("Run tests with coverage first:")
        print("  cd forge && pytest --cov=forge --cov-report=xml")
        return 1

    print(f"Parsing coverage file: {coverage_file}\n")

    parser = CoverageParser()
    data = parser.parse_coverage_xml(coverage_file)

    print(f"✅ Coverage parsed successfully!")
    print(f"\n📊 Coverage Summary:")
    print(f"  Total coverage: {data.total_coverage:.2f}%")
    print(f"  Files analyzed: {data.files_analyzed}")
    print(f"  Total statements: {data.total_statements}")
    print(f"  Covered statements: {data.covered_statements}")

    print(f"\n📁 Top 10 files by coverage:")
    sorted_files = sorted(data.file_coverage, key=lambda x: x.coverage_percentage, reverse=True)
    for i, fc in enumerate(sorted_files[:10], 1):
        print(f"  {i}. {fc.file_path}: {fc.coverage_percentage:.1f}% ({fc.covered_statements}/{fc.total_statements})")

    # Show files with < 100% coverage
    incomplete = [fc for fc in data.file_coverage if fc.coverage_percentage < 100.0]
    if incomplete:
        print(f"\n⚠️  Files with incomplete coverage ({len(incomplete)}):")
        for fc in sorted(incomplete, key=lambda x: x.coverage_percentage)[:5]:
            print(f"  - {fc.file_path}: {fc.coverage_percentage:.1f}% (missing {len(fc.missing_lines)} lines)")

    return 0

if __name__ == "__main__":
    sys.exit(main())
