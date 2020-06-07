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
        # fetch commits and branches
        print(f"Fetching")
        self.repo.git.fetch()
        # reset any current changes
        print(f"Resetting last branch")
        self.repo.git.reset('--hard')
        print(f"Checking out {branch}")
        self.repo.git.checkout(branch)
        # reset any changes there (only if it wasn't checked out)
        print(f"Resetting {branch}")
        self.repo.git.reset('--hard')
        # remove any extra non-tracked files (.pyc, etc)
        print(f"Cleaning {branch}")
        self.repo.git.clean('-xdf')
        # pull in the changes from from the remote
        # print(f"Pulling {branch}")
        # self.repo.git.pull()

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

        try:
            if c.build():
                print(f"{c.sha}: BUILD DONE")
                if c.measure():
                    print(f"{c.sha}: MEASUREMENT DONE")
                    if c.parse_and_upload():
                        print(f"{c.sha}: UPLOAD DONE")
                        if c.generatePlot():
                            print(f"{c.sha}: PLOTS DONE")
                            print("done testing")
        except Exception as e:
            print(f"_testCommit {c.sha} failed with {e}")
            c.updateStatus(-1, 'GENERAL', f"failed with {e}")

