import mongoengine as me
from mongoDocuments.Setup import Setup


if __name__ == '__main__':

    # Connect to DB
    me.connect(url='localhost:30017', user='XXX', password='XXX')
