import mongoengine as me
from models.Config import Config


class Results(me.DynamicDocument):
    """
    Holding results for a given config
    """
    config = me.ReferenceField(Config)

    # Measurements
    measurements = me.ListField()
    meanTime = me.FloatField()
    minTime = me.FloatField()

    def __str__(self):
        out = f'{str(self.config.commitSHA)}: {str(self.meanTime)}\n' \
              f'min: {self.minTime} mean: {self.meanTime}'
        return out

    meta = {
        'indexes': [
            'config',
        ]
    }
