import json
import requests
import mongoengine as me
from pymongo import errors
import imp
import os
import numpy as np

from hook.helper import pretty_request, initialStatus, codeStatus, speedupStatus
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
    #GIT_APP_ID = 39178
    GIT_APP_ID = os.environ["GITHUBAPPID"]
    # TODO: Remove if not needed for debugging anymore
    INSTALL_ID = 1600235
    # TODO: Add to config file
    PEM = "private-key.pem"
    DB = "database.config"
    # TODO: CHANGE TO AUTOPAS
    AUTOPAS = "../../AutoPas"
    THREADS = 4

    def __init__(self):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID)
        self.baseUrl = ""
        self.branch = ""
        self.baseSHA = ""
        self.base = ""

        self.RunUrls = {}
        self.CompareUrls = {}

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
        # THIS ACTIVATES ALL CHECK RUNS
        self._checkCommits(ci_url)

    def _checkCommits(self, url):
        """
        Gets list of pull request commits and runs checks
        """
        r = requests.get(url=url, headers=self.auth.getTokenHeader())
        pretty_request(r)
        print("COMMIT LIST:")
        cis = r.json()
        SHAs = [self.baseSHA]
        # Adding Base SHA of Pull Request to list
        for c in cis:
            SHAs.append(c["sha"])
        for sha in SHAs:
            # CHECKING IF ALREADY TESTED and order by newest
            shaConfigs = Config.objects(commitSHA=sha).order_by('-id')
            if shaConfigs.count() == 0:
                print("NEW COMMIT", sha)
                self.RunUrls[sha] = self._createCheckRun(sha, "Performance Run")
                if sha is not self.baseSHA:
                    self.CompareUrls[sha] = self._createCheckRun(sha, "Performance Comparison")
            else:
                print("Available Tests for SHA", shaConfigs.count())
                print("COMMIT ALREADY TESTED", sha)
                continue
        for sha in self.RunUrls.keys():
            print("TESTING COMMIT", sha)
            self._runCheck(sha)
            if sha in self.CompareUrls.keys():
                self._comparePerformance(sha)

    def _createCheckRun(self, sha, name):

        # Run API request with install token as auth
        params = {
            "name": name,
            "head_sha": sha,
        }
        CHECK_RUN_URL = f"{self.baseUrl}/check-runs"
        r = requests.post(url=CHECK_RUN_URL, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)
        response = r.json()
        check_run_id_url = response["url"]
        print(check_run_id_url)
        return check_run_id_url

    def _runCheck(self, sha):

        # RUN CHECK
        print(f"RUNNING CHECKS ON {sha}")

        # Update Status to in Progress
        r = requests.patch(url=self.RunUrls[sha], headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            cwd = os.getcwd()
            os.environ["OMP_NUM_THREADS"] = str(CheckFlow.THREADS)
            print("Running Threads:", os.environ["OMP_NUM_THREADS"])
            # TODO: _IMPORTANT: Think about replicating that work flow here and actually make
            #  build / measure / upload their own check runs in the suite or via updateStatus
            codes, headers, messages = self.repo.testSHA(sha)
            # TODO: CHANGE BACK TO FULL SHA TEST

            os.chdir(cwd)
            print("CODES", codes, messages)
            r = requests.patch(
                url=self.RunUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus(codes, headers, messages))
            pretty_request(r)
        except Exception as e:
            print(e)
            print(f"TestSHA {sha} failed with exit")
            r = requests.patch(
                url=self.RunUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus([-1], ["GENERAL"], ["exit() statement called"]))
            pretty_request(r)
            return False

    def _comparePerformance(self, sha):

        assert (sha is not self.baseSHA)

        print(f"Comparing Performance for {sha}")
        # Update Status to in Progress
        r = requests.patch(url=self.CompareUrls[sha], headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            baseConfigs = Config.objects(commitSHA=self.baseSHA).order_by('-id')
            shaConfigs = Config.objects(commitSHA=sha).order_by('-id')
        except errors.ServerSelectionTimeoutError as e:
            print(e)
            r = requests.patch(
                url=self.CompareUrls[sha],
                headers=self.auth.getTokenHeader(),
                json=codeStatus([-1], ["QUERY DATABASE"],
                                [f"Couldn't query database. TimedOut {e}"]))
            pretty_request(r)
            return False

        # Type Hint for QuerySet
        cr: Config
        bcr: Config
        codes = []
        header = []
        messages = []
        images = []
        for cr in shaConfigs:
            # Compare results from sha config (cr) and base config (bcr)
            # TODO: rerun tests if exact match is not available ( include system)
            bcr = self._getRecentRun(cr, baseConfigs)
            if bcr is None:
                r = requests.patch(
                    url=self.CompareUrls[sha],
                    headers=self.auth.getTokenHeader(),
                    json=codeStatus([-1], ["MATCH CONFIGS"],
                                    [f"Couldn't find matching base run config in database for {str(cr)}"]))
                pretty_request(r)
            else:
                code, d = self._compareConfig(bcr, cr)
                codes.append(code)
                header.append(str(cr))
                messages.append(f"Smin: {d[0]}, Smax: {d[1]}, Savg: {d[2]}")

        print("COMPARISON RESULTS:", codes, header, messages)
        r = requests.patch(
            url=self.CompareUrls[sha],
            headers=self.auth.getTokenHeader(),
            json=speedupStatus(codes, header, messages, []))
        pretty_request(r)

    def _getRecentRun(self, cr, baseConfigs):
        # TODO: include system
        bcr = baseConfigs.filter(
            # CONFIG FIELDS
            container=cr.container,
            # Verlet
            rebuildFreq=cr.rebuildFreq,
            skinRadius=cr.skinRadius,
            # General
            layout=cr.layout,
            functor=cr.functor,
            newton=cr.newton,
            cutoff=cr.cutoff,
            cellSizeFactor=cr.cellSizeFactor,
            generator=cr.generator,
            boxLength=cr.boxLength,
            particles=cr.particles,
            traversal=cr.traversal,
            iterations=cr.iterations,
            tuningStrategy=cr.tuningStrategy,
            tuningInterval=cr.tuningInterval,
            tuningSamples=cr.tuningSamples,
            tuningMaxEvidence=cr.tuningMaxEvidence,
            epsilon=cr.epsilon,
            sigma=cr.sigma
        )
        try:
            recent = bcr.first()
            print(recent)
            return recent
        except Exception as e:
            print(e)
            print("Couldn't find matching config")
            return None

    def _compareConfig(self, bcr, cr):
        baseMeasurements = bcr.measurements
        commitMeasurements = cr.measurements

        assert(len(baseMeasurements) == len(commitMeasurements))

        configCodes = []
        speedUps = []

        for bm, cm in zip(baseMeasurements, commitMeasurements):
            code, speedup = self._calcSpeedup(bm, cm)
            configCodes.append(code)
            speedUps.append(speedup)

        sMin = np.min(speedUps)
        sMax = np.max(speedUps)
        sAvg = np.average(speedUps)

        if -1 in configCodes:
            return -1, [sMin, sMax, sAvg]
        elif 0 in configCodes:
            return 0, [sMin, sMax, sAvg]
        else:
            return 1, [sMin, sMax, sAvg]

    def _calcSpeedup(self, bm, cm):
        bmit = bm["ItMicros"]
        cmit = cm["ItMicros"]
        speedup = cmit / bmit
        print("Iteration Times:", bmit, cmit)
        T_FAIL = 1.05
        T_NEUTRAL = 0.95
        if speedup > T_FAIL:
            code = -1
        elif speedup > T_NEUTRAL:
            code = 0
        else:
            code = 1

        return code, speedup

if __name__ == '__main__':

    CheckFlow.AUTOPAS = "../../AutoPas"
    check = CheckFlow()
    sha = "9e733e6e5b2d310732aaacf094dd8937c3fed8a0"
    check.baseSHA = "75a49a209512a85843fd26a973cc1718444e64a6"
    check.baseUrl = "https://api.github.com/repos/kruegener/AutoPas"
    check.auth.updateInstallID(1692178)
    check.CompareUrls[sha] = check._createCheckRun(sha, "Comp Test")
    check._comparePerformance(sha)


