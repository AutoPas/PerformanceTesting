from git import Repo
import os
import shutil
from subprocess import run, PIPE
from glob import glob
import time
from datetime import datetime
import re
from cpuinfo import get_cpu_info
import matplotlib

# Switch for GUI
matplotlib.use("Agg")
#matplotlib.use("TkAgg")
from matplotlib import pyplot as plt

from model.Config import Config

class Commit:

    baseDir = ""
    buildDir = "build"
    mdFlexDir = ""

    def __init__(self, repo: Repo, sha):
        # Reset Dir to specified commit
        repo.head.reset(sha, index=True, working_tree=True)
        self.message = repo.head.commit.message
        self.sha = sha
        self.repo = repo
        print("New commit:", self.sha, self.message, "\n")
        self.baseDir = repo.git_dir.strip(".git")
        self.buildDir = os.path.join(self.baseDir, self.buildDir)
        self.mdFlexDir = os.path.join(self.buildDir, "examples/md-flexible")
        print(self.baseDir)
        # Status codes and messages
        self.codes = []
        self.statusMessages = []

    def updateStatus(self, code, message):
        self.codes.append(code)
        self.statusMessages.append(message)

    def build(self):

        print("BUILD/MD-FLEX DIR: ", self.buildDir, self.mdFlexDir)

        # remove old buildDir if present
        # TODO: RESET FOR PRODUCTION
        #shutil.rmtree(self.buildDir, ignore_errors=True)
        try:
            os.mkdir(self.buildDir)
        except FileExistsError:
            print("build folder existet already. RESET FOR PRODUCTION")
        os.chdir(self.buildDir)

        # run cmake
        print("Running CMAKE")
        cmake_output = run(["cmake", "-DAUTOPAS_OPENMP=ON", "--target", "md-flexible", ".."], stdout=PIPE, stderr=PIPE)
        returncode = cmake_output.returncode
        if returncode != 0:
            print("CMAKE failed with return code", returncode)
            self.updateStatus(-1, f"CMAKE failed:\n{cmake_output.stderr}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False
            #exit(returncode)
        #print(cmake_output.stdout, cmake_output.stderr)
        self.updateStatus(1, f"CMAKE succeeded:\n{cmake_output.stdout}")
        # run make
        print("Running MAKE")

        THREADS = os.environ["OMP_NUM_THREADS"]
        # TODO: SET -B for PRODUCTION, but should be clean anyway because of reset build folder
        #make_output = run(["make", "md-flexible", "-B", "-j", THREADS], stdout=PIPE, stderr=PIPE)
        make_output = run(["make", "md-flexible", "-j", THREADS], stdout=PIPE, stderr=PIPE)
        make_returncode = make_output.returncode
        if make_returncode != 0:
            print("MAKE failed with return code", make_returncode)
            self.updateStatus(-1, f"MAKE failed:\n{make_output.stderr}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False
            #exit(make_returncode)
        #print(make_output.stdout, make_output.stderr)

        # change back to top level directory
        os.chdir(self.baseDir)
        self.updateStatus(1, f"CMAKE+MAKE passed")
        return True

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
        if measure_output.returncode != 0:
            print("MEASUREPERF failed with return code", measure_output.returncode)
            #print(measure_output.stdout, measure_output.stderr)
            self.updateStatus(-1, f"MEASUREPERF failed:\nSTDOUT: .... {measure_output.stdout.decode('utf-8')[-1000:]}\nSTDERR:{measure_output.stderr.decode('utf-8')}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False
            #exit(measure_output.returncode)

        # change to top
        os.chdir(self.baseDir)
        self.updateStatus(1, f"MEASUREPERF succeeded: {measure_output.stdout}")
        return True

    def commaSplit(self, val):
        return val.split(",")[0]

    def newlineStrip(self, val):
        return val.rstrip(" \n")

    def colonSep(self, c:Config, line):
        sep = line.split(":")
        e = [x for x in sep]
        key = e[0]
        val = e[1]

        if "Container" in key:
            c.container = self.commaSplit(val).lstrip(" ")
        elif "Verlet rebuild frequency" in key:
            c.rebuildFreq = float(self.newlineStrip(val))
        elif "Verlet skin radius" in key:
            c.skinRadius = float(self.newlineStrip(val))
        elif "Layout" in key:
            c.layout = self.commaSplit(val)
        elif "Functor" in key:
            c.functor = self.newlineStrip(val)
        elif "Newton3" in key:
            c.newton = self.commaSplit(val)
        elif "Cutoff" in key:
            c.cutoff = self.newlineStrip(val)
        elif "Cell size factor" in key:
            c.cellSizeFactor = self.newlineStrip(val)
        elif "Particle Generator" in key:
            c.generator = self.newlineStrip(val)
        elif "Box length" in key:
            c.boxLength = float(self.newlineStrip(val))
        elif "total" in key:
            particles = self.newlineStrip(val).split(" ")
            particles = [int(p) for p in particles[1:]]
            c.particles = particles
        elif "traversals" in key:
            c.traversal = self.commaSplit(val)
        elif "Iterations" in key:
            iterations = self.newlineStrip(val).split(" ")
            iterations = [int(i) for i in iterations[1:]]
            c.iterations = iterations
        elif "Tuning Strategy" in key:
            c.tuningStrategy = self.newlineStrip(val)[1:]
        elif "Tuning Interval" in key:
            c.tuningInterval = int(self.newlineStrip(val))
        elif "Tuning Samples" in key:
            c.tuningSamples = int(self.newlineStrip(val))
        elif "Tuning Max evidence" in key:
            c.tuningMaxEvidence = int(self.newlineStrip(val))
        elif "epsilon" in key:
            c.epsilon = float(self.newlineStrip(val))
        elif "sigma" in key:
            c.sigma = float(self.newlineStrip(val))
        else:
            print("UNPROCESSED COLON SEP PAIR")
            print(e)
            self.updateStatus(0, f"UNPROCESSED COLON SEP PAIR at Parsing step: {e}")
            return True
            #exit(-1)
        return True

    def spaceSep(self, c:Config, line):
        sep = line.lstrip(" ").rstrip("\n").split(" ")
        if "Particles" in line or len(line) < 2:
            pass
        else:
            m = {}
            #print([s for s in sep])
            # NumParticles || GFLOPs/s || MFUPs/s || Time[micros] || SingleIteration[micros]
            m["N"] = int(sep[0])
            m["GFLOPs"] = float(sep[1])
            m["MFUPs"] = float(sep[2])
            m["Micros"] = float(sep[3])
            m["ItMicros"] = float(sep[4])
            c.measurements.append(m)
        return True

    def upload(self):

        print(self.mdFlexDir)

        measurements = glob(os.path.join(self.mdFlexDir, "measurePerf*/"))

        self.configs = []

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
            #print(configPaths)
            #print(configNames)
            cpu = get_cpu_info()["brand"]

            for i, conf in enumerate(configPaths):

                c = Config()
                c.name = configNames[i]
                c.date = datetime.utcfromtimestamp(int(time.mktime(timestamp)))
                c.commitSHA = self.sha
                c.commitMessage = self.repo.commit(self.sha).message
                c.commitDate = self.repo.commit(self.sha).authored_datetime

                # Assumes tests were run on this system
                c.system = cpu

                # TODO: Decide if uniqueness is enforced (Change spare in model to False)
                # c.unique = c.name + c.commitSHA + c.system + str(c.date)
                # try:
                #     c.save()
                # except NotUniqueError:
                #     print("Exact Configuration for system and commit + date already saved!")
                #     continue

                with open(configPaths[i]) as f:
                    for r in f:
                        r = re.sub("\s\s+", " ", r)
                        if ":" in r:
                            if not self.colonSep(c, r):
                                return False
                        else:
                            if not self.spaceSep(c, r):
                                return False

                c.save()
                print(c)
                self.configs.append(c)

        os.chdir(self.baseDir)
        self.updateStatus(1, "RESULT UPLOAD succeeded\n")
        return True

    def generatePlot(self):

        configs = self.configs
        containers = ["DirectSum", "LinkedCells", "VerletListsCells", "VerletClusterLists", "VerletLists"]
        figs = {}
        # Create figs
        for cont in containers:
            figs[cont] = plt.figure(cont, figsize=(16, 9))
            plt.xlabel("Particles")
            plt.ylabel("MFUP/s")

        for c in configs:
            data = c.measurements
            N = [d["N"] for d in data]
            MFUPs = [d["MFUPs"] for d in data]

            plt.figure(c.container)
            name = c.name.lstrip("runtimes_").rstrip(".csv")
            plt.semilogx(N, MFUPs, label=name)
            plt.xticks(N, N)
            plt.legend()

        os.chdir(self.mdFlexDir)

        for cont in containers:
            plt.figure(cont)
            plt.savefig(cont + ".png")

        os.chdir(self.baseDir)
        self.updateStatus(1, "PLOTTING succeeded\n")
        return True
