import mongoengine as me


class Config(me.Document):

    name = me.StringField()
    date = me.DateTimeField()
    commitSHA = me.StringField()
    commitDate = me.DateTimeField()
    commitMessage = me.StringField()
    # Assumes Tests were run on same system as the files reside
    system = me.StringField()

    # Unique combination of Name + SHA + System + Date to prevent reupload
    # sparse allows for empty unique key
    unique = me.StringField(unique=True, sparse=True)

    # Test setup
    setup = me.DictField()

    def __str__(self):
        output = f"Name: {self.name} {self.commitSHA} Date: {self.date}"
        return output
