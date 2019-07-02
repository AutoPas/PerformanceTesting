from git import Repo
from Commit import Commit

class Repository:

    def __init__(self, gitPath, branch="master"):
        # Repo Object of already cloned Repo, expects a pulled and clean repo
        self.repo = Repo(gitPath)
        # get current head to reset later
        self.initialHead = self.repo.head.commit
        # Check for proper Repo
        if not self.repo.bare:
            self.commits = list(self.repo.iter_commits())
        else:
            print("empty repo")
            exit(-1)

    def testLatest(self):

        sha = self.commits[0].hexsha
        c = Commit(self.repo, sha)
        c.build()
        c.measure()

        # reset to previous state
        self.repo.head.reset(self.initialHead, index=True, working_tree=True)