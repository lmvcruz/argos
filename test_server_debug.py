"""
Test that captures server output for debugging
"""
import requests
import json
from pathlib import Path
import subprocess
import time
import sys


def test_validation():
    """Test validation endpoint via HTTP and capture server output"""
    # Start server, capturing output
    print("Starting server with output capture...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "lens.backend.server:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd="d:/playground/argos/lens",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    # Wait for server to start
    print("Waiting for server startup...")
    time.sleep(4)

    try:
        # Test file
        test_file = Path("d:/playground/argos/scout/scout/cli.py").resolve()

        print(f"Testing validation on: {test_file}")

        # Make request
        url = "http://127.0.0.1:8000/api/inspection/validate"
        payload = {
            "path": str(test_file),
            "language": "python",
            "validator": "black",
            "target": str(test_file),
            "fix": False
        }

        print(f"Sending request...")
        response = requests.post(url, json=payload, timeout=10)

        # Give time for logs to appear
        time.sleep(1)

        print(f"\n=== SERVER OUTPUT ===")
        try:
            # Try to read server output without blocking
            import select
            while True:
                line = server_proc.stdout.readline()
                if not line:
                    break
                print(line.rstrip())
        except:
            pass

        print(f"\n=== API RESPONSE ===")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if 'results' in result and result['results']:
                first_result = result['results'][0]
                print(f"Result keys: {first_result.keys()}")
                if 'diff' in first_result:
                    print("✅ Diff field IS present!")
                else:
                    print("❌ Diff field NOT present")

    finally:
        print("Shutting down server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except:
            server_proc.kill()


if __name__ == "__main__":
    test_validation()
