from mongoDocuments import QueueObject
from checks import CheckFlow

import time
import os
from subprocess import run, PIPE
import re


def addToQueue(c: CheckFlow, sha: str):
    # TODO: Add mode without GitHub interaction and manual DB auth entry
    #runUrl = c._createCheckRun(sha, f'MANUAL TEST RUN {time.asctime()}')

    q = QueueObject()
    #q.runUrl = runUrl
    q.commitSHA = sha
    #q.installID = 2027548
    q.running = False
    q.save()


if __name__ == '__main__':

    # me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
    #           password=os.environ['PASSWORD'])

    c = CheckFlow(initRepo=True)
    #c.auth.updateInstallID(2027548)
    #c.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"

    # Change to Repo
    os.chdir(c.repo.repo.git_dir.strip('.git'))

    # Get all merge commits
    startData = '2019-01-01'
    endDate = '2020-09-01'
    path = 'src/autopas/molecularDynamics/LJFunctor*'
    commitLog = run(['git', 'log',
                     '--merges',
                     '--first-parent', 'master',
                     '--since', startData,
                     '--until', endDate,
                     path],
                    stdout=PIPE, encoding='utf-8')

    pattern = re.compile('commit (\S+)\\n')
    matches = pattern.findall(commitLog.stdout)

    for m in matches:
        addToQueue(c, sha=m)
