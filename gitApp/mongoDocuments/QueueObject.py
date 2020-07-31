import mongoengine as me


class QueueObject(me.Document):

    commitSHA = me.StringField(sparse=False, unique=True)
    running = me.BooleanField()  # If currently worked on
    installID = me.IntField()
    status = me.StringField()  # To save errors etc.

    # Urls to communicate with API
    runUrl = me.URLField()
    compareUrl = me.URLField()

    # Possible SHAs to compare with
    compareOptions = me.DictField()  # 0_BaseSHA, 1_ForkPoint, 2_LastCommon

    def __str__(self):
        output = f"Name: {self.commitSHA} Running: {self.running}"
        return output

    meta = {
        'indexes': [
            'commitSHA'
        ]
    }
