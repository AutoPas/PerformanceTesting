from mongoDocuments import Config, Setup

import mongoengine as me
import os

if __name__ == '__main__':
    me.connect('performancedb', host=os.environ['MONGOHOST'], username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])

    setups = Config.objects().distinct(field='setup')
    print(setups)

    for i, s in enumerate(setups):

        setup = Setup()

        setup.name = f'DummySetup {i}'
        setup.yamlHash = f'{i}'
        setup.active = False
        setup.id = s.id

        setup.save()

        print(setup)