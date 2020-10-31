from git import Repo
from checks import Commit
from mongoDocuments import Setup, Checkpoint, QueueObject
from subprocess import run, PIPE
import os


class Repository:

    def __init__(self, gitPath, branch="origin/master"):
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
        return c.codes, c.headers, c.statusMessages, c.images

    def testMerge(self, baseSHA, branchSHA):
        """
        Trying a merge of base into branch

        Args:
            baseSHA: from e.g. origin/master
            branchSHA: from e.g. origin/feature

        Returns:

        """

        c = Commit(self.repo, branchSHA, baseSHA=baseSHA)   # Resets repo to mergeSha

        curdir = os.getcwd()

        os.chdir(self.repo.git_dir.rstrip('.git'))
        gitOutput = run(['git', 'merge', '--no-commit', baseSHA], stdout=PIPE, stderr=PIPE, encoding='utf-8')

        if gitOutput.returncode == 0:
            print(f'Merge of {baseSHA} and {branchSHA} succeeded.')
        else:
            print(f'Merge of {baseSHA} and {branchSHA} failed.')
            self.repo.head.reset(self.initialHead, index=True, working_tree=True)
            os.chdir(curdir)
            return [-1], ['Merge'], ['Merge failed'], []

        self._testCommit(c)

        os.chdir(curdir)
        # reset to previous state
        self.repo.head.reset(self.initialHead, index=True, working_tree=True)
        return c.codes, c.headers, c.statusMessages, c.images


    def testLast(self, last):

        last = self.commits[0:last]

        for commit in last:
            sha = commit.hexsha
            c = Commit(self.repo, sha)

            self._testCommit(c)

            # reset to previous state
            self.repo.head.reset(self.initialHead, index=True, working_tree=True)

    def _testCommit(self, c: Commit, customJob: QueueObject = None, plotting: bool = True):
        """
        test the commit and return status and images
        Args:
            c: Commit to test
            case: ['Setup', 'Checkpoint'] switch to use clean setups or checkpoints with their attached setups
            plotting: bool if plotting to imgur is needed

        Returns:

        """

        try:
            if c.build():
                print(f"{c.sha}: BUILD DONE")
                # Custom Job Testing
                if customJob is not None:
                    setup = customJob.customYaml
                    try:
                        checkpoint = customJob.customCheckpoint
                        measure = c.measureCheckpoint(checkpoint, setup)
                    except AttributeError:
                        measure = c.measure(setup)

                    if measure:
                        print(f"{c.sha}: Custom MEASUREMENT DONE")
                        if c.parse_and_upload():
                            print(f"{c.sha}: Custom UPLOAD DONE")
                    else:
                        c.save_failed_config('Run failed')

                # Default CI Testing
                else:
                    iterator = Setup.objects(active=True)
                    # TODO: Want to do same with checkpointed saves?
                    # iterator = Checkpoint.objects(active=True)
                    for it in iterator:
                        measure = c.measure(it)

                        if measure:
                            print(f"{c.sha}: MEASUREMENT DONE")
                            if c.parse_and_upload():
                                print(f"{c.sha}: UPLOAD DONE")
                                # TODO: Move outside for loop or only upload single picture inside generatePlot
                                if plotting:
                                    if c.generatePlot():
                                        print(f"{c.sha}: PLOTS DONE")
                                        print("done testing")
                        else:
                            c.save_failed_config('Run failed')
            else:
                c.save_failed_config('Build failed')

        except Exception as e:
            print(f"_testCommit {c.sha} failed with {e}")
            c.updateStatus(-1, 'GENERAL', f"failed with {e}")

    def fetchAll(self):
        """
        Fetching for all remote branches

        Returns:
        """
        print('Fetching all remotes')
        for remote in self.repo.remotes:
            remote.fetch()
            print('\t', remote)
