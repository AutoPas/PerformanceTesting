import mongoengine as me
from mongoDocuments.Setup import Setup


"""
Script used to upload all .yaml files in this directory, and if changes occur for same name files, update version number

"""
if __name__ == '__main__':

    # Connect to DB
    me.connect(url='localhost:30017', user='XXX', password='XXX')

    # TODO: check for same file content

    # TOOD: if not same, but same name, update version number, deactivate last version
