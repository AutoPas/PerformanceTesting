from mongoDocuments import Checkpoint, Setup

import os
from datetime import datetime
import hashlib
import mongoengine as me
from datetime import datetime

"""
Script to upload matching checkpoint and setup combinations
"""

if __name__ == '__main__':
    # Connect to DB
    me.connect('performancedb', host='localhost:30017', username=os.environ['USERNAME'],
               password=os.environ['PASSWORD'])

    combinations = [
        {'setup': 'perfTest_homo_0_particles.yaml',
         'vtk': 'homo.vtk_0.vtk'},
        {'setup': 'perfTest_inhomo_0_particles.yaml',
         'vtk': 'inhomo.vtk_0.vtk'}
    ]

    for c in combinations:
        s = Setup()
        s.name = c['setup']
        s.uploadDate = datetime.utcnow()
        s.active = False
        with open(c['setup'], 'r') as f:
            file = f.read()
            s.yaml = file
            s.yamlHash = hashlib.sha256(file.encode('utf-8')).hexdigest()
        s.save()

        check = Checkpoint()
        check.name = c['setup']
        check.setup = s
        check.uploadDate = datetime.utcnow()
        check.active = True
        with open(c['vtk'], 'r') as f:
            vtk = f.read()
            check.vtk.put(vtk.encode('utf-8'))
        check.save()

        print(f'Saved {c}')
