from mongoDocuments import QueueObject
from checks import CheckFlow
import time


if __name__ == '__main__':

    testSHA = "1baed181eaf3e698b8e7061a8ac8d0607844d39f"
    compareSHA = 'a3193c3dfc47afd976b1e1061bddb579b04c7ab9'

    c = CheckFlow(initRepo=False)
    c.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"
    c.auth.updateInstallID(2027548)
    compareUrl = c._createCheckRun(testSHA, f"MANUAL COMPARE {time.asctime()}")

    q = QueueObject()
    q.compareUrl = compareUrl
    q.commitSHA = testSHA
    q.installID = 2027548
    q.compareOptions = {'0_BaseSHA': compareSHA}
    c.comparePerformance(q)
