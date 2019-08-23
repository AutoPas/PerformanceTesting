from gitApp.hook.helper import pretty_request
import json
import requests
from gitApp.hook.authenticator import Authenticator

class CheckFlow:

    GIT_APP_ID = 39178
    INSTALL_ID = 1600235
    PEM = "kruegenertest.2019-08-21.private-key.pem"

    def __init__(self):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID, CheckFlow.INSTALL_ID)

    def receiveHook(self, request):

        pass

    def createCheck(self):

        # TODO: get install ID on install webhook automatically

        self.auth.getTokenHeader()

        # Run API request with install token as auth
        params = {
            "name": "Second Check",
            "head_sha": "80b38c41e081a492a9d5fe3de6683ae34bce8b24",
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
                        "",
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
    run.createCheck()