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

# curl -v POST -H "Accept: application/vnd.github.everest-preview+json"
# -H "Authorization: token adf0e2f0ecce527264796019dd98c5b8918c9c2f" -H "Content-Type: application/json"
# --data '{"event_type":"runner_finished"}' https://api.github.com/repos/aronchick/gha-arm-experiment/dispatches

url = "https://api.github.com/repos/aronchick/gha-arm-experiment/dispatches"
return_headers = {"Authorization": f"token {GITHUB_TOKEN}","Accept": "application/vnd.github.everest-preview+json", "Content-Type": "application/json"}
data_body = '{"event_type": "runner_finished", "client_payload": {"tag": "'+ TAG +'"} }'

res = requests.post(url, data=data_body, headers=return_headers)
print(res)