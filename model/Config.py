import mongoengine as me

class Config(me.Document):

    name = me.StringField()
    date = me.DateTimeField()

    def __str__(self):
        output = f"Name: {self.name} Date: {self.date}"
        return output