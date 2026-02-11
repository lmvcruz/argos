import requests
import json
import time

# Test active project
response = requests.get('http://localhost:8000/api/projects/active').json()
active = response['active_project']
print(f'Active Project: {active["name"]} at {active["local_folder"]}')

# Test files endpoint
files_resp = requests.get(
    f'http://localhost:8000/api/inspection/files?path={active["local_folder"]}').json()
print(f'\nFiles count: {len(files_resp["files"])}')
print('First 5 files:')
for f in files_resp["files"][:5]:
    print(f'  - {f["name"]} ({f["type"]})')

# Test discovery on anvil specifically
anvil_path = 'd:\\playground\\argos\\anvil'
print(f'\n===Testing test discovery on anvil===')
start = time.time()
tests_resp = requests.get(
    f'http://localhost:8000/api/tests/discover?path={anvil_path}', timeout=180).json()
elapsed = time.time() - start
print(f'Time: {elapsed:.1f}s')
print(f'Test Suites: {tests_resp["total_suites"]}')
print(f'Test Cases: {tests_resp["total_tests"]}')
if tests_resp["suites"]:
    print('First 3 suites:')
    for suite in tests_resp["suites"][:3]:
        print(f'  - {suite["name"]}: {len(suite["tests"])} tests')
