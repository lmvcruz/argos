"""
Direct test of validation endpoint via HTTP
"""
import requests
import json
from pathlib import Path
import subprocess
import time
import sys


def test_validation():
    """Test validation endpoint via HTTP"""
    # Start server
    print("Starting server...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "lens.backend.server:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd="d:/playground/argos/lens",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(4)

    try:
        # Test file
        test_file = Path("d:/playground/argos/scout/scout/cli.py").resolve()

        print(f"\nTesting validation on: {test_file}")
        print(f"File exists: {test_file.exists()}")

        # Make request
        url = "http://127.0.0.1:8000/api/inspection/validate"
        payload = {
            "path": str(test_file),
            "language": "python",
            "validator": "black",
            "target": str(test_file),
            "fix": False
        }

        print(f"\nSending request to {url}")
        response = requests.post(url, json=payload, timeout=10)

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n=== API RESPONSE ===")
            print(f"Response keys: {result.keys()}")

            if 'results' in result and result['results']:
                print(f"Number of results: {len(result['results'])}")
                first_result = result['results'][0]
                print(f"First result keys: {first_result.keys()}")
                print(
                    f"First result (truncated): {str(first_result)[:200]}...")

                if 'diff' in first_result:
                    print(f"\n✅ SUCCESS: Diff field present!")
                    diff = first_result['diff']
                    print(f"Diff length: {len(diff) if diff else 0} chars")
                    if diff:
                        print(f"Diff preview:\n{diff[:500]}...")
                else:
                    print(f"\n❌ ERROR: Diff field NOT in response!")
                    print(f"Available keys: {list(first_result.keys())}")
        else:
            print(f"Response text: {response.text}")

    finally:
        print("\nShutting down server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)


if __name__ == "__main__":
    test_validation()
