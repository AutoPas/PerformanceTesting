import json
import requests
import mongoengine

from hook.helper import pretty_request
from hook.authenticator import Authenticator


class CheckFlow:

    GIT_APP_ID = 39178
    # TODO: get install ID on webhook automatically / create setup file for rest
    INSTALL_ID = 1600235
    PEM = "kruegenertest.2019-08-21.private-key.pem"
    # TODO: Get them from url during installation
    OWNER = "KRUEGENER"
    REPO = "PushTest"

    def __init__(self):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID, CheckFlow.INSTALL_ID)
        self.repo = CheckFlow.REPO
        self.owner = CheckFlow.OWNER

    def receiveHook(self, request):# WSGIRequest):
        print("RUNNING CHECKS")
        body = json.loads(request.body)
        pull = body["pull_request"]
        installation = body["installation"]
        print(pull["commits_url"])
        self._getCommits(pull["commits_url"])

    def _getCommits(self, url):
        r = requests.get(url=url, headers=self.auth.getTokenHeader())
        pretty_request(r)
        print("COMMIT LIST:")
        cis = r.json()
        for c in cis:
            sha = c["sha"]
            print("NEW COMMIT", sha, c["commit"]["message"])
            self._createCheck(sha)

    def _createCheck(self, sha):

        # Run API request with install token as auth
        params = {
            "name": "Auto Check",
            "head_sha": sha,
        }
        CHECK_RUN_URL = "https://api.github.com/repos/kruegener/PushTest/check-runs"
        r = requests.post(url=CHECK_RUN_URL, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)
        check_run_id_url = json.loads(r.text)["url"]
        print(check_run_id_url)

        # Update Status
        params = {
            "status": "in_progress",
            # "conclusion": "success",
            "output": {
                "title": "Test X",
                "summary": "something happened",
                "text": "Look, more details for this commit\n"
                        "aldfkjalsdjf"
                        "======"
                        "ff",
                "images": [
                    {
                        "alt": "test image",
                        "image_url": "https://image.shutterstock.com/image-vector/example-sign-paper-origami-speech-260nw-1164503347.jpg"
                    }
                ]
            }
        }
        r = requests.patch(url=check_run_id_url, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)


if __name__ == '__main__':
    run = CheckFlow()
    run._createCheck()