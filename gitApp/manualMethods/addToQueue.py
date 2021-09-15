from mongoDocuments import QueueObject
from checks import CheckFlow

if __name__ == '__main__':

    # me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
    #           password=os.environ['PASSWORD'])

    q = QueueObject()
    c = CheckFlow(initRepo=False)
    c.auth.updateInstallID(2027548)
    c.baseUrl = "https://api.github.com/repos/AutoPas/AutoPas"

    testSHA = '5c489e1630fb5091b23a40452133223cbf333aea'

    # TODO: Add mode without GitHub interaction and manual DB auth entry

    runUrl = c._createCheckRun(testSHA, 'MANUAL TEST RUN')

    q.runUrl = runUrl
    q.commitSHA = testSHA
    q.installID = 2027548
    q.running = False
    q.save()

