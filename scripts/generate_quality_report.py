"""
Generate code quality reports from lint violation data.

This script generates HTML and Markdown reports showing code quality trends,
violations by severity, most common issues, and quality improvements over time.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add anvil to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import ExecutionDatabase


def generate_comparison_report(db: ExecutionDatabase, validator: Optional[str] = None) -> str:
    """
    Generate HTML comparison report between local and CI quality.

    Args:
        db: ExecutionDatabase instance
        validator: Filter by validator (flake8/black/isort) or None for all

    Returns:
        HTML comparison report string
    """
    # Get latest local and CI summaries
    local_summaries = db.get_lint_summary(space="local", validator=validator, limit=10)
    ci_summaries = db.get_lint_summary(space="ci", validator=validator, limit=10)

    # Group by validator
    local_by_validator = {}
    for s in local_summaries:
        if s.validator not in local_by_validator:
            local_by_validator[s.validator] = s

    ci_by_validator = {}
    for s in ci_summaries:
        if s.validator not in ci_by_validator:
            ci_by_validator[s.validator] = s

    # Get all validators
    all_validators = set(local_by_validator.keys()) | set(ci_by_validator.keys())

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Local vs CI Quality Comparison</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
        }}
        .metric-card.local {{
            border-color: #3498db;
        }}
        .metric-card.ci {{
            border-color: #9b59b6;
        }}
        .metric-card h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .diff {{
            font-size: 18px;
            margin-top: 10px;
        }}
        .diff.better {{
            color: #27ae60;
        }}
        .diff.worse {{
            color: #e74c3c;
        }}
        .diff.same {{
            color: #95a5a6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .space-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .space-badge.local {{
            background-color: #3498db;
            color: white;
        }}
        .space-badge.ci {{
            background-color: #9b59b6;
            color: white;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Local vs CI Quality Comparison</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Comparison by Validator</h2>
    """

    for val in sorted(all_validators):
        local_summary = local_by_validator.get(val)
        ci_summary = ci_by_validator.get(val)

        local_violations = local_summary.total_violations if local_summary else 0
        ci_violations = ci_summary.total_violations if ci_summary else 0

        diff = local_violations - ci_violations
        diff_class = "better" if diff < 0 else ("worse" if diff > 0 else "same")
        diff_symbol = "↓" if diff < 0 else ("↑" if diff > 0 else "=")

        html += f"""
        <div style="margin: 30px 0;">
            <h3 style="text-align: center; color: #34495e;">{val.upper()}</h3>
            <div class="comparison-grid">
                <div class="metric-card local">
                    <h3><span class="space-badge local">LOCAL</span></h3>
                    <div class="metric-value">{local_violations}</div>
                    <div class="metric-label">Total Violations</div>
        """

        if local_summary:
            html += f"""
                    <div style="margin-top: 10px; font-size: 14px;">
                        Errors: {local_summary.errors} |
                        Warnings: {local_summary.warnings} |
                        Info: {local_summary.info}
                    </div>
                    <div class="timestamp">Last run: {local_summary.timestamp.strftime('%Y-%m-%d %H:%M')}</div>
            """
        else:
            html += """
                    <div style="margin-top: 10px; font-size: 14px; color: #95a5a6;">
                        No local data
                    </div>
            """

        html += f"""
                </div>
                <div class="metric-card ci">
                    <h3><span class="space-badge ci">CI</span></h3>
                    <div class="metric-value">{ci_violations}</div>
                    <div class="metric-label">Total Violations</div>
        """

        if ci_summary:
            html += f"""
                    <div style="margin-top: 10px; font-size: 14px;">
                        Errors: {ci_summary.errors} |
                        Warnings: {ci_summary.warnings} |
                        Info: {ci_summary.info}
                    </div>
                    <div class="timestamp">Last run: {ci_summary.timestamp.strftime('%Y-%m-%d %H:%M')}</div>
            """
        else:
            html += """
                    <div style="margin-top: 10px; font-size: 14px; color: #95a5a6;">
                        No CI data
                    </div>
            """

        html += """
                </div>
            </div>
        """

        # Add difference indicator
        if local_summary and ci_summary:
            html += f"""
            <div style="text-align: center; margin-top: 10px;">
                <div class="diff {diff_class}">
                    {diff_symbol} {abs(diff)} violations difference
                </div>
                <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">
                    {"Local has fewer violations ✅" if diff < 0 else ("Local has more violations ⚠️" if diff > 0 else "Same quality level")}
                </div>
            </div>
            """

        html += "</div>"

    html += """
    </div>
</body>
</html>
    """

    return html


def generate_html_report(
    db: ExecutionDatabase,
    space: Optional[str] = None,
    window_days: Optional[int] = None,
    validator: Optional[str] = None,
) -> str:
    """
    Generate HTML quality report.

    Args:
        db: ExecutionDatabase instance
        space: Filter by execution space (local/ci) or None for all
        window_days: Number of days to include in report
        validator: Filter by validator (flake8/black/isort) or None for all

    Returns:
        HTML report string
    """
    # Calculate time window
    cutoff_time = None
    if window_days:
        cutoff_time = datetime.now() - timedelta(days=window_days)

    # Get lint summaries
    summaries = db.get_lint_summary(space=space, validator=validator, limit=100)

    # Filter by time window
    if cutoff_time:
        summaries = [s for s in summaries if s.timestamp >= cutoff_time]

    if not summaries:
        return "<html><body><h1>No quality data found</h1></body></html>"

    # Calculate metrics
    total_violations = sum(s.total_violations for s in summaries)
    total_errors = sum(s.errors for s in summaries)
    total_warnings = sum(s.warnings for s in summaries)
    total_info = sum(s.info for s in summaries)

    # Get latest summary per validator
    latest_by_validator = {}
    for summary in summaries:
        if summary.validator not in latest_by_validator:
            latest_by_validator[summary.validator] = summary

    # Get violations for detailed breakdown
    violations = db.get_lint_violations(space=space, validator=validator, limit=1000)

    # Filter by time window
    if cutoff_time:
        violations = [v for v in violations if v.timestamp >= cutoff_time]

    # Aggregate violations by code
    by_code: Dict[str, int] = {}
    for viol in violations:
        by_code[viol.code] = by_code.get(viol.code, 0) + 1

    # Aggregate violations by file
    by_file: Dict[str, List] = {}
    for viol in violations:
        if viol.file_path not in by_file:
            by_file[viol.file_path] = []
        by_file[viol.file_path].append(viol)

    # Sort by frequency
    top_codes = sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:10]
    top_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Code Quality Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-card.error {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .metric-card.warning {{
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            color: #2d3436;
        }}
        .metric-card.info {{
            background: linear-gradient(135deg, #a8edea 0%, #74b9ff 100%);
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .severity-ERROR {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .severity-WARNING {{
            color: #f39c12;
            font-weight: bold;
        }}
        .severity-INFO {{
            color: #3498db;
        }}
        .code {{
            font-family: 'Courier New', monospace;
            background-color: #ecf0f1;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .validator-badge {{
            display: inline-block;
            background-color: #9b59b6;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Code Quality Report</h1>

        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Space: <strong>{space or 'All'}</strong> |
           Validator: <strong>{validator or 'All'}</strong> |
           Window: <strong>{window_days or 'All'} days</strong></p>

        <h2>Overall Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total Violations</div>
                <div class="metric-value">{total_violations}</div>
            </div>
            <div class="metric-card error">
                <div class="metric-label">Errors</div>
                <div class="metric-value">{total_errors}</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-label">Warnings</div>
                <div class="metric-value">{total_warnings}</div>
            </div>
            <div class="metric-card info">
                <div class="metric-label">Info</div>
                <div class="metric-value">{total_info}</div>
            </div>
        </div>

        <h2>Latest Results by Validator</h2>
        <table>
            <thead>
                <tr>
                    <th>Validator</th>
                    <th>Files Scanned</th>
                    <th>Violations</th>
                    <th>Errors</th>
                    <th>Warnings</th>
                    <th>Info</th>
                    <th>Last Run</th>
                </tr>
            </thead>
            <tbody>
    """

    for val, summary in sorted(latest_by_validator.items()):
        html += f"""
                <tr>
                    <td><span class="validator-badge">{val}</span></td>
                    <td>{summary.files_scanned}</td>
                    <td><strong>{summary.total_violations}</strong></td>
                    <td class="severity-ERROR">{summary.errors}</td>
                    <td class="severity-WARNING">{summary.warnings}</td>
                    <td class="severity-INFO">{summary.info}</td>
                    <td class="timestamp">{summary.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>

        <h2>Top Violation Codes</h2>
        <table>
            <thead>
                <tr>
                    <th>Code</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
    """

    for code, count in top_codes:
        percentage = (count / total_violations * 100) if total_violations > 0 else 0
        html += f"""
                <tr>
                    <td><span class="code">{code}</span></td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
        """

    html += """
            </tbody>
        </table>

        <h2>Files with Most Violations</h2>
        <table>
            <thead>
                <tr>
                    <th>File Path</th>
                    <th>Violations</th>
                    <th>Errors</th>
                    <th>Warnings</th>
                </tr>
            </thead>
            <tbody>
    """

    for file_path, file_viols in top_files:
        errors = sum(1 for v in file_viols if v.severity == "ERROR")
        warnings = sum(1 for v in file_viols if v.severity == "WARNING")
        html += f"""
                <tr>
                    <td>{file_path}</td>
                    <td><strong>{len(file_viols)}</strong></td>
                    <td class="severity-ERROR">{errors}</td>
                    <td class="severity-WARNING">{warnings}</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
    """

    return html


def generate_markdown_report(
    db: ExecutionDatabase,
    space: Optional[str] = None,
    window_days: Optional[int] = None,
    validator: Optional[str] = None,
) -> str:
    """
    Generate Markdown quality report.

    Args:
        db: ExecutionDatabase instance
        space: Filter by execution space (local/ci) or None for all
        window_days: Number of days to include in report
        validator: Filter by validator (flake8/black/isort) or None for all

    Returns:
        Markdown report string
    """
    # Calculate time window
    cutoff_time = None
    if window_days:
        cutoff_time = datetime.now() - timedelta(days=window_days)

    # Get lint summaries
    summaries = db.get_lint_summary(space=space, validator=validator, limit=100)

    # Filter by time window
    if cutoff_time:
        summaries = [s for s in summaries if s.timestamp >= cutoff_time]

    if not summaries:
        return "# Code Quality Report\n\nNo quality data found."

    # Calculate metrics
    total_violations = sum(s.total_violations for s in summaries)
    total_errors = sum(s.errors for s in summaries)
    total_warnings = sum(s.warnings for s in summaries)
    total_info = sum(s.info for s in summaries)

    # Get latest summary per validator
    latest_by_validator = {}
    for summary in summaries:
        if summary.validator not in latest_by_validator:
            latest_by_validator[summary.validator] = summary

    # Get violations for detailed breakdown
    violations = db.get_lint_violations(space=space, validator=validator, limit=1000)

    # Filter by time window
    if cutoff_time:
        violations = [v for v in violations if v.timestamp >= cutoff_time]

    # Aggregate violations by code
    by_code: Dict[str, int] = {}
    for viol in violations:
        by_code[viol.code] = by_code.get(viol.code, 0) + 1

    # Sort by frequency
    top_codes = sorted(by_code.items(), key=lambda x: x[1], reverse=True)[:10]

    # Build Markdown
    md = f"""# Code Quality Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Space**: {space or 'All'}
**Validator**: {validator or 'All'}
**Window**: {window_days or 'All'} days

## Overall Metrics

| Metric | Count |
|--------|-------|
| Total Violations | {total_violations} |
| Errors | {total_errors} |
| Warnings | {total_warnings} |
| Info | {total_info} |

## Latest Results by Validator

| Validator | Files Scanned | Violations | Errors | Warnings | Info | Last Run |
|-----------|---------------|------------|--------|----------|------|----------|
"""

    for val, summary in sorted(latest_by_validator.items()):
        last_run = summary.timestamp.strftime('%Y-%m-%d %H:%M')
        md += f"| {val} | {summary.files_scanned} | {summary.total_violations} | {summary.errors} | {summary.warnings} | {summary.info} | {last_run} |\n"

    md += f"""
## Top Violation Codes

| Code | Count | Percentage |
|------|-------|------------|
"""

    for code, count in top_codes:
        percentage = (count / total_violations * 100) if total_violations > 0 else 0
        md += f"| `{code}` | {count} | {percentage:.1f}% |\n"

    return md


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate code quality reports from lint data")
    parser.add_argument("--db", default=".anvil/history.db", help="Database path")
    parser.add_argument(
        "--space", choices=["local", "ci", "all"], default="all", help="Filter by execution space"
    )
    parser.add_argument("--window", type=int, help="Number of days to include in report")
    parser.add_argument(
        "--validator",
        choices=["flake8", "black", "isort", "all"],
        default="all",
        help="Filter by validator",
    )
    parser.add_argument(
        "--format", choices=["html", "markdown", "both"], default="html", help="Report format"
    )
    parser.add_argument("--output", help="Output file path (default: quality-report.<ext>)")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Generate local vs CI comparison report (ignores --space and --window)",
    )

    args = parser.parse_args()

    # Open database
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ Database not found: {args.db}")
        print("   Run tests first: python scripts/run_local_tests.py")
        return 1

    db = ExecutionDatabase(str(db_path))

    # Handle comparison mode
    if args.compare:
        validator = None if args.validator == "all" else args.validator
        html = generate_comparison_report(db, validator=validator)
        output_path = args.output or "quality-comparison.html"
        Path(output_path).write_text(html, encoding="utf-8")
        print(f"✅ Comparison report generated: {output_path}")
        print(f"   Open in browser to view local vs CI quality differences")
        db.close()
        return 0

    # Resolve space and validator
    space = None if args.space == "all" else args.space
    validator = None if args.validator == "all" else args.validator

    # Generate reports
    if args.format in ["html", "both"]:
        html = generate_html_report(db, space=space, window_days=args.window, validator=validator)
        output_path = args.output or "quality-report.html"
        Path(output_path).write_text(html, encoding="utf-8")
        print(f"✅ HTML report generated: {output_path}")

    if args.format in ["markdown", "both"]:
        md = generate_markdown_report(db, space=space, window_days=args.window, validator=validator)
        output_path = args.output or "quality-report.md"
        Path(output_path).write_text(md, encoding="utf-8")
        print(f"✅ Markdown report generated: {output_path}")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
