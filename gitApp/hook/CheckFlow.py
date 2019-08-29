import json
import requests
import mongoengine as me
import imp
import os

from hook.helper import pretty_request, initialStatus, codeStatus
from hook.Authenticator import Authenticator
from checks.Repository import Repository
from model.Config import Config

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
    PEM = "kruegenertest.2019-08-21.private-key.pem"
    DB = "database.config"
    # TODO: CHANGE TO AUTOPAS
    AUTOPAS = "../AutoPas"
    THREADS = 4

    def __init__(self):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID)
        self.baseUrl = ""
        self.branch = ""
        self.baseSHA = ""
        self.base = ""

        self.SHAUrls = {}

        # Initiate DB connection with settings from file
        dbPath = CheckFlow.DB
        import os
        print(os.getcwd())
        try:
            db = imp.load_source('db', dbPath)
        except Exception as e:
            print(e)
            print("database.config MISSING. Create file based on: database.config.example")
            exit(-1)

        # Connect to MongoDB
        print("DB settings: ", db.collection, db.user, db.server)  # , db.password)
        me.connect(db.collection, username=db.user, password=db.password, host=("mongodb://" + db.server))

        # Initiate Repo
        self.repo = Repository(CheckFlow.AUTOPAS)

    def receiveHook(self, request):  # WSGIRequest):
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
        self.base = pull["base"]["ref"]
        self.baseSHA = pull["base"]["sha"]
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
        # Adding Base SHA of Pull Request to list
        shas.append(self.baseSHA)
        for c in cis:
            shas.append(c["sha"])
        for sha in shas:
            # CHECKING IF ALREADY TESTED and order by newest
            shaConfigs = Config.objects(commitSHA=sha).order_by('-id')
            if shaConfigs.count() == 0:
                print("NEW COMMIT", sha)
                self._createCheck(sha)
            else:
                print("Available Tests for SHA", shaConfigs.count())
                print("COMMIT ALREADY TESTED", sha)
                shas.remove(sha)
                continue
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
            # TODO: Where does the directory change mistake happen?
            cwd = os.getcwd()
            os.environ["OMP_NUM_THREADS"] = str(CheckFlow.THREADS)
            # TODO: _IMPORTANT: Think about replicating that work flow here and actually make
            #  build / measure / upload their own check runs in the suite or via updateStatus
            codes, headers, messages = self.repo.testSHA(sha)
            # TODO: CHANGE BACK TO FULL SHA TEST
            # ONLY FOR DEBUGGING
            # codes, headers, messages = [0, 0, 0], ["test1", "test2", "test3"], ["test1", "test2", "test3"]

            os.chdir(cwd)
            print("CODES", codes, messages)
            r = requests.patch(
                url=self.SHAUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus(codes, headers, messages))
            pretty_request(r)
        except Exception as e:
            print(e)
            print(f"TestSHA {sha} failed with exit")
            r = requests.patch(
                url=self.SHAUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus([-1], "GENERAL", ["exit() statement called"]))
            pretty_request(r)
            return False

        if -1 in codes:
            print(f"TestSHA {sha} failed with code -1")
        else:
            print(f"TestSHA {sha} passed")