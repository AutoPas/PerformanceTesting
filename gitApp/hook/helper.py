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


def codeStatus(codes, messages):

    text = ""

    # TODO: Save Full messages in database and serve on web page

    for i, code in enumerate(codes):
        if code == -1:
            text += "\n```diff\n- FAILURE:\n```\n"
            text += messages[i][-5000:]
        elif code == 0:
            text += "\n```diff\nNEUTRAL:\n```\n"
            text += messages[i][-500:]
        else:
            text += "\n```diff\n+ SUCCESS:\n```\n"
            text += messages[i][-500:]

    if -1 in codes:
        conclusion = "failure"
    elif 0 in codes:
        conclusion = "neutral"
    else:
        conclusion = "success"

    params = {
        #"status": "in_progress",
        "conclusion": conclusion,
        "output": {
            "title": "Test X",
            "summary": "It's over",
            "text": f"Summary\n{text}",
            "images": [
                {
                    "alt": "test image",
                    "image_url": "https://image.shutterstock.com/image-vector/example-sign-paper-origami-speech-260nw-1164503347.jpg"
                }
            ]
        }
    }
    return params