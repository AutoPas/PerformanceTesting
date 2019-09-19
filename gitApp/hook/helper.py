import json

VERBOSE = True


def vprint(message):
    if VERBOSE:
        print(message)


def pretty_request(request):

    if not VERBOSE:
        return

    for k, v in request.headers.items():
        print(k, v)

    try:
        body = request.body.decode("utf-8")
    except Exception as e:
        vprint(e)
        body = request.text
        print(request.url)
    try:
        jsonBody = json.loads(body)
        print(json.dumps(jsonBody, indent=4, sort_keys=True))
    except:
        print(request)


def initialStatus():
    params = {
        "status": "in_progress",
        "output": {
            "title": "Test Suite",
            "summary": "Working on it",
            "text": "Waiting for results ...\n",
        }
    }
    return params


def codeStatus(codes, header, messages):

    text = ""

    # TODO: Save Full messages in database and serve on web page

    for i, code in enumerate(codes):
        text += f"\n## {header[i]}\n"
        if code == -1:
            text += "\n```diff\n- FAILURE:\n```\n"
            text += "...\n" + messages[i][-5000:]
        elif code == 0:
            text += "\n```diff\nNEUTRAL:\n```\n"
            text += "...\n" + messages[i][-500:]
        else:
            text += "\n```diff\n+ SUCCESS:\n```\n"
            text += "...\n" + messages[i][-500:]

    if -1 in codes:
        conclusion = "failure"
    elif 0 in codes:
        conclusion = "neutral"
    else:
        conclusion = "success"

    params = {
        # "status": "in_progress",
        "conclusion": conclusion,
        "output": {
            "title": "Results",
            "summary": "It's over",
            "text": f"# Summary\n{text}",
            "images": [
                {
                    "alt": "test image",
                    "image_url": "https://bit.ly/2ZlkScy"
                }
            ]
        }
    }
    return params

def speedupStatus(codes, header, messages, images):

    text = ""

    # TODO: Save Full messages and images in database and serve on web page

    for i, code in enumerate(codes):
        text += f"\n## {header[i]}\n"
        if code == -1:
            text += "\n```diff\n- FAILURE:\n```\n"
            text += "...\n" + messages[i][-5000:]
        elif code == 0:
            text += "\n```diff\nNEUTRAL:\n```\n"
            text += "...\n" + messages[i][-500:]
        else:
            text += "\n```diff\n+ SUCCESS:\n```\n"
            text += "...\n" + messages[i][-500:]

    if -1 in codes:
        conclusion = "failure"
    elif 0 in codes:
        conclusion = "neutral"
    else:
        conclusion = "success"

    params = {
        # "status": "in_progress",
        "conclusion": conclusion,
        "output": {
            "title": "Results",
            "summary": "It's over",
            "text": f"# Summary\n{text}",
            "images": [
                {
                    "alt": "test image",
                    "image_url": "https://bit.ly/2ZlkScy"
                }
            ]
        }
    }
    return params


def convertOutput(out):
    s = str(out, "utf-8")
    vprint(s)
    return s
