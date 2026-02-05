#!/usr/bin/env python3
"""
Test the /api/verdict/execute endpoint
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

# Test with the anvil tests directory
project_path = "d:\\playground\\argos\\anvil\\tests"

payload = {
    "projectPath": project_path
}

print(f"Sending request to {BASE_URL}/api/verdict/execute")
print(f"Project path: {project_path}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(
        f"{BASE_URL}/api/verdict/execute",
        json=payload,
        timeout=60
    )

    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("Test Execution Results:")
        print(json.dumps(data, indent=2))
    else:
        print(f"Error response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
