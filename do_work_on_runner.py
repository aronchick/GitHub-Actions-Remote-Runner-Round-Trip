import requests
import sys
import requests
from requests.api import head

GITHUB_TOKEN = None
TAG = None

if len(sys.argv) >= 2:
    GITHUB_TOKEN = sys.argv[1]
    TAG = sys.argv[2]

print("i'm working really hard on the runner")

url = "https://api.github.com/repos/aronchick/gha-arm-experiment/dispatches"
gh_token = "token " + GITHUB_TOKEN
return_headers = {"Authorization": gh_token,"Accept": "application/vnd.github.everest-preview+json", "Content-Type": "application/json"}
data_body = '{"event_type": "runner_finished", "client_payload": {"tag": "'+ TAG +'"} }'

res = requests.post(url, data=data_body, headers=return_headers)
print(res)