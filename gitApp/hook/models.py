from django.db import models


# Create your models here.
class NodeLock(models.Model):
    """
    lock preventing multiple uwsgi workers to start testing on the same node
    """

    node = models.CharField(max_length=256, unique=True)
    isLocked = models.BooleanField()

    def __str__(self):
        return self.node