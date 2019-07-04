import mongoengine as me

class Config(me.Document):

    name = me.StringField()
    date = me.DateTimeField()

    # CONFIG FIELDS
    container = me.StringField()
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
    tuningInterval = me.IntField()
    tuningSamples = me.IntField()
    epsilon = me.FloatField()
    sigma = me.FloatField()

    def __str__(self):
        output = f"Name: {self.name} Date: {self.date}"
        return output