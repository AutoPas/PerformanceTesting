import json
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


def newJWT(cert_bytes, GIT_APP_ID):
    print("CERT", cert_bytes)
    private_key = default_backend().load_pem_private_key(cert_bytes, None)
    now = int(time.time())
    payload = {
        # issued at
        "iat": now,
        # expiry
        "exp": now + (9 * 60),
        # issuer (git app id)
        "iss": GIT_APP_ID
    }
    jwt_key = jwt.encode(payload, private_key, algorithm="RS256")
    print("JWT ENCODED", jwt_key)
    print(jwt.decode(jwt_key, private_key, verify=False, algorithms=["RS256"]))
    return jwt_key
