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

    # Image Link
    imgurLink = me.URLField()
    # Delete Hash
    deleteHash = me.StringField()

    def __str__(self):
        output = f"Name: {self.commitMessage}\n" \
                 f"SHA: {self.commitSHA}\n" \
                 f"Date: {self.date}\n" \
                 f"Systen: {self.system}\n" \
                 f"Setup: {self.setup}"
        return output

    # Setup indexing for faster querying
    meta = {
        'indexes': [
            'commitSHA'
        ]
    }
