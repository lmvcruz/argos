#!/usr/bin/env python
"""Create test data to verify file caching works."""
from datetime import datetime
from pathlib import Path
import json

# Create test data in the file cache
logs_dir = Path.home() / ".scout" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Create test run
run_id = "123456"
job_id = "1"
run_dir = logs_dir / f"run_{run_id}"
run_dir.mkdir(exist_ok=True)

# Write test log file
log_file = run_dir / f"job_{job_id}.log"
log_content = """Run #123456: Test execution log
==================================
Starting test run...
Running pytest...

tests/test_example.py::test_pass PASSED
tests/test_example.py::test_fail FAILED

FAILURES:
tests/test_example.py::test_fail - AssertionError: Expected True but got False

Summary: 1 passed, 1 failed
"""

log_file.write_text(log_content)
print(f"✓ Created log file: {log_file}")
print(f"  Content preview:")
print(f"  {log_content[:100]}...")

# Write metadata file
meta_file = run_dir / f"job_{job_id}.meta"
meta_content = {
    "run_id": run_id,
    "job_id": job_id,
    "retrieved_at": datetime.now().isoformat(),
    "size_bytes": len(log_content),
    "job_name": "test-job"
}
meta_file.write_text(json.dumps(meta_content, indent=2))
print(f"✓ Created metadata file: {meta_file}")

# List what's in the logs dir
print(f"\n~/.scout/logs/ contents:")
for item in logs_dir.rglob("*"):
    if item.is_file():
        print(f"  {item.relative_to(logs_dir)}")
