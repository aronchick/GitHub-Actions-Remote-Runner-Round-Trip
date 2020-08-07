import requests
import sys

from requests.api import head

GITHUB_TOKEN = sys.argv[1]
TAG = sys.argv[2]

print("i'm working really hard on the runner")

url = "https://api.github.com/repos/aronchick/gha-arm-experiment/dispatches"
return_headers = {
    "Authorization": "token {}".format(GITHUB_TOKEN),
    "Accept": "application/vnd.github.everest-preview+json",
}
data_body = {'event_type': 'runner_finished', 'tag': '{}'.format(TAG)}
requests.post(url, data=data_body, headers=return_headers)
