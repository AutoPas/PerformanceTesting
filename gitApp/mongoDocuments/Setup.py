import mongoengine as me


class Setup(me.DynamicDocument):
    """
    Holding .yaml file used for performance testing runs
    """

    # Yaml File
    name = me.StringField(unique=False)
    version = me.IntField(unique=True)
    file = me.FileField(unique=True)
    active = me.BooleanField()

    def __str__(self):
        out = f'{self.name}'
        return out