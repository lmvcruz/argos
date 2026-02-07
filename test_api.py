"""Test the validation API endpoint to verify diffs are returned."""

import json
import requests
import time
from pathlib import Path

# Get absolute path to scout/scout/cli.py
test_file = Path(__file__).parent / "scout" / "scout" / "cli.py"

# Wait a moment for server to start
time.sleep(1)

try:
    response = requests.post(
        "http://localhost:8000/api/inspection/validate",
        json={
            "path": str(test_file),
            "language": "python",
            "validator": "black",
            "target": str(test_file)
        },
        timeout=10
    )

    print("=== API RESPONSE ===")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nResponse keys: {data.keys()}")

        if "results" in data:
            results = data["results"]
            print(f"\nNumber of results: {len(results)}")

            if results:
                first = results[0]
                print(f"\nFirst result:")
                print(f"  file: {first.get('file')}")
                print(f"  validator: {first.get('validator')}")
                print(f"  has diff: {'diff' in first}")

                if "diff" in first:
                    diff = first["diff"]
                    print(f"  diff length: {len(diff)} chars")
                    print(f"\n  diff preview:\n{diff[:300]}")
                else:
                    print(f"  Keys in result: {first.keys()}")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Error: {e}")
