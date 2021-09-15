from mongoDocuments import Config
from mongoDocuments import Result
from mongoDocuments import Setup
from mongoDocuments import Checkpoint
from hook.helper import convertOutput, get_dyn_keys, generate_label_table
from checks import ImgurUploader

from git import Repo
import os
import io
import shutil
from subprocess import run, PIPE
from datetime import datetime
import re
from cpuinfo import get_cpu_info
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import mongoengine as me
from shutil import copyfile

# Switch for GUI
matplotlib.use("Agg")
# matplotlib.use("TkAgg")


class Commit:
    baseDir = ""
    buildDir = "perfBuild"
    mdFlexDir = ""

    def __init__(self, repo: Repo, sha: str, baseSHA: str = None):
        # Reset Dir to specified commit
        repo.head.reset(sha, index=True, working_tree=True)
        self.message = repo.head.commit.message
        self.sha = sha
        self.repo = repo
        print("New commit:", self.sha, self.message, "\n")
        self.baseDir = repo.git_dir.strip(".git")
        self.buildDir = os.path.join(self.baseDir, Commit.buildDir)
        self.mdFlexDir = os.path.join(self.buildDir, "examples/md-flexible")
        print("BASE DIR:", self.baseDir)
        print("BUILD DIR:", self.buildDir)
        print("MDFLEX DIR:", self.mdFlexDir)
        # Status codes, headers and messages
        self.codes = []
        self.headers = []
        self.statusMessages = []
        self.images = []
        self.measure_output = None
        self.perfSetup = None
        self.baseSHA = baseSHA

    def updateStatus(self, code, header, message, image=None):
        self.codes.append(code)
        self.headers.append(header)
        self.statusMessages.append(message)
        if image is not None:
            self.images.append(image)

    def build(self):

        print("BUILD/MD-FLEX DIR: ", self.buildDir, self.mdFlexDir)

        os.chdir(self.baseDir)
        run(['git', 'clean', '-dxf'])  # Force clean all untracked and/or ignored files
        # remove old buildDir if present
        shutil.rmtree(self.buildDir, ignore_errors=True)
        try:
            os.mkdir(self.buildDir)
        except FileExistsError:
            print("build folder existed already. RESET FOR PRODUCTION")
        os.chdir(self.buildDir)

        # run cmake
        print("Running CMAKE")
        # TODO: log and test change to clang
        os.environ['CC'] = 'clang-11'
        os.environ['CXX'] = 'clang++-11'
        cmake_output = run(["cmake", "-DAUTOPAS_OPENMP=ON", ".."], stdout=PIPE, stderr=PIPE)
        returncode = cmake_output.returncode
        if returncode != 0:
            print("CMAKE failed with return code", returncode)
            self.updateStatus(-1, "CMAKE", f"CMAKE failed:\n{convertOutput(cmake_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False, convertOutput(cmake_output.stderr)

        self.updateStatus(1, "CMAKE", f"CMAKE succeeded:\n{convertOutput(cmake_output.stdout)[-800:]}")

        # run make
        print("Running MAKE")

        THREADS = os.environ["OMP_NUM_THREADS"]
        make_output = run(["make", "md-flexible", "-j", THREADS], stdout=PIPE, stderr=PIPE)
        make_returncode = make_output.returncode
        if make_returncode != 0:
            print("MAKE failed with return code", make_returncode)
            self.updateStatus(-1, "MAKE", f"MAKE failed:\n{convertOutput(make_output.stderr)}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False, convertOutput(make_output.stderr)

        self.updateStatus(1, "MAKE", f"MAKE succeeded:\n{convertOutput(make_output.stdout)[-800:]}")

        # change back to top level directory
        os.chdir(self.baseDir)
        self.updateStatus(1, "BUILD", f"CMAKE+MAKE passed")
        return True, 'Build Succeeded'

    def measure(self, setup: Setup):

        # oldMain.py path
        # issues with using the __file__ method when deploying via uwsgi
        # mainPath = os.path.abspath(os.path.dirname(__file__))
        mainPath = os.path.join(self.baseDir, "..", "PerformanceTesting/gitApp/checks")
        print("measure_perf directory:", mainPath)

        # change to md-flexible folder
        os.chdir(self.mdFlexDir)

        # Setting yaml file for this run
        self.perfSetup = setup
        yamlFile = 'perfConfig.yaml'
        with open(yamlFile, 'w') as f:
            f.write(self.perfSetup.yaml)

        # Running one tuning session with yaml setup
        self.measure_output = run(['./md-flexible',
                                   '--log-level', 'debug',
                                   '--yaml-filename', f'{yamlFile}'],
                                  stdout=PIPE, stderr=PIPE)


        if self.measure_output.returncode != 0:
            print("MEASUREPERF failed with return code", self.measure_output.returncode)
            self.updateStatus(-1,
                              "PERFORMANCE MEASUREMENT",
                              f"MEASUREPERF failed:\nSTDOUT: .... "
                              f"{convertOutput(self.measure_output.stdout)[-500:]}\n"
                              f"STDERR:{convertOutput(self.measure_output.stderr)}\n"
                              f"Setup: {self.perfSetup.name}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False, convertOutput(self.measure_output.stderr)

        # change to top
        os.chdir(self.baseDir)
        self.updateStatus(1, "PERFORMANCE MEASUREMENT", f"MEASUREPERF succeeded: \n...\n"
                                                        f"{convertOutput(self.measure_output.stdout)[-500:]}\n"
                                                        f"{self.perfSetup.name}")
        return True, 'Measure Succeeded'


    def measureCheckpoint(self, checkpoint: Checkpoint, setup: Setup = None):

        # oldMain.py path
        # issues with using the __file__ method when deploying via uwsgi
        # mainPath = os.path.abspath(os.path.dirname(__file__))
        mainPath = os.path.join(self.baseDir, "..", "PerformanceTesting/gitApp/checks")
        print("measure_perf directory:", mainPath)

        # change to md-flexible folder
        os.chdir(self.mdFlexDir)

        # Setting yaml file for this run
        if setup is None:
            self.perfSetup = checkpoint.setup
        else:
            self.perfSetup = setup
        yamlFile = 'perfConfig.yaml'
        with open(yamlFile, 'w') as f:
            f.write(self.perfSetup.yaml)

        # Setting checkpoint file for this run
        self.checkpoint = checkpoint
        checkpointFile = 'checkpoint.vtk'
        with open(checkpointFile, 'w') as f:
            f.write(self.checkpoint.vtk.read().decode('utf-8'))

        # Running one tuning session with yaml setup
        self.measure_output = run(['./md-flexible',
                                   '--log-level', 'debug',
                                   '--yaml-filename', f'{yamlFile}',
                                   '--checkpoint', f'{checkpointFile}'],
                                  stdout=PIPE, stderr=PIPE)


        """
        DEBUG OUTPUT OF BINARIES AND LOGS
        debug_dir = '/home'
        try:
            # TODO: SPECIAL DEBUG BULLSHIT
            with open(f'{dir}/{self.sha}.log', 'w') as f:
                f.write(self.measure_output.stdout.decode('utf-8'))

            copyfile(os.path.join(self.mdFlexDir, 'md-flexible'), f'{dir}/md-flex_{self.sha}')
        except Exception as e:
            print(e)
        """

        if self.measure_output.returncode != 0:
            print("MEASUREPERF failed with return code", self.measure_output.returncode)
            self.updateStatus(-1,
                              "PERFORMANCE MEASUREMENT with Checkpoint",
                              f"MEASUREPERF failed:\nSTDOUT: .... "
                              f"{convertOutput(self.measure_output.stdout)[-500:]}\n"
                              f"STDERR:{convertOutput(self.measure_output.stderr)}\n"
                              f"Setup: {self.perfSetup.name}")
            # change back to top level directory
            os.chdir(self.baseDir)
            return False, convertOutput(self.measure_output.stderr)

        # change to top
        os.chdir(self.baseDir)
        self.updateStatus(1, "PERFORMANCE MEASUREMENT", f"MEASUREPERF succeeded: \n...\n"
                                                        f"{convertOutput(self.measure_output.stdout)[-500:]}\n"
                                                        f"{self.perfSetup.name}")
        return True, 'Measure Succeeded'


    def parse_and_upload(self):

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

        db_entry = Config()
        db_entry.name = 'performance via single tuning phase'  # TODO: Keep name field?
        db_entry.date = run_timestamp
        db_entry.commitSHA = self.sha
        db_entry.commitMessage = self.repo.commit(self.sha).message
        db_entry.commitDate = self.repo.commit(self.sha).authored_datetime
        db_entry.mergedBaseSHA = self.baseSHA

        # Assumes tests were run on this system
        db_entry.system = cpu

        # Saving Setup used in perf script
        db_entry.setup = self.perfSetup

        # TODO: Decide if uniqueness is enforced (Change spare in models to False)
        # db_entry.unique = db_entry.name + db_entry.commitSHA + db_entry.system + str(db_entry.date)
        # try:
        #     db_entry.save()
        # except NotUniqueError:
        #     print("Exact Configuration for system and commit + date already saved!")
        #     continue
        try:
            db_entry.save()
        except Exception as e:
            self.updateStatus(-1, "UPLOAD", str(e))
            return False, f'Upload of config to DB failed {e}'
        print(db_entry)

        for run in config_runs:

            results = Result()
            results.config = db_entry

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
                    results[key] = quantity

                # Parsing times
                times = times_pattern.findall(run[1])
                times = [float(t) for t in times]
                results.measurements = times
                results.meanTime = np.mean(times)  # Mean running Time
                results.minTime = np.min(times)  # Min running Time
            except Exception as e:
                print(f'Parsing of measurement failed {e}')
                self.updateStatus(-1, "PARSING", str(e))
                return False, f'Parsing failed with {e}'

            try:
                results.save()
            except Exception as e:
                self.updateStatus(-1, "UPLOAD", str(e))
                return False, f'Upload of Result failed with {e}'
            print(results)

        os.chdir(self.baseDir)
        self.updateStatus(1, "UPLOAD", "RESULT UPLOAD succeeded\n")
        return True, 'Upload succeeded'

    def save_failed_config(self, failure: str):
        """
        Saving failed configs to not re-run them again
        :param failure: Failure Mode
        :return:
        """
        db_entry = Config()
        db_entry.name = 'Performance Testing Failed'  # TODO: Keep name field?
        db_entry.date = datetime.utcnow()
        db_entry.commitSHA = self.sha
        db_entry.commitMessage = self.repo.commit(self.sha).message
        db_entry.commitDate = self.repo.commit(self.sha).authored_datetime
        # Saving Setup used in perf script
        if self.perfSetup is not None:
            db_entry.setup = self.perfSetup
        db_entry.failure = failure
        db_entry.save()

    def generatePlot(self):
        """
        Quick overview plot for commit
        :return:
        """

        try:

            imgur = ImgurUploader()

            confs = Config.objects(commitSHA=self.sha)
            images = []

            # Multiple Plots if more than one config was run
            conf: Config
            for conf in confs:
                results = Result.objects(config=conf)

                means = np.array([r.meanTime for r in results])
                mins = np.array([r.minTime for r in results])

                header, all_keys = get_dyn_keys(results)
                header_string = r'$\bf{' + header + '}$'
                labels = generate_label_table(results, all_keys)

                # Sort by minimum time
                sort_keys = np.argsort(mins)[::-1]
                sorted_means = means[sort_keys]
                sorted_mins = mins[sort_keys]
                sorted_labels = labels[sort_keys]
                sorted_labels = np.append(sorted_labels, header_string)

                fig = plt.figure(figsize=(15, len(means) / 4))
                plt.gca().set_title(conf)
                plt.barh(np.arange(len(means)), sorted_means, label='mean')
                plt.barh(np.arange(len(means)), sorted_mins, label='min')
                plt.legend()
                plt.xlabel('nanoseconds')
                plt.xscale('log')
                plt.yticks(np.arange(len(sorted_labels)), sorted_labels)
                plt.grid(which='both', axis='x')
                plt.tight_layout()

                # Upload figure
                buf = io.BytesIO()
                fig.savefig(buf, format='png')
                buf.seek(0)
                link, hash = imgur.upload(buf.read())
                conf.perfImgurLink = link
                conf.perfDeleteHash = hash
                conf.save()

                self.updateStatus(1, "PLOTTING", "PLOTTING succeeded\n", link)

        except Exception as e:
            self.updateStatus(-1, "PLOTTING", f"PLOTTING failed\n{e}")

        os.chdir(self.baseDir)
        return True


if __name__ == '__main__':
    me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])
    c = Commit(Repo('../../../AutoPas'), '64a5b092bc32a7b01e19be4091a79148fecb04e7')
    c.generatePlot()
