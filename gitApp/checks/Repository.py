from git import Repo
from checks.Commit import Commit


class Repository:

    def __init__(self, gitPath, branch="master"):
        # Repo Object of already cloned Repo, expects a pulled and clean repo
        self.repo = Repo(gitPath)
        # Checkout branch
        self.checkoutBranch(branch)
        # get current head to reset later
        self.initialHead = self.repo.head.commit
        # Check for proper Repo
        if not self.repo.bare:
            self.commits = list(self.repo.iter_commits())
        else:
            print("empty repo")
            exit(-1)

    def checkoutBranch(self, branch):
        # reset any current changes
        self.repo.git.reset('--hard')
        print(f"Checking out {branch}")
        self.repo.git.checkout(branch)
        # reset any changes there (only if it wasn't checked out)
        self.repo.git.reset('--hard')
        # remove any extra non-tracked files (.pyc, etc)
        self.repo.git.clean('-xdf')
        # pull in the changes from from the remote
        self.repo.remotes.origin.pull()

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
        return c.codes, c.headers, c.statusMessages

    def testLast(self, last):

        last = self.commits[0:last]

        for commit in last:
            sha = commit.hexsha
            c = Commit(self.repo, sha)

            self._testCommit(c)

            # reset to previous state
            self.repo.head.reset(self.initialHead, index=True, working_tree=True)

    def _testCommit(self, c: Commit):

        if c.build():
            if c.measure():
                if c.upload():
                    if c.generatePlot():
                        print("done testing")
