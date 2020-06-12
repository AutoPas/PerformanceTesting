from mongoDocuments.QueueObject import QueueObject
from checks.CheckFlow import CheckFlow
import sys


class Worker:
    """
    Worker class running all performance measurements currently in queue
    """

    def __init__(self):
        self.checkflow = CheckFlow(initRepo=True)  # Handles Repo, DB and Auth calls


    def checkQueue(self):
        """
        Checks Queue for remaining tests recursively
        :return: True if queue is
        """
        nextUp: QueueObject
        queue = QueueObject.objects(running=False)
        if len(queue) != 0:
            nextUp = queue.order_by('_id').first()  # Should work through queue by FIFO
            del queue
        else:
            return True

        nextUp.running = True
        nextUp.save()  # Update status to running

        sha = nextUp.commitSHA

        try:
            self.checkflow.auth.updateInstallID(nextUp.installID)
            if self.checkflow.runCheck(sha, nextUp.runUrl):  # Run perf measurements
                if nextUp.compareUrl is not None:
                    self.checkflow.comparePerformance(sha, nextUp.compareUrl)  # Run comparison
            nextUp.status = "completed"
            nextUp.save()
            nextUp.delete()  # Bit unnecessary to change status earlier, but hey
        except Exception as exc:
            nextUp.status = str(exc)
            nextUp.save()

        # Recursion to check for remaining queue
        if self.checkQueue():
            print('Queue is done')


### RUNNING IN STANDALONE MODE IN POD ###
if __name__ == '__main__':

    try:
        w = Worker()
        w.checkQueue()
        sys.exit(0)
    except Exception as e:
        print('\n\n\n\n WORKER FAILED \n\n\n\n')
        print(e)
        print('\n\n\n\n WORKER FAILED \n\n\n\n')
        sys.exit(-1)
