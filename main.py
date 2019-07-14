#!/usr/bin/python3

"""@package PerformanceTesting

This code aims to automate and standardize performance testing for AutoPas.
The implementation should be able to be called by Jenkins whenever new commits are incoming.
To simplify setup and make the system more portable, it relies on MongoDB for storage.

"""

import time
import matplotlib
import mongoengine as me
import imp

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from model.Config import Config
from Repository import Repository

if __name__ == "__main__":

    start = time.time()

    # TODO: checkout process also part of python and not of Jenkins
    # TODO: does the target work
    # TODO: add commit hexsha / date / message
    # TODO: github bot
    # TODO: documentation
    # TODO: Requirements python
    # TODO: Add system config

    gitPath = "../AutoPas"

    # Database connection
    try:
        db = imp.load_source('db', 'database.config')
    except:
        print("database.config MISSING. Create file based on: database.config.example")
        exit(-1)

    print("DB settings: ", db.collection, db.user, db.server)#, db.password)

    me.connect(db.collection, username=db.user, password=db.password, host=("mongodb://"+db.server))

    print("Getting repo history")

    repo = Repository(gitPath, branch="master")

    print("Starting main tests")

    repo.testLatest()


    end = time.time()
    print("DURATION", end - start, "seconds")
