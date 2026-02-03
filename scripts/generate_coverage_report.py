"""
Generate coverage report from Anvil database.

This script generates comprehensive coverage reports showing:
- Coverage trends over time
- Per-file coverage analysis
- Coverage regressions
- Coverage gaps

Usage:
    python scripts/generate_coverage_report.py --format html
    python scripts/generate_coverage_report.py --format markdown --output coverage-report.md
    python scripts/generate_coverage_report.py --space ci --window 30
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add anvil to path
anvil_path = Path(__file__).parent.parent / "anvil"
sys.path.insert(0, str(anvil_path))

from anvil.storage.execution_schema import ExecutionDatabase


def generate_html_report(db, space, window):
    """
    Generate HTML coverage report.

    Args:
        db: ExecutionDatabase instance
        space: Filter by space (local/ci/all)
        window: Number of days to include

    Returns:
        HTML content as string
    """
    # Get coverage summaries
    summaries = db.get_coverage_summary(space=space if space != "all" else None, limit=100)

    if not summaries:
        return "<html><body><h1>No coverage data found</h1></body></html>"

    # Filter by window
    if window:
        cutoff = datetime.now() - timedelta(days=window)
        summaries = [s for s in summaries if s.timestamp >= cutoff]

    # Get latest summary
    latest = summaries[0] if summaries else None

    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .coverage-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .coverage-value {{
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .coverage-good {{ color: #28a745; }}
        .coverage-warning {{ color: #ffc107; }}
        .coverage-bad {{ color: #dc3545; }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .progress-bar {{
            width: 100px;
            height: 20px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            display: inline-block;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s;
        }}
        .trend-up {{ color: #28a745; }}
        .trend-down {{ color: #dc3545; }}
        .trend-stable {{ color: #6c757d; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Coverage Report</h1>
        <div class="subtitle">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            Space: {space.upper()} |
            Window: {window if window else 'All'} days
        </div>
    </div>
"""

    if latest:
        coverage_class = (
            "coverage-good" if latest.total_coverage >= 80
            else "coverage-warning" if latest.total_coverage >= 60
            else "coverage-bad"
        )

        html += f"""
    <div class="coverage-box">
        <h2>Overall Coverage</h2>
        <div class="coverage-value {coverage_class}">
            {latest.total_coverage:.2f}%
        </div>
        <div class="metric">
            <div class="metric-label">Files Analyzed</div>
            <div class="metric-value">{latest.files_analyzed}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Total Statements</div>
            <div class="metric-value">{latest.total_statements:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Covered Statements</div>
            <div class="metric-value">{latest.covered_statements:,}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Last Updated</div>
            <div class="metric-value">{latest.timestamp.strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </div>
"""

    # Coverage trend
    if len(summaries) > 1:
        html += """
    <div class="coverage-box">
        <h2>Coverage Trend</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Execution ID</th>
                    <th>Coverage</th>
                    <th>Files</th>
                    <th>Statements</th>
                    <th>Trend</th>
                </tr>
            </thead>
            <tbody>
"""
        for i, summary in enumerate(summaries[:20]):
            trend = ""
            if i < len(summaries) - 1:
                diff = summary.total_coverage - summaries[i + 1].total_coverage
                if diff > 0.5:
                    trend = f'<span class="trend-up">▲ +{diff:.2f}%</span>'
                elif diff < -0.5:
                    trend = f'<span class="trend-down">▼ {diff:.2f}%</span>'
                else:
                    trend = '<span class="trend-stable">━ stable</span>'

            coverage_class = (
                "coverage-good" if summary.total_coverage >= 80
                else "coverage-warning" if summary.total_coverage >= 60
                else "coverage-bad"
            )

            html += f"""
                <tr>
                    <td>{summary.timestamp.strftime('%Y-%m-%d %H:%M')}</td>
                    <td><code>{summary.execution_id}</code></td>
                    <td class="{coverage_class}"><strong>{summary.total_coverage:.2f}%</strong></td>
                    <td>{summary.files_analyzed}</td>
                    <td>{summary.covered_statements:,} / {summary.total_statements:,}</td>
                    <td>{trend}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

    # Per-file coverage (latest)
    if latest:
        file_coverage = db.get_coverage_history(execution_id=latest.execution_id, limit=1000)

        if file_coverage:
            # Sort by coverage percentage
            file_coverage.sort(key=lambda x: x.coverage_percentage)

            html += """
    <div class="coverage-box">
        <h2>Per-File Coverage (Latest Execution)</h2>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Coverage</th>
                    <th>Statements</th>
                    <th>Missing Lines</th>
                    <th>Progress</th>
                </tr>
            </thead>
            <tbody>
"""
            for fc in file_coverage:
                coverage_class = (
                    "coverage-good" if fc.coverage_percentage >= 80
                    else "coverage-warning" if fc.coverage_percentage >= 60
                    else "coverage-bad"
                )

                missing_count = len(fc.missing_lines) if fc.missing_lines else 0
                missing_preview = ""
                if fc.missing_lines and missing_count <= 5:
                    missing_preview = ", ".join(str(line) for line in fc.missing_lines[:5])
                elif fc.missing_lines:
                    missing_preview = f"{', '.join(str(line) for line in fc.missing_lines[:5])}... (+{missing_count - 5})"

                html += f"""
                <tr>
                    <td><code>{fc.file_path}</code></td>
                    <td class="{coverage_class}"><strong>{fc.coverage_percentage:.1f}%</strong></td>
                    <td>{fc.covered_statements} / {fc.total_statements}</td>
                    <td>{missing_count} lines {f'({missing_preview})' if missing_preview else ''}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill {coverage_class}"
                                 style="width: {fc.coverage_percentage}%; background: currentColor;">
                            </div>
                        </div>
                    </td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""

    html += """
</body>
</html>
"""

    return html


def generate_markdown_report(db, space, window):
    """
    Generate Markdown coverage report.

    Args:
        db: ExecutionDatabase instance
        space: Filter by space (local/ci/all)
        window: Number of days to include

    Returns:
        Markdown content as string
    """
    summaries = db.get_coverage_summary(space=space if space != "all" else None, limit=100)

    if not summaries:
        return "# Coverage Report\n\nNo coverage data found."

    # Filter by window
    if window:
        cutoff = datetime.now() - timedelta(days=window)
        summaries = [s for s in summaries if s.timestamp >= cutoff]

    latest = summaries[0] if summaries else None

    md = f"""# 📊 Coverage Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Space:** {space.upper()}
**Window:** {window if window else 'All'} days

---

"""

    if latest:
        md += f"""## Overall Coverage

- **Coverage:** {latest.total_coverage:.2f}%
- **Files Analyzed:** {latest.files_analyzed}
- **Total Statements:** {latest.total_statements:,}
- **Covered Statements:** {latest.covered_statements:,}
- **Last Updated:** {latest.timestamp.strftime('%Y-%m-%d %H:%M')}

---

"""

    # Coverage trend
    if len(summaries) > 1:
        md += """## Coverage Trend

| Date | Execution ID | Coverage | Files | Statements | Trend |
|------|--------------|----------|-------|------------|-------|
"""
        for i, summary in enumerate(summaries[:20]):
            trend = ""
            if i < len(summaries) - 1:
                diff = summary.total_coverage - summaries[i + 1].total_coverage
                if diff > 0.5:
                    trend = f'📈 +{diff:.2f}%'
                elif diff < -0.5:
                    trend = f'📉 {diff:.2f}%'
                else:
                    trend = '━ stable'

            md += f"| {summary.timestamp.strftime('%Y-%m-%d %H:%M')} | `{summary.execution_id}` | **{summary.total_coverage:.2f}%** | {summary.files_analyzed} | {summary.covered_statements:,} / {summary.total_statements:,} | {trend} |\n"

        md += "\n---\n\n"

    # Per-file coverage
    if latest:
        file_coverage = db.get_coverage_history(execution_id=latest.execution_id, limit=1000)

        if file_coverage:
            # Show files with < 100% coverage
            incomplete = [fc for fc in file_coverage if fc.coverage_percentage < 100.0]
            incomplete.sort(key=lambda x: x.coverage_percentage)

            md += f"""## Files with Incomplete Coverage ({len(incomplete)})

| File | Coverage | Statements | Missing Lines |
|------|----------|------------|---------------|
"""
            for fc in incomplete[:50]:  # Top 50 files
                missing_count = len(fc.missing_lines) if fc.missing_lines else 0
                missing_preview = ""
                if fc.missing_lines and missing_count <= 3:
                    missing_preview = ", ".join(str(line) for line in fc.missing_lines[:3])
                elif fc.missing_lines:
                    missing_preview = f"{', '.join(str(line) for line in fc.missing_lines[:3])}... (+{missing_count - 3})"

                md += f"| `{fc.file_path}` | {fc.coverage_percentage:.1f}% | {fc.covered_statements} / {fc.total_statements} | {missing_count} lines {f'({missing_preview})' if missing_preview else ''} |\n"

    return md


def main():
    """Generate coverage report."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate coverage report')
    parser.add_argument('--db', default='.anvil/history.db', help='Database path')
    parser.add_argument(
        '--space', default='all', choices=['all', 'local', 'ci'], help='Filter by space'
    )
    parser.add_argument('--window', type=int, help='Window in days (default: all data)')
    parser.add_argument(
        '--format', default='html', choices=['html', 'markdown'], help='Report format'
    )
    parser.add_argument('--output', help='Output file (default: stdout or coverage-report.{ext})')

    args = parser.parse_args()

    # Open database
    db = ExecutionDatabase(args.db)

    # Generate report
    if args.format == 'html':
        content = generate_html_report(db, args.space, args.window)
        default_output = 'coverage-report.html'
    else:
        content = generate_markdown_report(db, args.space, args.window)
        default_output = 'coverage-report.md'

    db.close()

    # Write output
    output_file = args.output or default_output

    if output_file == '-':
        print(content)
    else:
        Path(output_file).write_text(content, encoding='utf-8')
        print(f"✅ Coverage report generated: {output_file}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
