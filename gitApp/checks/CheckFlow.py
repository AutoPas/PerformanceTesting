import json
import requests
import mongoengine as me
import imp
import os
import io
import sys
import numpy as np
import matplotlib.pyplot as plt
from subprocess import run, PIPE

try:
    from gitApp.settings import BASE_DIR
except ModuleNotFoundError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BASE_DIR = os.path.join('../gitApp', BASE_DIR)
from hook.helper import pretty_request, initialStatus, codeStatus, spawnWorker, get_dyn_keys, generate_label_table
from checks import Authenticator
from checks import ImgurUploader
from checks import Repository
from mongoDocuments import Config
from mongoDocuments import QueueObject
from mongoDocuments import Result

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

    def __init__(self, initRepo=True):
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
            self.repo.fetchAll()

    def receiveHook(self, request):  # WSGIRequest):
        """ on receive of pull_request event """

        print("RUNNING CHECKS")
        body = json.loads(request.body)
        # Update Repo installation ID for Github App auth
        self.auth.updateInstallID(int(body["installation"]["id"]))

        # Fetching for Repo
        self.repo.fetchAll()

        # Base url for all API request for this repo
        self.baseUrl = body["repository"]["url"]
        pull = body["pull_request"]

        # Get URL for commits list
        ci_url = pull["commits_url"]

        # Checkout branch associated with pull request
        self.branch = pull["head"]["ref"]
        self.base = pull["base"]["ref"]
        # self.baseSHA = pull["base"]["sha"]  # Completely unclear what determines which SHA is printed here. It's not the HEAD
        print(ci_url)

        # Run checks on commits url
        needWorker = self._checkCommits(ci_url)
        if needWorker:
            spawnWorker()


    def _getLastCommonRef(self, baseRef: str, branchRef: str) -> str:
        """
        Running git command in AutoPas Repo to find last common ref.
        This usually is the last time origin/master was merged into the feature branch.

        Args:
            baseRef: SHA on base branch or ref (e.g. origin/master)
            branchRef: SHA on feature branch or ref

        Returns:
            str: last common ref

        """

        baseDir = os.getcwd()
        os.chdir(self.repo.repo.git_dir.strip('.git'))

        gitOutput = run(['git', 'merge-base', baseRef, branchRef], stdout=PIPE, stderr=PIPE, encoding='utf-8')

        os.chdir(baseDir)

        if gitOutput.returncode == 0:
            sha = gitOutput.stdout.strip('\n')
        else:
            raise ValueError(f'No Common Ref found for: {baseRef} {branchRef}', gitOutput.stderr)

        return sha

    def _getForkPoint(self, baseBranch: str, branchRef: str) -> str:
        """
        Running git command in AutoPas Repo to find fork point of branch.

        Args:
            baseBranch: name of base branch, e.g. master
            branchRef: SHA on feature branch or ref (e.g. origin/feature)

        Returns:
            str: fork point sha on baseBranch

        """

        baseDir = os.getcwd()
        os.chdir(self.repo.repo.git_dir.strip('.git'))

        gitOutput = run(['git', 'merge-base', '--fork-point', baseBranch, branchRef], stdout=PIPE, stderr=PIPE, encoding='utf-8')

        os.chdir(baseDir)

        if gitOutput.returncode == 0:
            sha = gitOutput.stdout.strip('\n')
        else:
            raise ValueError(f'No Fork Point found for: {baseBranch} {branchRef}', gitOutput.stderr)

        return sha


    def _getBranchHead(self, baseBranch: str) -> str:
        """
        Running git command in AutoPas Repo to find head of branch

        Args:
            baseBranch: name of base branch, e.g. master

        Returns:
            str: HEAD sha on baseBranch

        """

        baseDir = os.getcwd()
        os.chdir(self.repo.repo.git_dir.strip('.git'))

        gitOutput = run(['git', 'show-ref', '--hash', baseBranch], stdout=PIPE, stderr=PIPE, encoding='utf-8')

        os.chdir(baseDir)

        if gitOutput.returncode == 0:
            sha = gitOutput.stdout.strip('\n')
        else:
            raise ValueError(f'No HEAD found for: {baseBranch}', gitOutput.stderr)

        return sha


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

        self.baseSHA = self._getBranchHead(f'origin/{self.base}')
        compareSHAs = {'0_BaseSHA': self.baseSHA}
        # Adding Fork Point if available
        try:
            forkPoint = self._getForkPoint(baseBranch=f'origin/{self.base}', branchRef=f'origin/{self.branch}')
            compareSHAs['1_ForkPoint'] = forkPoint
        except ValueError:
            print(f'No Forkpoint found for {self.branch} on {self.base}')
        # Adding Last Common Commit if available
        try:
            lastCommon = self._getLastCommonRef(baseRef=f'origin/{self.base}', branchRef=f'origin/{self.branch}')
            compareSHAs['2_LastCommon'] = lastCommon
        except ValueError:
            print(f'No common ancestor between {self.base} and {self.branch}')

        needWorker = False  # if nothing is added to queue, no worker needs to be spawned

        prSHAs = []
        # Full list
        for c in cis:
            prSHAs.append(c["sha"])

        allSHAs = list(compareSHAs.values()) + prSHAs

        for sha in allSHAs:
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
                if sha in prSHAs:
                    queue.compareOptions = compareSHAs
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


    def runCheck(self, q: QueueObject):

        # RUN CHECK
        print(f"RUNNING CHECKS ON {q.commitSHA} {q.runUrl}")

        # Update Status to in Progress
        r = requests.patch(url=q.runUrl, headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        try:
            cwd = os.getcwd()
            print("Running Threads:", os.environ["OMP_NUM_THREADS"])

            # Check if commit has comparisons setup
            if '0_BaseSHA' in q.compareOptions.keys():
                # BaseSHA is available (should always be the case)
                baseSHA = q.compareOptions['0_BaseSHA']
                # Try to merge base into branch and run performance
                codes, headers, messages, images = self.repo.testMerge(baseSHA=baseSHA, branchSHA=q.commitSHA)

                if -1 in codes:
                    # Merge has failed, run unmerged instead
                    codes, headers, messages, images = self.repo.testSHA(q.commitSHA)

            else:
                # No comparison modes set. Just test commit
                codes, headers, messages, images = self.repo.testSHA(q.commitSHA)

            os.chdir(cwd)

            print("CODES", codes, messages)
            r = requests.patch(
                url=q.runUrl,
                headers=self.auth.getTokenHeader(),
                json=codeStatus(codes, headers, messages, images))
            pretty_request(r)
            if -1 in codes:
                return False
            else:
                return True

        except Exception as e:
            print(e)
            print(f"TestSHA {q.commitSHA} failed with exit")
            r = requests.patch(
                url=q.runUrl,
                headers=self.auth.getTokenHeader(),
                json=codeStatus([-1], ["GENERAL"], [f"exit() statement called\n{e}"]))
            pretty_request(r)
            return False

    def comparePerformance(self, q: QueueObject):
        """
        Function to compare performance between different commits in the Repo.

        Works on a checkrun already created via the GitHub checks api at compareUrl.
        Comparison options include:
            1a) Merge Current Master Head into branch and compare performance between merged and un-merged master
            1b) Merge failed -> Compare between non-merged feature branch and master
            2) To Be Implemented (perf already available): Compare against the Fork Point
            3) To Be Implemented (perf already available): Compare against the Last Common commit between master and feature branch

        Args:
            q: QueueObject containing all necessary information to run comparison

        Returns:

        """

        commitSHA = q.commitSHA
        print(f"Comparing Performance for {commitSHA} {q.compareUrl}")
        # Update Status to in Progress
        r = requests.patch(url=q.compareUrl, headers=self.auth.getTokenHeader(), json=initialStatus())
        pretty_request(r)

        codes, headers, messages, images = [], [], [], []

        try:
            # Get Pull Requests associated with sha
            # commitPR_url = f'{compareUrl.split("/check-runs/")[0]}/commits/{str(sha)}/pulls'
            # r = requests.get(url=commitPR_url, headers=self.auth.getTokenHeader())

            baseSHA = q.compareOptions['0_BaseSHA']
            baseConfigs = Config.objects(commitSHA=baseSHA).order_by('-date')
            if baseConfigs.first() is None:
                raise RuntimeError(f'<b>No performance runs for the PR base {baseSHA} were found</b>')

            # Check for all configs, aka Setups
            for base in baseConfigs:
                test = Config.objects(commitSHA=commitSHA, system=base.system, setup=base.setup).order_by('-date').first()  # Get freshest config
                if test is None:
                    raise RuntimeError(f'<b>No matching configs between this commit {commitSHA} and PR base {baseSHA} could be found.</b>')

                # Case 1) Merge worked out
                if test.mergedBaseSHA is not None:
                    headers.append('Merged Master into Feature Branch Comparison')
                else:
                    headers.append('Feature vs. Master Comparison (no-merge)')

                # TODO: Add comparison for lastcommon and fork point, perf tests are already running

                fig, minSpeeds, meanSpeeds, missing = self._compareConfigs(base, test)

                # Upload figure
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                imgur = ImgurUploader()
                link, hash = imgur.upload(buf.read())
                images.append(link)
                test.compImgurLink = link
                test.compDeleteHash = hash
                test.save()

                messages.append(f'<b>Perf Results:</b>\n\n'
                                f'<b>Setup:</b> {test.setup.name}'
                                f'<b>Comparing this commit</b> {commitSHA} with base {baseSHA}\n'
                                f'<b>Threshold to pass:</b> speedup >= {CheckFlow.PERF_THRESHOLD}\n'
                                f'<b>Minimum Time Speedup Average:</b> {np.mean(minSpeeds)}\n'
                                f'<b>Mean Time Speedup Average:</b> {np.mean(meanSpeeds)}\n\n'
                                f'<b>Not available configs to compare:</b> {missing}')

                # Setup Params for message
                codes.append(1 if np.mean(minSpeeds) >= CheckFlow.PERF_THRESHOLD else -1)

            params = codeStatus(codes, headers, messages, images)

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
        r = requests.patch(url=q.compareUrl, headers=self.auth.getTokenHeader(), json=params)
        pretty_request(r)


    def _compareConfigs(self, base: Config, test: Config):
        """
        Given two configs, find all overlapping results and compare them

        :param base: PR Base SHA config
        :param test: Commit in PR to compare to base
        :return:
        """

        # Use base as common denominator and look for results containing the keys in base
        baseResults = Result.objects(config=base)
        testResults = Result.objects(config=test)

        missing_results_counter = 0
        minSpeeds = []
        meanSpeeds = []

        matchedResults = []

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
            matchedResults.append(testRes)

        header, all_keys = get_dyn_keys(matchedResults)
        header_string = r'$\bf{' + header + '}$'
        labels = generate_label_table(matchedResults, all_keys)

        sort_keys = np.argsort(minSpeeds)
        sorted_min_speedsup = np.array(minSpeeds)[sort_keys]
        sorted_mean_speedsup = np.array(meanSpeeds)[sort_keys]
        sorted_labels = labels[sort_keys]
        sorted_labels = np.append(sorted_labels, header_string)

        colors = ['g' if speed >= CheckFlow.PERF_THRESHOLD else 'r' for speed in sorted_min_speedsup]

        fig = plt.figure(figsize=(15, len(labels)/4))
        plt.title('Speedup')
        plt.barh(np.arange(len(sort_keys)), sorted_min_speedsup, color=colors, alpha=.5, label='Speedup: minimum runtime')
        plt.barh(np.arange(len(sort_keys)), sorted_mean_speedsup, color='gray', alpha=.5, label='Speedup: mean runtime')
        plt.axvline(1, c='k', label='no change')
        plt.axvline(CheckFlow.PERF_THRESHOLD, c='r', label='passing threshold')
        plt.yticks(np.arange(len(sorted_labels)), sorted_labels)
        plt.legend(loc='lower right')
        plt.grid(which='both', axis='x')
        plt.xlim(0, 2)
        plt.tight_layout()
        plt.show()

        print(f"{missing_results_counter} not matched out of {len(baseResults)}")
        return fig, sorted_min_speedsup, sorted_mean_speedsup, missing_results_counter


    @staticmethod
    def _compareResults(base: Result, test: Result):
        """
        Compare invididual matching results

        :param base:
        :param test:
        :return: Speedups
        """
        return base.minTime / test.minTime, base.meanTime / test.meanTime



if __name__ == '__main__':

    CheckFlow.AUTOPAS = "../../AutoPas"
    check = CheckFlow(initRepo=True)

    try:
        bc = check._getBranchHead('origin/master')
        print(bc)
        lc = check._getLastCommonRef('637c2e2', 'a6e67a4')
        print(lc)
        fc = check._getForkPoint('origin/master', 'a6e67a4')
        print(fc)
    except ValueError:
        pass
    single_sha = "64a5b092bc32a7b01e19be4091a79148fecb04e7"
    # check.baseSHA = "cb22dd6e28ad8d4f25b076562e4bf861613b3153"
    check.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"
    check.auth.updateInstallID(2027548)
    #check.CompareUrls[single_sha] = check._createCheckRun(single_sha, "DEBUG TEST")
    runUrl = check._createCheckRun(single_sha, "DEBUG TEST")
    check.runCheck(single_sha, runUrl)
    #check.comparePerformance(single_sha, 'https://api.github.com/repos/AutoPas/AutoPas/check-runs/762824540')


