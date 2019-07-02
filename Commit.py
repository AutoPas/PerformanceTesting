from git import Repo
import os
import shutil
from subprocess import run, PIPE

from model.Config import Config

# TODO: DISABLE
FAKE_BUILD = True

class Commit:

    baseDir = ""
    buildDir = "build"

    def __init__(self, repo: Repo, commit):
        # Reset Dir to specified commit
        repo.head.reset(commit, index=True, working_tree=True)
        self.message = repo.head.commit.message
        self.commit = commit
        self.repo = repo
        print("New commit:", self.commit, self.message, "\n")
        self.baseDir = repo.git_dir.strip(".git")
        print(self.baseDir)

    def build(self):

        buildDir = os.path.join(self.baseDir, self.buildDir)

        print("BUILD DIR: ", buildDir)

        # remove old buildDir if present
        if not FAKE_BUILD:
            shutil.rmtree(buildDir, ignore_errors=True)
            os.mkdir(buildDir)
        os.chdir(buildDir)

        # run cmake
        print("Running CMAKE")
        cmake_output = run(["cmake", "-DAUTOPAS_OPENMP=ON", "--target", "md-flexible", ".."], stdout=PIPE, stderr=PIPE)
        print(cmake_output.stdout, cmake_output.stderr)

        # run make
        print("Running MAKE")
        if FAKE_BUILD:
            make_output = run(["make", "-j", "4"], stdout=PIPE, stderr=PIPE)
        else:
            make_output = run(["make", "-B", "-j", "4"], stdout=PIPE, stderr=PIPE)
        print(make_output.stdout, make_output.stderr)

        # change back to top level directory
        os.chdir(self.baseDir)


    def measure(self):
        # change to build folder
        os.chdir(self.buildDir)
        
        # change to top
        os.chdir(self.baseDir)
