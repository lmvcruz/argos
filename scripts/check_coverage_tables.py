import sqlite3

conn = sqlite3.connect('.anvil/history.db')

print("Tables in database:")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]
for t in tables:
    print(f"  {t[0]}")

print("\nChecking for coverage-related tables:")
coverage_tables = [t for t in table_names if 'coverage' in t.lower()]
if coverage_tables:
    print(f"  ✅ Found: {', '.join(coverage_tables)}")
else:
    print("  ❌ No coverage tables found")

print("\nWhat we have:")
print("  ✓ execution_history (test results)")
print("  ✓ entity_statistics (test stats)")

if "coverage_history" in table_names:
    print("  ✅ coverage_history")
else:
    print("  ❌ coverage_history (NOT YET)")

if "coverage_summary" in table_names:
    print("  ✅ coverage_summary")
else:
    print("  ❌ coverage_summary (NOT YET)")

conn.close()

