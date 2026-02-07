"""
Test validation endpoint error
"""
import requests
import json
from pathlib import Path
import sys


def test():
    url = "http://127.0.0.1:8000/api/inspection/validate"
    payload = {
        "path": "d:/playground/argos",
        "language": "python",
        "validator": "black",
        "target": "d:/playground/argos/scout/scout/cli.py",
        "fix": True
    }

    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Sending to: {url}")

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test()
