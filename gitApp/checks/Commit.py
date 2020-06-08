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
import numpy as np

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
        self.measure_output = None
        self.perfSetup = {}

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

        # main.py path
        # issues with using the __file__ method when deploying via uwsgi
        # mainPath = os.path.abspath(os.path.dirname(__file__))
        mainPath = os.path.join(self.baseDir, "..", "PerformanceTesting/gitApp/checks")
        print("measure_perf directory:", mainPath)

        # change to md-flexible folder
        os.chdir(self.mdFlexDir)

        self.perfSetup = {
            'deltaT': 0.0,
            'tuningPhases': 1,
            'generator': 'uniform',
            'particles': 1000
        }
        # Running one tuning session
        self.measure_output = run(['./md-flexible',
                              '--deltaT', f'{self.perfSetup["deltaT"]}',
                              '--tuning-phases', f'{self.perfSetup["tuningPhases"]}',
                              '--log-level', 'debug',
                              '--particle-generator', f'{self.perfSetup["generator"]}',
                              '--particles-total', f'{self.perfSetup["particles"]}'], stdout=PIPE, stderr=PIPE)
        if self.measure_output.returncode != 0:
            print("MEASUREPERF failed with return code", self.measure_output.returncode)
            self.updateStatus(-1,
                              "PERFORMANCE MEASUREMENT",
                              f"MEASUREPERF failed:\nSTDOUT: .... "
                              f"{convertOutput(self.measure_output.stdout)[-500:]}\n"
                              f"STDERR:{convertOutput(self.measure_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False

        # change to top
        os.chdir(self.baseDir)
        self.updateStatus(1, "PERFORMANCE MEASUREMENT", f"MEASUREPERF succeeded: \n...\n"
                                                        f"{convertOutput(self.measure_output.stdout)[-500:]}")
        return True


    def parse_and_upload(self):

        # TODO: Move to new measurement script via self.measurement_output
        print("uploading", self.mdFlexDir)

        try:
            cpu = get_cpu_info()["brand"]
        except Exception as e:
            print(f"Couldn't determine CPU brand: {e}")
            cpu = "N/A"
        run_timestamp = datetime.utcnow()

        coarse_pattern = re.compile(r'Collected times for\s+{(.*)}\s:\s\[(.*)\]')
        config_pattern = re.compile(r'([^,]+): ([^,]+)')
        times_pattern = re.compile(r'(\d+)')
        config_runs = coarse_pattern.findall(self.measure_output.stdout.decode('utf-8'))

        for run in config_runs:

            db_entry = Config()
            db_entry.name = 'performance via single tuning phase'  # TODO: Keep name field?
            db_entry.date = run_timestamp
            db_entry.commitSHA = self.sha
            db_entry.commitMessage = self.repo.commit(self.sha).message
            db_entry.commitDate = self.repo.commit(self.sha).authored_datetime

            # Assumes tests were run on this system
            db_entry.system = cpu

            # Saving Setup used in perf script
            db_entry.setup = self.perfSetup

            # TODO: Decide if uniqueness is enforced (Change spare in model to False)
            # db_entry.unique = db_entry.name + db_entry.commitSHA + db_entry.system + str(db_entry.date)
            # try:
            #     db_entry.save()
            # except NotUniqueError:
            #     print("Exact Configuration for system and commit + date already saved!")
            #     continue

            # Filter all config parameters
            config = config_pattern.findall(run[0])

            # Parsing output
            try:
                # Parsing Config keys and values
                for pair in config:
                    key = pair[0].replace(' ', '')  # Replace spaces
                    key = 'dynamic_' + key  # Adding prefix to clearly show dynamic field creation in DB
                    quantity = pair[1].replace(' ', '')  # Replace spaces

                    try:  # Try converting to float if appropriate
                        quantity = float(quantity)
                    except ValueError:
                        pass

                    print(key, quantity)
                    db_entry[key] = quantity

                # Parsing times
                times = times_pattern.findall(run[1])
                times = [float(t) for t in times]
                db_entry.measurements = times
                db_entry.meanTime = np.mean(times)  # Mean running Time
                db_entry.minTime = np.min(times)  # Min running Time
            except Exception as e:
                print(f'Parsing of measurement failed {e}')
                self.updateStatus(-1, "PARSING", str(e))
                return False

            try:
                db_entry.save()
            except Exception as e:
                self.updateStatus(-1, "UPLOAD", str(e))
                return False

            print(db_entry)
            self.configs.append(db_entry)

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