import mongoengine as me


class Setup(me.DynamicDocument):
    """
    Holding .yaml file used for performance testing runs
    """

    # Yaml File
    name = me.StringField()
    file = me.FileField()
    active = me.BooleanField()

    def __str__(self):
        out = f'{self.name}'
        return out