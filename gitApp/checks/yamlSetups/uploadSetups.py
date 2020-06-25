from mongoDocuments.Setup import Setup

import mongoengine as me
import glob
import hashlib
from datetime import datetime


"""
Script used to upload all .yaml files in this directory, and if changes occur for same name files, update version number

"""
if __name__ == '__main__':

    # Connect to DB
    # TODO: use env or .config files for settings
    me.connect(url='localhost:30017', user='XXX', password='XXX')

    # TODO: check for same file content
    for filename in glob.glob('*.yaml'):
        print(filename)
        s = Setup()
        s.name = filename
        s.uploadDate = datetime.utcnow()

        with open(filename, 'r') as f:
            file = f.read()
            s.yaml = file
            s.yamlHash = hashlib.md5(file.encode('utf-8')).hexdigest()

        # Checking File uniqueness via yaml hash for a given name
        try:
            s.active = True
            s.save()
            print('New Setup saved\n')

            # Deactivating old versions
            for old in Setup.objects(name=s.name, yamlHash__ne=s.yamlHash):
                old.active = False
                old.save()

        except me.NotUniqueError:
            print('File already present\n')
            continue
