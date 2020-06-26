import mongoengine as me


class Setup(me.DynamicDocument):
    """
    Holding .yaml file used for performance testing runs
    """

    name = me.StringField(unique=False)  # Name of setup, can be kept and updated with changed file
    yaml = me.StringField(unique=False)  # Yaml String
    yamlHash = me.StringField(unique=True)  # MD5 hash to check for file uniqueness given a setup name
    active = me.BooleanField()  # Only one setup with the same name shall be active
    uploadDate = me.DateTimeField()

    def __str__(self):
        out = f'{self.name} {self.uploadDate}\n' \
              f'{self.yaml}'
        return out
