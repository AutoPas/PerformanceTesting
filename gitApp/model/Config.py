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
    setup = me.DictField()

    # Instead using dynamic fields, so don't have to manually add them here if output of measure_Perf changes
    '''

    # CONFIG FIELDS
    container = me.StringField()
    # Verlet
    rebuildFreq = me.FloatField()
    skinRadius = me.FloatField()
    # General
    layout = me.StringField()
    functor = me.StringField()
    newton = me.StringField()
    cutoff = me.StringField()
    cellSizeFactor = me.StringField()
    generator = me.StringField()
    boxLength = me.FloatField()
    particles = me.ListField()
    traversal = me.StringField()
    iterations = me.ListField()
    tuningStrategy = me.StringField()
    tuningInterval = me.IntField()
    tuningSamples = me.IntField()
    tuningMaxEvidence = me.IntField()
    epsilon = me.FloatField()
    sigma = me.FloatField()

    '''

    # Measurements
    measurements = me.ListField()
    meanTime = me.FloatField()
    minTime = me.FloatField()

    def __str__(self):
        output = f"Name: {self.name} Date: {self.date}"
        return output
