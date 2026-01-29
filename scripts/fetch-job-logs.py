"""Fetch full job logs from GitHub Actions."""
import requests
import os
import sys

job_id = 61918157932  # Ubuntu 3.9 job

headers = {
    'Authorization': f'Bearer {os.environ["GITHUB_TOKEN"]}',
    'Accept': 'application/vnd.github+json'
}

resp = requests.get(f'https://api.github.com/repos/lmvcruz/argos/actions/jobs/{job_id}/logs', headers=headers)

if resp.status_code == 200:
    # Find DEBUG lines
    for line in resp.text.split('\n'):
        if 'DEBUG:' in line or 'test_ignores_symlinks_when_disabled' in line:
            print(line)
else:
    print(f"Error: {resp.status_code}")
    print(resp.text)
