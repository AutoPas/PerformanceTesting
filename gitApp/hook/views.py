from django.shortcuts import render
from django.views.generic.base import View
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import jwt
from cryptography.hazmat.backends import default_backend
import time

def pretty_request(request):

    for k, v in request.headers.items():
        print(k,v)

    try:
        body = request.body.decode("utf-8")
    except:
        body = request.text
        print(request.url)
    jsonBody = json.loads(body)
    print(json.dumps(jsonBody, indent=4, sort_keys=True))

# Create your views here.
@csrf_exempt
def base(request):

    pretty_request(request)

    response_text = "Hey There"
    return HttpResponse(response_text)

@csrf_exempt
def receiveHook(request):

    pretty_request(request)

    print("hook called")
    return HttpResponse("200")

def newJWT(cert_bytes):
    print("CERT", cert_bytes)
    private_key = default_backend().load_pem_private_key(cert_bytes, None)
    now = int(time.time())
    payload = {
        # issued at
        "iat": now,
        # expiry
        "exp": now + (5 * 60),
        # issuer (git app id)
        "iss": 39178
    }
    jwt_key = jwt.encode(payload, private_key, algorithm="RS256")
    print("JWT ENCODED", jwt_key)
    print(jwt.decode(jwt_key, private_key, verify=False, algorithms=["RS256"]))
    return jwt_key

def createCheck():

    # TODO: get install ID on install webhook automatically
    INSTALL_ID = 1600235
    APP_URL = "https://api.github.com/app"

    user = "kruegener"
    token = "4efef70cab3f5941eab32a598178c7e2783db9e9"

    cert_bytes = open("../kruegenertest.2019-08-21.private-key.pem", "r").read().encode()

    jwt_key = newJWT(cert_bytes)

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
        "head_sha": "908c945eede1a3798efe5e48624e589cbf6baa1d",
    }
    CHECK_RUN_URL = "https://api.github.com/repos/kruegener/PushTest/check-runs"
    r = requests.post(url=CHECK_RUN_URL, headers=token_headers, json=params)
    pretty_request(r)
    check_run_id_url = json.loads(r.text)["url"]
    print(check_run_id_url)

    # Update Status
    params = {
        "status": "in_progress",
        "output": {
            "title": "Test X",
            "summary": "something happened",
            "text": "Look, more details for this commit",
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
    createCheck()