import json
import requests
from mongoDocuments.Results import Results


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


def codeStatus(codes, header, messages, images=[]):

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

    img_params = []
    for i in images:
        img_params.append({'image_url': i, 'alt': i})

    params = {
        # "status": "in_progress",
        "conclusion": conclusion,
        "output": {
            "title": "Results",
            "summary": "It's over",
            "text": f"# Summary\n{text}",
            "images": img_params
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
    try:
        s = str(out, "utf-8")
        vprint(s)
    except Exception as e:
        s = f'ERROR CONVERTING SYS OUT:\n{e}\n{out}'
        print('output conversion failed', e, out)
    return s


def get_dyn_keys(res: Results):
    out = ''
    all_attr = res.__dict__
    keys = all_attr['_fields_ordered']
    for k in keys:
        if 'dynamic_' in k:
            out += k.replace('dynamic_', '') + ": "
            out += str(all_attr[k]) + ' '
    out.rstrip(' ')
    return out


def _getServiceAccountToken():
    """
    Loads service account auth token
    :return: token
    """
    token = 'token'
    authHeader = {
        "Authorization": f"Bearer {token}"
    }
    return authHeader


def _checkIfAlreadyRunning():
    """
    Check if there is already a running worker pod
    :return: bool
    """
    r = requests.get(url='https://pproc-be.sccs.in.tum.de:8443/api/v1/namespaces/ls1autopasjenkins/pods',
                     headers=_getServiceAccountToken(),
                     verify=False  # Not checking SSL Cert valid
                     )
    pretty_request(r)
    for i in r.json()['items']:

        try:
            podType = i['metadata']['labels']['type']
            if podType == 'perfrunner':
                status = i['status']['phase']
                if status == 'Pending':
                    return True  # Do not schedule a new pod
                elif status == 'Running':
                    return True  # Do not schedule a new pod

        except KeyError:
            continue

    return False  # if no pod with label perfrunner and status running or pending was found


def _spawnNewWorker():
    """
    Spawn a new Worker pod
    :return:
    """
    image = 'ls1autopasjenkins/performancetesting'
    cpu = 13

    params = \
        {
            "kind": "Pod",
            "apiVersion": "v1",
            "metadata": {
                "generateName": "api-test-pod",
                "labels": {
                    "type": "perfrunner"
                }
            },
            "spec": {
                "containers": [{
                    "name": "perfpod",
                    "image": f"docker-registry.default.svc:5000/{image}",
                    "resources": {
                        "requests": {
                            "cpu": cpu
                        },
                        "limits": {
                            "cpu": cpu
                        }
                    },
                    "env": [
                        {
                            "name": "GITHUBAPPID",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "autopas-performance-tester-github-app-id",
                                    "key": "GITHUBAPPID"
                                }
                            }
                        },
                        {
                            "name": "IMGURCLIENTID",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "autopas-performance-tester-imgur-client-id",
                                    "key": "IMGURCLIENTID"
                                }
                            }
                        }]
                }],
                "nodeSelector": {
                    "node-role.kubernetes.io/compute": "true"
                },
                "affinity": {
                    "nodeAffinity": {
                        "requiredDuringSchedulingIgnoredDuringExecution": {
                            "nodeSelectorTerms": [{
                                "matchExpressions": [{
                                    "key": "kubernetes.io/hostname",
                                    "operator": "NotIn",
                                    "values": [
                                        "pproc-nvd.sccs.cluster"
                                    ]
                                }]
                            }]
                        }
                    }
                },
                "restartPolicy": "Never",
                "serviceAccount": "ls1jenkins",
                "schedulerName": "default-scheduler"
            }
        }

    r = requests.post(url='https://pproc-be.sccs.in.tum.de:8443/api/v1/namespaces/ls1autopasjenkins/pods',
                      headers=_getServiceAccountToken(),
                      json=params,
                      verify=False)
    pretty_request(r)
    return r.status_code


def spawnWorker():
    """OpenShift API call to start a worker pod"""

    if not _checkIfAlreadyRunning():
        code = _spawnNewWorker()
        print(f'\n\nSPAWNING WORKER: {code}')
    else:
        print('\nNo new Worker needed\n')


if __name__ == '__main__':
    spawnWorker()
