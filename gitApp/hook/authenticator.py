import json
import time
import dateutil.parser
import jwt
import requests
from cryptography.hazmat.backends import default_backend
from .helper import *

class Authenticator:

    # Expiry Thresholds in minutes
    INSTALL_EXP_THRESHOLD = 2
    JWT_EXP_THRESHOLD = 2

    def __init__(self, pem, git_app_id, install_id):
        self.pem = pem
        self.app_id = git_app_id
        self.install_id = install_id
        self.jwt_expiry = -1
        self.jwt_token = None
        self.install_expiry = -1
        self.install_token = None

    def getToken(self):
        """ Check expiry date of existing install token and create new one if needed, returns valid token."""
        self._checkInstallToken()
        return self.install_token

    def getTokenHeader(self):
        """ Returns fully formed header with valid installation token """
        self.getToken()
        token_headers = {
            "Accept": "application/vnd.github.antiope-preview+json, "
                      "application/vnd.github.machine-man-preview+json, "
                      "application/vnd.github.v3+json",
            "Authorization": "token {}".format(self.install_token),
        }
        return token_headers

    def _checkJWT(self):
        """
        Checks if the passed JWT is still current and either returns the old one or creates and returns a new one
        """

        now = time.time()
        if self.jwt_expiry < (now - (Authenticator.JWT_EXP_THRESHOLD * 60)):
            vprint("JWT expired")
            self._newJWT()
        else:
            vprint("JWT still valid")

    def _newJWT(self):
        """
        Creates new JWT for authentication based on private key and GIT APP ID
        """
        cert_bytes = open(f"{self.pem}", "r").read().encode()
        print("CERT", cert_bytes)
        private_key = default_backend().load_pem_private_key(cert_bytes, None)
        now = int(time.time())
        new_expiry = now + (9 * 60)
        payload = {
            # issued at
            "iat": now,
            # expiry
            "exp": new_expiry,
            # issuer (git app id)
            "iss": self.app_id
        }
        jwt_key = jwt.encode(payload, private_key, algorithm="RS256")
        print("JWT ENCODED", jwt_key)
        print(jwt.decode(jwt_key, private_key, verify=False, algorithms=["RS256"]))
        self.jwt_token = jwt_key
        self.jwt_expiry = new_expiry

    def _checkInstallToken(self):
        """
        Checks Install token for expiry date and creates new one if necessary
        """
        now = int(time.time())
        if self.install_expiry < (now - Authenticator.INSTALL_EXP_THRESHOLD * 60):
            vprint(f"INSTALL TOKEN expired {self.install_expiry} {now} {(now - Authenticator.INSTALL_EXP_THRESHOLD * 60)}")
            self._newInstallToken()
        else:
            vprint("INSTALL TOKEN valid")

    def _newInstallToken(self):
        self._checkJWT()
        jwt_headers = {
            "Accept": "application/vnd.github.antiope-preview+json, "
                      "application/vnd.github.machine-man-preview+json, "
                      "application/vnd.github.v3+json",
            "Authorization": "Bearer {}".format(self.jwt_token.decode()),
        }
        print(jwt_headers)

        # Get Installation Token
        INSTALLATION_URL = f"https://api.github.com/app/installations/{self.install_id}/access_tokens"
        r = requests.post(url=INSTALLATION_URL, headers=jwt_headers)
        print(r.url)
        # response
        pretty_request(r)
        parsed = json.loads(r.text)
        self.install_token = parsed["token"]
        self.install_expiry = int(dateutil.parser.parse((parsed["expires_at"])).timestamp())
        print(self.install_token)
        print(self.install_expiry)
