from mongoDocuments import Setup

import mongoengine as me


class Config(me.DynamicDocument):

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
    setup = me.ReferenceField(Setup)

    # Image Link
    perfImgurLink = me.URLField()
    compImgurLink = me.URLField()
    # Delete Hash
    perfDeleteHash = me.StringField()
    compDeleteHash = me.StringField()

    # Merged Commit
    mergedBaseSHA = me.StringField()

    # Failure field
    failure = me.StringField()

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


    @staticmethod
    def checkExisting(sha: str) -> bool:
        """
        Check if there already exists a config for a given sha
        Args:
            sha: SHA to check for

        Returns:
            bool: True if already existing Config
        """
        c = Config.objects(commitSHA=sha).order_by('-date').first()  # Get freshest config
        return c is not None
