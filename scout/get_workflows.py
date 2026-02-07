import os
import json
import urllib.request

token = os.getenv('GITHUB_TOKEN')
req = urllib.request.Request(
    'https://api.github.com/repos/lmvcruz/argos/actions/workflows',
    headers={'Authorization': f'token {token}'}
)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read())
    for w in data.get('workflows', []):
        print(f"{w['name']:40} {w['path']}")
