from git import Repo
import os
import shutil
from subprocess import run, PIPE
from glob import glob
import time
from datetime import datetime
import csv
import re

from model.Config import Config

# TODO: SET PROPERLY
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
        self.buildDir = os.path.join(self.baseDir, self.buildDir)
        self.mdFlexDir = os.path.join(self.buildDir, "examples/md-flexible")
        print(self.baseDir)

    def colonSep(self, c:Config, line):
        sep = line.split(":")
        e = [x for x in sep]
        if "Container" in e[0]:
            c.container = e[1].split(",")[0]
        elif "Layout" in e[0]:
            c.layout = e[1].split(",")[0]
        elif "Functor" in e[0]:
            c.functor = e[1].rstrip(" \n")
        elif "Newton3" in e[0]:
            c.newton = e[1].split(",")[0]
        elif "Cutoff" in e[0]:
            c.cutoff = e[1].rstrip(" \n")
        elif "Cell size factor" in e[0]:
            c.cellSizeFactor = e[1].rstrip(" \n")
        elif "Particle Generator" in e[0]:
            c.generator = e[1].rstrip(" \n")
        elif "Box length" in e[0]:
            c.boxLength = float(e[1].rstrip(" \n"))
        elif "total" in e[0]:
            particles = e[1].rstrip(" \n").split(" ")
            particles = [int(p) for p in particles[1:]]
            c.particles = particles
        elif "traversals" in e[0]:
            c.traversal = e[1].split(",")[0]
        elif "Iterations" in e[0]:
            iterations = e[1].rstrip(" \n").split(" ")
            iterations = [int(i) for i in iterations[1:]]
            c.iterations = iterations
        elif "Tuning Interval" in e[0]:
            c.tuningInterval = int(e[1].rstrip(" \n"))
        elif "Tuning Samples" in e[0]:
            c.tuningSamples = int(e[1].rstrip(" \n"))
        elif "epsilon" in e[0]:
            c.epsilon = float(e[1].rstrip(" \n"))
        elif "sigma" in e[0]:
            c.sigma = float(e[1].rstrip(" \n"))
        else:
            print("UNPROCESSED COLON SEP PAIR")
            print(e)


    def spaceSep(self, c:Config, line):
        print(line)
        sep = csv.reader(line, delimiter=":")
        pass

    def build(self):

        print("BUILD/MD-FLEX DIR: ", self.buildDir, self.mdFlexDir)

        # remove old buildDir if present
        shutil.rmtree(self.buildDir, ignore_errors=True)
        os.mkdir(self.buildDir)
        os.chdir(self.buildDir)

        # run cmake
        print("Running CMAKE")
        cmake_output = run(["cmake", "-DAUTOPAS_OPENMP=ON", "--target", "md-flexible", ".."], stdout=PIPE, stderr=PIPE)
        print(cmake_output.stdout, cmake_output.stderr)

        # run make
        print("Running MAKE")
        make_output = run(["make", "-j", "4"], stdout=PIPE, stderr=PIPE)
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

        print(self.mdFlexDir)

        measurements = glob(os.path.join(self.mdFlexDir, "measurePerf*/"))

        # all measurement folders (should only be 1 usually)
        for i, folder in enumerate(measurements):
            folder = os.path.basename(os.path.dirname(folder))
            folder = folder.lstrip("measurePerf_")
            timestamp = time.strptime(folder, "%Y-%m-%d_%H-%M-%S")
            print(timestamp)

            # change into measurement folder
            os.chdir(measurements[i])

            # collect all configs
            configPaths = glob(os.path.join(measurements[i], "*.csv"))
            configNames = [os.path.basename(x) for x in configPaths]
            print(configPaths)
            print(configNames)

            for i, conf in enumerate(configPaths):

                c = Config()
                c.name = configNames[i]
                c.date = datetime.utcfromtimestamp(int(time.mktime(timestamp)))

                # TODO:
                # - parse csv file for config details
                # - add listField with the actual measurements
                # - optional: add plotting
                with open(configPaths[i]) as f:
                    for r in f:
                        r = re.sub("\s\s+", " ", r)
                        if ":" in r:
                            self.colonSep(c, r)
                        else:
                            self.spaceSep(c, r)

                c.save()

                exit()

                print(c)


        os.chdir(self.baseDir)
