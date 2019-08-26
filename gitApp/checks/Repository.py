from git import Repo
from checks.Commit import Commit

class Repository:

    def __init__(self, gitPath, branch="master"):
        # Repo Object of already cloned Repo, expects a pulled and clean repo
        self.repo = Repo(gitPath)
        # Checkout branch
        self.repo.git.checkout(branch)
        # get current head to reset later
        self.initialHead = self.repo.head.commit
        # Check for proper Repo
        if not self.repo.bare:
            self.commits = list(self.repo.iter_commits())
        else:
            print("empty repo")
            exit(-1)

    def checkoutBranch(self, branch):
        print(f"Checking out {branch}")
        self.repo.git.checkout(branch)

    def testNewest(self):

        sha = self.commits[0].hexsha
        c = Commit(self.repo, sha)

        self._testCommit(c)

        # reset to previous state
        self.repo.head.reset(self.initialHead, index=True, working_tree=True)

    def testSHA(self, sha):

        c = Commit(self.repo, sha)

        self._testCommit(c)

        # reset to previous state
        self.repo.head.reset(self.initialHead, index=True, working_tree=True)

    def testLast(self, last):

        last = self.commits[0:last]

        for commit in last:
            sha = commit.hexsha
            c = Commit(self.repo, sha)

            self._testCommit(c)

            # reset to previous state
            self.repo.head.reset(self.initialHead, index=True, working_tree=True)

    def _testCommit(self, c: Commit):

        # TODO: Re-Enable
        c.build()
        c.measure()
        c.upload()
        c.generatePlot()