from mongoDocuments import QueueObject
from checks import CheckFlow

if __name__ == '__main__':

    testSHA = "3114972f9816c81a5c8f74a13495c287861793b0"
    compareSHA = 'a3193c3dfc47afd976b1e1061bddb579b04c7ab9'

    c = CheckFlow(initRepo=False)
    c.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"
    c.auth.updateInstallID(2027548)
    compareUrl = c._createCheckRun(testSHA, "MANUAL COMPARE")

    q = QueueObject()
    q.compareUrl = compareUrl
    q.commitSHA = testSHA
    q.installID = 2027548
    q.compareOptions = {'0_BaseSHA': compareSHA}
    c.comparePerformance(q)