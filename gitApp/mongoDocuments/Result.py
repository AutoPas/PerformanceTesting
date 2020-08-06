import mongoengine as me
from mongoDocuments import Config


class Result(me.DynamicDocument):
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
            '#config',
            # TODO: Watch out for changes in keywords and update these indices for performance (not really helping though)
            'dynamic_Container',
            'dynamic_CellSizeFactor',
            'dynamic_DataLayout',
            'dynamic_Traversal',
            'dynamic_Newton3',
            'dynamic_LoadEstimator',
            {
                'fields': ['config', 'dynamic_Container'],
                'name': 'compound0'
            },
            {
                'fields': ['config', 'dynamic_Container', 'dynamic_DataLayout'],
                'name': 'compound1'
            },
            {
                'fields': ['config', 'dynamic_Container', 'dynamic_DataLayout', 'dynamic_Traversal'],
                'name': 'compound2'
            },
            {
                'fields': ['config', 'dynamic_Container', 'dynamic_DataLayout', 'dynamic_Traversal', 'dynamic_Newton3'],
                'name': 'compound3'
            },
            {
                'fields': ['config', 'dynamic_Container', 'dynamic_DataLayout', 'dynamic_Traversal', 'dynamic_Newton3', 'dynamic_CellSizeFactor'],
                'name': 'compound4'
            },
            {
                'fields': ['config', 'dynamic_Container', 'dynamic_DataLayout', 'dynamic_Traversal', 'dynamic_Newton3', 'dynamic_CellSizeFactor', 'dynamic_LoadEstimator'],
                'name': 'compound5'
            }
        ]
    }
