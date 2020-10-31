from . import Setup, Checkpoint
import mongoengine as me


class QueueObject(me.Document):

    commitSHA = me.StringField(sparse=False, unique=True, unique_with=['job'], required=True)
    running = me.BooleanField()  # If currently worked on
    installID = me.IntField()
    status = me.StringField()  # To save errors etc.

    # Urls to communicate with API
    runUrl = me.URLField()
    compareUrl = me.URLField()

    # Possible SHAs to compare with
    compareOptions = me.DictField()  # 0_BaseSHA, 1_ForkPoint, 2_LastCommon

    # TODO: Add optional Yaml overwrite here and check in test routine
    # TODO: Add optional checkpoint overwrite here and check in test routine
    # Custom Job Settings
    # Job name
    job = me.StringField(default='default-job', required=True)
    customYaml = me.ReferenceField(Setup, required=False)
    customCheckpoint = me.ReferenceField(Checkpoint, required=False)
    jobuser = me.StringField(default='auto-generated', required=True)

    def __str__(self):
        output = f"Name: {self.job} | {self.commitSHA} Running: {self.running}"
        return output

    meta = {
        'indexes': [
            'commitSHA'
        ]
    }
