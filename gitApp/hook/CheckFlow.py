import json
import requests
import mongoengine as me
import imp

from hook.helper import pretty_request, initialStatus, codeStatus
from hook.Authenticator import Authenticator
from checks.Repository import Repository

"""
Codes:
    -1: failed
    0: neutral
    1: success
"""

class CheckFlow:

    GIT_APP_ID = 39178
    # TODO: Remove if not needed for debugging anymore
    INSTALL_ID = 1600235
    # TODO: Add to config file
    PEM = "gitApp/kruegenertest.2019-08-21.private-key.pem"
    DB = "gitApp/database.config"
    # TODO: CHANGE TO AUTOPAS
    AUTOPAS = "../PushTest"

    def __init__(self):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID)
        self.baseUrl = ""
        self.branch = ""
        self.SHAUrls = {}

        # Initiate DB connection with settings from file
        dbPath = CheckFlow.DB
        try:
            db = imp.load_source('db', dbPath)
        except:
            print("database.config MISSING. Create file based on: database.config.example")
            exit(-1)

        # Connect to MongoDB
        print("DB settings: ", db.collection, db.user, db.server)  # , db.password)
        me.connect(db.collection, username=db.user, password=db.password, host=("mongodb://" + db.server))

        # Initiate Repo
        self.repo = Repository(CheckFlow.AUTOPAS)

    def receiveHook(self, request):# WSGIRequest):
        """ on receive of pull_request event """

        print("RUNNING CHECKS")
        body = json.loads(request.body)
        # Update Repo installation ID for Github App auth
        self.auth.updateInstallID(int(body["installation"]["id"]))

        # Base url for all API request for this repo
        self.baseUrl = body["repository"]["url"]
        pull = body["pull_request"]

        # Get URL for commits list
        ci_url = pull["commits_url"]

        # Checkout branch associated with pull request
        self.branch = pull["head"]["ref"]
        self.repo.checkoutBranch(self.branch)
        print(ci_url)

        # Run checks on commits url
        self._checkCommits(ci_url)

    def _checkCommits(self, url):
        """
        Gets list of pull request commits and runs checks
        """
        r = requests.get(url=url, headers=self.auth.getTokenHeader())
        pretty_request(r)
        print("COMMIT LIST:")
        cis = r.json()
        shas = []
        for c in cis:
            shas.append(c["sha"])
        for sha in shas:
            print("NEW COMMIT", sha)
            self._createCheck(sha)
        for sha in shas:
            print("TESTING COMMIT", sha)
            self._runCheck(sha)


    def _createCheck(self, sha):

        # Run API request with install token as auth
        params = {
            "name": "Auto Check",
            "head_sha": sha,
        }
        CHECK_RUN_URL = f"{self.baseUrl}/check-runs"
        r = requests.post(url=CHECK_RUN_URL, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)
        response = r.json()
        check_run_id_url = response["url"]

        print(check_run_id_url)

        self.SHAUrls[sha] = check_run_id_url

    def _runCheck(self, sha):

        # RUN CHECK
        print(f"RUNNING CHECKS ON {sha}")

        # Update Status to in Progress
        r = requests.patch(url=self.SHAUrls[sha], headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            codes, messages = self.repo.testSHA(sha)
            print("CODES", codes, messages)
            r = requests.patch(
                url=self.SHAUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus(codes, messages))
        except:
            print(f"TestSHA {sha} failed with exit")
            return False

        if -1 in codes:
            print(f"TestSHA {sha} failed with code -1")
        else:
            print(f"TestSHA {sha} passed")


if __name__ == '__main__':
    run = CheckFlow()
    run._createCheck()