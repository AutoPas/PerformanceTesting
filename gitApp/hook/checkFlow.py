from gitApp.hook.helper import pretty_request, newJWT
import json
import requests

class CheckFlow:

    GIT_APP_ID = 39178

    def __init__(self):
        print("new checkFlow instance")

    def createCheck(self):
        # TODO: get install ID on install webhook automatically
        INSTALL_ID = 1600235
        APP_URL = "https://api.github.com/app"

        user = "kruegener"
        token = "4efef70cab3f5941eab32a598178c7e2783db9e9"

        cert_bytes = open("../kruegenertest.2019-08-21.private-key.pem", "r").read().encode()

        jwt_key = newJWT(cert_bytes, self.GIT_APP_ID)

        jwt_headers = {
            "Accept": "application/vnd.github.antiope-preview+json, "
                      "application/vnd.github.machine-man-preview+json, "
                      "application/vnd.github.v3+json",
            "Authorization": "Bearer {}".format(jwt_key.decode()),
        }
        print(jwt_headers)

        # Get Installation Token
        INSTALLATION_URL = f"https://api.github.com/app/installations/{INSTALL_ID}/access_tokens"
        r = requests.post(url=INSTALLATION_URL, headers=jwt_headers)
        print(r.url)
        # response
        pretty_request(r)
        install_token = json.loads(r.text)["token"]
        print(install_token)

        # Run API request with install token as auth
        token_headers = {
            "Accept": "application/vnd.github.antiope-preview+json, "
                      "application/vnd.github.machine-man-preview+json, "
                      "application/vnd.github.v3+json",
            "Authorization": "token {}".format(install_token),
        }
        params = {
            "name": "Second Check",
            "head_sha": "80b38c41e081a492a9d5fe3de6683ae34bce8b24",
        }
        CHECK_RUN_URL = "https://api.github.com/repos/kruegener/PushTest/check-runs"
        r = requests.post(url=CHECK_RUN_URL, headers=token_headers, json=params)
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
        r = requests.patch(url=check_run_id_url, headers=token_headers, json=params)
        pretty_request(r)


if __name__ == '__main__':
    run = CheckFlow()
    run.createCheck()