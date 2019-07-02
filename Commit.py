from git import Repo
import os
import shutil
from subprocess import run, PIPE

from model.Config import Config

# TODO: DISABLE
FAKE_BUILD = True
THREADS = 4

class Commit:

    baseDir = ""
    buildDir = "build"
    mdFlexDir = ""

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

        self.buildDir = os.path.join(self.baseDir, self.buildDir)
        self.mdFlexDir = os.path.join(self.buildDir, "examples/md-flexible")
        print("BUILD/MD-FLEX DIR: ", self.buildDir, self.mdFlexDir)

        # remove old buildDir if present
        if not FAKE_BUILD:
            shutil.rmtree(self.buildDir, ignore_errors=True)
            os.mkdir(self.buildDir)
        os.chdir(self.buildDir)

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
        # change to md-flexible folder
        os.chdir(self.mdFlexDir)

        # main.py path
        mainPath = os.path.dirname(os.path.abspath(__file__))
        print(mainPath)
        # short test script copy to build folder
        shutil.copy(os.path.join(mainPath, "measurePerf_short.sh"), self.mdFlexDir)

        # export thread number and run test
        measure_output = run(["./measurePerf_short.sh", "md-flexible"], stdout=PIPE, stderr=PIPE)
        print(measure_output.stdout, measure_output.stderr)

        # change to top
        os.chdir(self.baseDir)

    def upload(self):
        pass
