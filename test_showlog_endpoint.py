"""Test show-log endpoint."""
import requests
import json

# Test the show-log endpoint with a run that we know has logs
run_id = 21786230446

print(f"Testing show-log endpoint for run_id={run_id}")
print()

try:
    response = requests.get(f"http://localhost:8000/api/scout/show-log/{run_id}")
    print(f"Status code: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()

        print(f"Workflow: {data.get('workflow_name')}")
        print(f"Total jobs: {len(data.get('jobs', []))}")
        print()

        for job in data.get('jobs', [])[:3]:  # Show first 3 jobs
            print(f"Job: {job.get('job_name')} (ID: {job.get('job_id')})")
            print(f"  Status: {job.get('status')} / {job.get('conclusion')}")
            print(f"  Has raw log: {job.get('has_raw_log')}")
            raw_log = job.get('raw_log', '')
            if raw_log:
                print(f"  Raw log length: {len(raw_log)} characters")
                print(f"  First 200 chars: {raw_log[:200]}")
            else:
                print(f"  Raw log: EMPTY or NULL")
            print()
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Error making request: {e}")
