"""Test script for lint database schema."""

from anvil.anvil.storage.execution_schema import (
    CodeQualityMetrics,
    ExecutionDatabase,
    LintSummary,
    LintViolation,
)
from datetime import datetime

# Initialize database
db = ExecutionDatabase(":memory:")
print("✅ Schema initialized successfully")

# List all tables
cursor = db.connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"\n📊 Total tables created: {len(tables)}")
for table in tables:
    print(f"  - {table}")

# Check lint tables specifically
lint_tables = [t for t in tables if "lint" in t or "quality" in t]
print(f"\n✅ Lint-specific tables: {len(lint_tables)}")
for t in lint_tables:
    print(f"  ✓ {t}")

# Test inserting a lint violation
test_violation = LintViolation(
    execution_id="test-exec-001",
    file_path="forge/models/test.py",
    line_number=42,
    column_number=10,
    severity="ERROR",
    code="E501",
    message="line too long (105 > 100 characters)",
    validator="flake8",
    timestamp=datetime.now(),
    space="local",
)

violation_id = db.insert_lint_violation(test_violation)
print(f"\n✅ Inserted test violation with ID: {violation_id}")

# Test inserting a lint summary
test_summary = LintSummary(
    execution_id="test-exec-001",
    timestamp=datetime.now(),
    validator="flake8",
    files_scanned=10,
    total_violations=5,
    errors=2,
    warnings=3,
    info=0,
    by_code={"E501": 2, "W503": 3},
    space="local",
)

summary_id = db.insert_lint_summary(test_summary)
print(f"✅ Inserted test summary with ID: {summary_id}")

# Test querying lint data
violations = db.get_lint_violations(execution_id="test-exec-001")
print(f"\n✅ Retrieved {len(violations)} violations")

summaries = db.get_lint_summary(execution_id="test-exec-001")
print(f"✅ Retrieved {len(summaries)} summaries")

# Test code quality metrics
test_metrics = CodeQualityMetrics(
    file_path="forge/models/test.py",
    validator="flake8",
    total_scans=5,
    total_violations=10,
    avg_violations_per_scan=2.0,
    most_common_code="E501",
    last_scan=datetime.now(),
    last_violation=datetime.now(),
    last_updated=datetime.now(),
)

metrics_id = db.upsert_code_quality_metrics(test_metrics)
print(f"✅ Inserted/updated quality metrics with ID: {metrics_id}")

# Query quality metrics
metrics = db.get_code_quality_metrics(file_path="forge/models/test.py")
print(f"✅ Retrieved {len(metrics)} quality metrics")

print("\n🎉 All lint schema tests passed!")
db.close()
