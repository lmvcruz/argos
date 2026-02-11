"""Test async test discovery endpoints."""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_async_discovery():
    """Test the async test discovery flow."""

    # Start discovery
    print("1. Starting test discovery...")
    response = requests.post(
        f"{BASE_URL}/api/tests/discover/start",
        json={"path": "d:\\playground\\argos\\anvil"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to start discovery: {response.status_code}")
        print(response.text)
        return False

    data = response.json()
    task_id = data.get("task_id")
    print(f"✓ Discovery started, task_id: {task_id}")

    # Poll for results
    print("\n2. Polling for results (every 2s)...")
    max_attempts = 30  # 60 seconds max

    for i in range(max_attempts):
        time.sleep(2)

        response = requests.get(f"{BASE_URL}/api/tests/discover/status/{task_id}")

        if response.status_code != 200:
            print(f"❌ Failed to get status: {response.status_code}")
            return False

        data = response.json()
        status = data.get("status")

        print(f"  Attempt {i+1}: status = {status}")

        if status == "completed":
            result = data.get("result", {})
            print(f"\n✓ Discovery completed!")
            print(f"  - Suites: {result.get('total_suites', 0)}")
            print(f"  - Tests: {result.get('total_tests', 0)}")

            # Show first few suites
            suites = result.get('suites', [])
            if suites:
                print(f"\n  First 3 suites:")
                for suite in suites[:3]:
                    print(f"    - {suite.get('name')}: {len(suite.get('tests', []))} tests")

            return True

        elif status == "failed":
            error = data.get("error")
            print(f"\n❌ Discovery failed: {error}")
            return False

    print(f"\n❌ Timeout after {max_attempts * 2} seconds")
    return False

if __name__ == "__main__":
    print("Testing async test discovery endpoints...\n")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("❌ Backend not responding")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Backend not running at http://localhost:8000")
        print("   Please start the backend first.")
        sys.exit(1)

    success = test_async_discovery()

    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)
