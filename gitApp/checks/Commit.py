from model.Config import Config
from hook.helper import convertOutput

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
from matplotlib import pyplot as plt
from warnings import warn

# Switch for GUI
matplotlib.use("Agg")
# matplotlib.use("TkAgg")


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
        self.configs = []
        print("New commit:", self.sha, self.message, "\n")
        self.baseDir = repo.git_dir.strip(".git")
        self.buildDir = os.path.join(self.baseDir, self.buildDir)
        self.mdFlexDir = os.path.join(self.buildDir, "examples/md-flexible")
        print("BASE DIR:", self.baseDir)
        print("BUILD DIR:", self.buildDir)
        print("MDFLEX DIR:", self.mdFlexDir)
        # Status codes, headers and messages
        self.codes = []
        self.headers = []
        self.statusMessages = []

    def updateStatus(self, code, header, message):
        self.codes.append(code)
        self.headers.append(header)
        self.statusMessages.append(message)

    def build(self):

        print("BUILD/MD-FLEX DIR: ", self.buildDir, self.mdFlexDir)

        # remove old buildDir if present
        shutil.rmtree(self.buildDir, ignore_errors=True)
        try:
            os.mkdir(self.buildDir)
        except FileExistsError:
            print("build folder existed already. RESET FOR PRODUCTION")
        os.chdir(self.buildDir)

        # run cmake
        print("Running CMAKE")
        cmake_output = run(["cmake", "-DAUTOPAS_OPENMP=ON", "--target", "md-flexible", ".."], stdout=PIPE, stderr=PIPE)
        returncode = cmake_output.returncode
        if returncode != 0:
            print("CMAKE failed with return code", returncode)
            self.updateStatus(-1, "CMAKE", f"CMAKE failed:\n{convertOutput(cmake_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False

        self.updateStatus(1, "CMAKE", f"CMAKE succeeded:\n{convertOutput(cmake_output.stdout)[-800:]}")

        # run make
        print("Running MAKE")

        THREADS = os.environ["OMP_NUM_THREADS"]
        make_output = run(["make", "md-flexible", "-B", "-j", THREADS], stdout=PIPE, stderr=PIPE)
        make_returncode = make_output.returncode
        if make_returncode != 0:
            print("MAKE failed with return code", make_returncode)
            self.updateStatus(-1, "MAKE", f"MAKE failed:\n{convertOutput(make_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False

        self.updateStatus(1, "MAKE", f"MAKE succeeded:\n{convertOutput(make_output.stdout)[-800:]}")

        # change back to top level directory
        os.chdir(self.baseDir)
        self.updateStatus(1, "BUILD", f"CMAKE+MAKE passed")
        return True

    def measure(self):
        # change to md-flexible folder
        os.chdir(self.mdFlexDir)

        # main.py path
        # issues with using the __file__ method when deploying via uwsgi
        # mainPath = os.path.abspath(os.path.dirname(__file__))
        mainPath = os.path.join(self.baseDir, "..", "PerformanceTesting/gitApp/checks")
        print("measure_perf directory:", mainPath)
        # short test script copy to build folder
        shutil.copy(os.path.join(mainPath, "measurePerf_short.sh"), self.mdFlexDir)

        # export thread number and run test
        measure_output = run(["./measurePerf_short.sh", "md-flexible"], stdout=PIPE, stderr=PIPE)
        if measure_output.returncode != 0:
            print("MEASUREPERF failed with return code", measure_output.returncode)
            self.updateStatus(-1,
                              "PERFORMANCE MEASUREMENT",
                              f"MEASUREPERF failed:\nSTDOUT: .... "
                              f"{convertOutput(measure_output.stdout)[-500:]}\n"
                              f"STDERR:{convertOutput(measure_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False

        # change to top
        os.chdir(self.baseDir)
        self.updateStatus(1, "PERFORMANCE MEASUREMENT", f"MEASUREPERF succeeded: \n...\n"
                                                        f"{convertOutput(measure_output.stdout)[-500:]}")
        return True

    @staticmethod
    def commaSplit(val):
        return val.split(",")[0]

    @staticmethod
    def newlineStrip(val):
        return val.rstrip(" \n")

    @FutureWarning
    def colonSep(self, c: Config, line):
        """WARNING: Deprecated"""
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
            self.updateStatus(0, "PARSING", f"UNPROCESSED COLON SEP PAIR at Parsing step: {e}")
            return True
        return True

    @staticmethod
    @FutureWarning
    def spaceSep(c: Config, line):
        """WARNING: Deprecated"""
        sep = line.lstrip(" ").rstrip("\n").split(" ")
        if "Particles" in line or len(line) < 2:
            pass
        else:
            m = {
                "N": int(sep[0]),
                "GFLOPs": float(sep[1]),
                "MFUPs": float(sep[2]),
                "Micros": float(sep[3]),
                "ItMicros": float(sep[4])
            }
            # print([s for s in sep])
            # NumParticles || GFLOPs/s || MFUPs/s || Time[micros] || SingleIteration[micros]
            c.measurements.append(m)
        return True

    def upload(self):

        print("uploading", self.mdFlexDir)

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
            # print(configPaths)
            # print(configNames)
            try:
                cpu = get_cpu_info()["brand"]
            except Exception as e:
                print(f"Couldn't determine CPU brand: {e}")
                cpu = "N/A"

            for j, conf in enumerate(configPaths):

                c = Config()
                c.name = configNames[j]
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

                with open(configPaths[j]) as f:
                    for r in f:
                        r = re.sub("\s\s+", " ", r)

                        # TODO: test dynamic fields
                        if ":" in r:
                            if not self.colonRegex(c, r):
                                return False
                            # if not self.colonSep(c, r):
                            #    return False
                        else:
                            if not self.spaceRegex(c, r):
                                return False
                            # if not self.spaceSep(c, r):
                            #    return False

                try:
                    c.save()
                except Exception as e:
                    self.updateStatus(-1, "UPLOAD", str(e))
                    return False

                print(c)
                self.configs.append(c)

        os.chdir(self.baseDir)
        self.updateStatus(1, "UPLOAD", "RESULT UPLOAD succeeded\n")
        return True

    def generatePlot(self):

        configs = self.configs
        containers = ["DirectSum", "LinkedCells", "VerletListsCells", "VerletClusterLists", "VerletLists"]
        figs = {}
        try:
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
        except Exception as e:
            self.updateStatus(-1, "PLOTTING", str(e))
            return False

        os.chdir(self.baseDir)
        self.updateStatus(1, "PLOTTING", "PLOTTING succeeded\n")
        return True

    def colonRegex(self, c: Config, line: str):
        """
        Parses lines containing ':' and adds dynamic fields to mongo document

        :param c: Current config
        :param line: Line to parse
        :return: True/False on success
        """
        try:
            pattern = re.compile('(\S+.*\S+)\s*:\s+(.*)')
            key, value = pattern.findall(line)

            # TODO: Optionally try casting to float and int
            # Add dynamic field to the config model
            c[key] = value
            return True

        except Exception as e:
            warn(f'Colon Seperation in upload failed with: {e}')
            self.updateStatus(0, "PARSING", f"UNPROCESSED COLON SEP PAIR at Parsing step: {line, e}")
            return False

    def spaceRegex(self, c: Config, line: str):
        """
        Parses lines containing spaces seperation, here the number of particles and the measurements

        :param c: Config
        :param line: String line
        :return: True/False depending on success
        """

        try:
            pattern = re.compile('\s*(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*')

            res = pattern.findall(line)
            if len(res) == 0:
                pass

            m = {
                "N": int(res[0]),
                "GFLOPs": float(res[1]),
                "MFUPs": float(res[2]),
                "Micros": float(res[3]),
                "ItMicros": float(res[4])
            }
            c.measurements.append(m)

            return True
        except Exception as e:
            warn(f'spaceRegex failed with {line, e}')
            self.updateStatus(0, "PARSING", f"UNPROCESSED SPACE SEP PAIR at Parsing step: {line, e}")
            return False
