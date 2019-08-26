import json

VERBOSE = True


def vprint(message):
    if VERBOSE:
        print(message)


def pretty_request(request):

    if not VERBOSE:
        return

    for k, v in request.headers.items():
        print(k,v)

    try:
        body = request.body.decode("utf-8")
    except:
        body = request.text
        print(request.url)
    jsonBody = json.loads(body)
    print(json.dumps(jsonBody, indent=4, sort_keys=True))

def initialStatus():
    params = {
        "status": "in_progress",
        # "conclusion": "success",
        "output": {
            "title": "Test X",
            "summary": "Nothing happened yet",
            "text": "Look, more details for this commit\n",
            "images": [
                {
                    "alt": "test image",
                    "image_url": "https://image.shutterstock.com/image-vector/example-sign-paper-origami-speech-260nw-1164503347.jpg"
                }
            ]
        }
    }
    return params