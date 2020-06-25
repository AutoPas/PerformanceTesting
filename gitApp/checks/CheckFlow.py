import json
import requests
import mongoengine as me
from pymongo import errors
import imp
import os
import io
import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    from gitApp.settings import BASE_DIR
except ModuleNotFoundError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.join('../gitApp', BASE_DIR)
from hook.helper import pretty_request, initialStatus, codeStatus, speedupStatus, get_dyn_keys, spawnWorker
from checks.Authenticator import Authenticator
from checks.Repository import Repository
from mongoDocuments.Config import Config
from mongoDocuments.QueueObject import QueueObject
from mongoDocuments.Results import Results
from checks.ImgurUploader import ImgurUploader

"""
Codes:
    -1: failed
    0: neutral
    1: success
"""


class CheckFlow:
    GIT_APP_ID = os.environ["GITHUBAPPID"]
    # TODO: Add to config file
    PEM = "private-key.pem"
    DB = "database.config"

    AUTOPAS = "../../AutoPas"
    PERF_THRESHOLD = 0.9  # TODO: Define speedup criterium further

    def __init__(self, initRepo=False):
        print("new checkFlow instance")
        self.auth = Authenticator(CheckFlow.PEM, CheckFlow.GIT_APP_ID)
        self.baseUrl = ""
        self.branch = ""
        self.baseSHA = ""
        self.base = ""

        # Initiate DB connection with settings from file
        dbPath = os.path.join(BASE_DIR, CheckFlow.DB)
        print(os.getcwd())
        try:
            db = imp.load_source('db', dbPath)
        except Exception as e:
            print(e)
            print("database.config MISSING. Create file based on: database.config.example")
            sys.exit(-1)

        # Connect to MongoDB
        print("DB settings: ", db.collection, db.user, db.server)  # , db.password)
        me.connect(db.collection, username=db.user, password=db.password, host=("mongodb://" + db.server))

        # Initiate Repo
        # TODO: Separate Hook calls from Worker calls
        if initRepo:
            self.repo = Repository(os.path.join(BASE_DIR, CheckFlow.AUTOPAS))

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
        # TODO: Needed here?
        # self.repo.checkoutBranch(self.branch)
        print(ci_url)

        # Run checks on commits url
        needWorker = self._checkCommits(ci_url)
        if needWorker:
            spawnWorker()

    def _checkCommits(self, url):
        """
        Gets list of pull request commits and runs checks
        :param url: url to receive commits from
        :return: if worker is needed
        """
        r = requests.get(url=url, headers=self.auth.getTokenHeader())
        pretty_request(r)
        print("COMMIT LIST:")
        cis = r.json()
        SHAs = [self.baseSHA]  # Adding additional SHA from master

        needWorker = False  # if nothing is added to queue, no worker needs to be spawned

        # Full list
        for c in cis:
            SHAs.append(c["sha"])
        for sha in SHAs:
            # CHECKING IF ALREADY TESTED and order by newest
            shaConfigs = Config.objects(commitSHA=sha).order_by('-id')
            if shaConfigs.count() == 0:
                print("NEW COMMIT", sha)
                queue = QueueObject()
                queue.commitSHA = sha
                queue.installID = self.auth.install_id
                try:
                    queue.save()
                except me.NotUniqueError:
                    print('SHA is already queued')
                    continue
                queue.runUrl = self._createCheckRun(sha, "Performance Run")
                if sha is not self.baseSHA:
                    queue.compareUrl = self._createCheckRun(sha, "Performance Comparison")
                queue.running = False
                queue.save()
                needWorker = True  # Switch on worker spawn
            else:
                print("Available Tests for SHA", shaConfigs.count())
                print("COMMIT ALREADY TESTED", sha)
                continue

        return needWorker


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

    def runCheck(self, sha, runUrl):

        # RUN CHECK
        print(f"RUNNING CHECKS ON {sha} {runUrl}")

        # Update Status to in Progress
        r = requests.patch(url=runUrl, headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            cwd = os.getcwd()
            print("Running Threads:", os.environ["OMP_NUM_THREADS"])
            # TODO: _IMPORTANT: Think about replicating that work flow here and actually make
            #  build / measure / upload their own check runs in the suite or via updateStatus
            codes, headers, messages, images = self.repo.testSHA(sha)

            os.chdir(cwd)
            print("CODES", codes, messages)
            r = requests.patch(
                url=runUrl,
                headers=self.auth.getTokenHeader(),
                json=codeStatus(codes, headers, messages, images))
            pretty_request(r)
            if -1 in codes:
                return False
            else:
                return True
        except Exception as e:
            print(e)
            print(f"TestSHA {sha} failed with exit")
            r = requests.patch(
                url=runUrl,
                headers=self.auth.getTokenHeader(),
                json=codeStatus([-1], ["GENERAL"], [f"exit() statement called\n{e}"]))
            pretty_request(r)
            return False

    def comparePerformance(self, sha, compareUrl):

        print(f"Comparing Performance for {sha} {compareUrl}")
        # Update Status to in Progress
        r = requests.patch(url=compareUrl, headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            # Get Pull Requests associated with sha
            commitPR_url = f'{compareUrl.split("/check-runs/")[0]}/commits/{str(sha)}/pulls'
            r = requests.get(url=commitPR_url, headers=self.auth.getTokenHeader())
            pretty_request(r)

            # TODO: What if involved in more than one PR
            shaPRs = r.json()
            if len(shaPRs) == 0:
                raise RuntimeError(f'<b>Github Commit API returned 0 Pull Requests associated with this SHA {sha} at {commitPR_url}</b>')
            baseSHA = shaPRs[0]['base']['sha']

            # TODO: What if multiple configs are all of interest, and not just the newest
            base = Config.objects(commitSHA=baseSHA).order_by('-date').first()  # Get freshest config
            if base is None:
                # Todo: Rerun tests if base has not failed, but just not been tested yet
                raise RuntimeError(f'<b>No performance runs for the PR base {baseSHA} were found</b>')
            test = Config.objects(commitSHA=sha, system=base.system, setup=base.setup).order_by('-date').first()  # Get freshest config
            if test is None:
                raise RuntimeError(f'<b>No matching configs between this commit {sha} and PR base {baseSHA} could be found.</b>')
            fig, minSpeeds, meanSpeeds, missing = self._compareConfigs(base, test)

            # Upload figure
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            imgur = ImgurUploader()
            link, hash = imgur.upload(buf.read())
            test.compImgurLink = link
            test.compDeleteHash = hash
            test.save()

            message = f'<b>Perf Results:</b>\n\n' \
                      f'<b>Comparing this commit</b> {sha} with base {baseSHA}\n' \
                      f'<b>Threshold to pass:</b> speedup >= {CheckFlow.PERF_THRESHOLD}\n' \
                      f'<b>Minimum Time Speedup Average:</b> {np.mean(minSpeeds)}\n' \
                      f'<b>Mean Time Speedup Average:</b> {np.mean(meanSpeeds)}\n\n' \
                      f'<b>Not available configs to compare:</b> {missing}'

            # Setup Params for message
            code = [1 if np.mean(minSpeeds) >= CheckFlow.PERF_THRESHOLD else -1]
            header = ['COMPARISON']
            message = [message]
            params = codeStatus(code, header, message, [link])

        except RuntimeError as v:
            code = [0]
            header = ['COMPARISON']
            message = [str(v)[-500:]]
            params = codeStatus(code, header, message)

        except Exception as e:
            code = [-1]
            header = ['COMPARISON']
            message = [str(e)[-500:]]
            params = codeStatus(code, header, message)

        # Patch Checkrun
        r = requests.patch(url=compareUrl, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)


    def _compareConfigs(self, base: Config, test: Config):
        """
        Given two configs, find all overlapping results and compare them

        :param base: PR Base SHA config
        :param test: Commit in PR to compare to base
        :return:
        """

        # Use base as common denominator and look for results containing the keys in base
        baseResults = Results.objects(config=base)
        testResults = Results.objects(config=test)

        missing_results_counter = 0
        labels = []
        minSpeeds = []
        meanSpeeds = []

        for baseRes in baseResults:
            # Build dynamic keys dict
            dynamicFields = [key for key in baseRes.__dict__['_fields_ordered'] if 'dynamic_' in key]
            query = dict()
            for field in dynamicFields:
                query[field] = baseRes[field]

            # Get Results with matching settings (filter existing queryset)
            testRes = testResults.filter(**query)
            if len(testRes) == 0:
                missing_results_counter += 1
                continue
            testRes = testRes.order_by('-_id').first()  # Get newest matching if there's more than one

            minSpeedup, meanSpeedup = self._compareResults(baseRes, testRes)
            minSpeeds.append(minSpeedup)
            meanSpeeds.append(meanSpeedup)
            labels.append(get_dyn_keys(testRes))

        sort_keys = np.argsort(minSpeeds)
        sorted_min_speedsup = np.array(minSpeeds)[sort_keys]
        sorted_mean_speedsup = np.array(meanSpeeds)[sort_keys]
        sorted_labels = np.array(labels)[sort_keys]

        colors = ['g' if speed >= CheckFlow.PERF_THRESHOLD else 'r' for speed in sorted_min_speedsup]

        fig = plt.figure(figsize=(15, len(labels)/4))
        plt.title('Speedup')
        plt.barh(np.arange(len(labels)), sorted_min_speedsup, color=colors, alpha=.5, label='Speedup: minimum runtime')
        plt.barh(np.arange(len(labels)), sorted_mean_speedsup, color='gray', alpha=.5, label='Speedup: mean runtime')
        plt.axvline(1, c='k', label='no change')
        plt.axvline(CheckFlow.PERF_THRESHOLD, c='r', label='passing threshold')
        plt.yticks(np.arange(len(labels)), sorted_labels)
        plt.legend()
        plt.grid(which='both', axis='x')
        plt.xlim(0, 2)
        plt.tight_layout()
        # plt.show()

        print(f"{missing_results_counter} not matched out of {len(baseResults)}")
        return fig, sorted_min_speedsup, sorted_mean_speedsup, missing_results_counter

    def _compareResults(self, base: Results, test: Results):
        """
        Compare invididual matching results

        :param base:
        :param test:
        :return: Speedups
        """
        return base.minTime / test.minTime, base.meanTime / test.meanTime



if __name__ == '__main__':

    CheckFlow.AUTOPAS = "../../AutoPas"
    check = CheckFlow()
    single_sha = "3ca1622626af6627d263971bc3351d208d72ec0e"
    check.baseSHA = "cb22dd6e28ad8d4f25b076562e4bf861613b3153"
    check.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"
    check.auth.updateInstallID(2027548)
    #check.CompareUrls[single_sha] = check._createCheckRun(single_sha, "DEBUG TEST")
    #runUrl = check._createCheckRun(single_sha, "DEBUG TEST")
    #check.runCheck(single_sha, runUrl)
    check.comparePerformance(single_sha, 'https://api.github.com/repos/AutoPas/AutoPas/check-runs/762824540')


