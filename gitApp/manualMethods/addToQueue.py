from mongoDocuments import QueueObject
from checks import CheckFlow

if __name__ == '__main__':

    # me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
    #           password=os.environ['PASSWORD'])

    q = QueueObject()
    c = CheckFlow(initRepo=False)
    c.auth.updateInstallID(2027548)
    c.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"

    testSHA = 'a3193c3dfc47afd976b1e1061bddb579b04c7ab9'

    # TODO: Add mode without GitHub interaction and manual DB auth entry

    runUrl = c._createCheckRun(testSHA, 'MANUAL TEST RUN')

    q.runUrl = runUrl
    q.commitSHA = testSHA
    q.installID = 2027548
    q.running = False
    q.save()

