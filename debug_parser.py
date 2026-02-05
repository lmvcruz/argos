#!/usr/bin/env python3
import re
import json

sample_output = """tests/test_example.py::test_pass1 PASSED                             [20%]
tests/test_example.py::test_fail1 FAILED                             [40%]
tests/test_example.py::test_skip1 SKIPPED                            [60%]
tests/test_example.py::test_pass2 PASSED                             [80%]

=== 2 passed, 1 failed, 1 skipped in 0.35s ==="""

lines = sample_output.split("\n")
tests = []
summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0.0}

for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")

    # Look for test result lines
    match = re.search(r"(\S+?::\S+)\s+(PASSED|FAILED|SKIPPED)", line)
    if match:
        print(f"  -> MATCHED: {match.group(1)} {match.group(2)}")
        test_path = match.group(1)
        status = match.group(2).lower()

        parts = test_path.split("::")
        file_path = parts[0]
        test_name = "::".join(parts[1:])

        tests.append({
            "id": f"test_{len(tests)}",
            "name": test_name,
            "status": status,
            "file": file_path,
            "duration": 0,
        })

        summary["total"] += 1
        if status == "passed":
            summary["passed"] += 1
        elif status == "failed":
            summary["failed"] += 1
        elif status == "skipped":
            summary["skipped"] += 1
    elif re.search(r"\d+\s+(passed|failed|skipped)", line) and "in" in line:
        print(f"  -> SUMMARY LINE")
        passed_match = re.search(r"(\d+)\s+passed", line)
        failed_match = re.search(r"(\d+)\s+failed", line)
        skipped_match = re.search(r"(\d+)\s+skipped", line)
        time_match = re.search(r"(\d+\.?\d*)\s*s", line)

        if passed_match:
            summary["passed"] = int(passed_match.group(1))
        if failed_match:
            summary["failed"] = int(failed_match.group(1))
        if skipped_match:
            summary["skipped"] = int(skipped_match.group(1))
        if time_match:
            summary["duration"] = float(time_match.group(1))

print("\nFinal results:")
print(json.dumps({"tests": tests, "summary": summary}, indent=2))
