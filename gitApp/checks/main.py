#!/usr/bin/python3

"""@package PerformanceTesting

This code aims to automate and standardize performance testing for AutoPas.
The implementation should be able to be called by Jenkins whenever new commits are incoming.
To simplify setup and make the system more portable, it relies on MongoDB for storage.

"""

import time
import mongoengine as me
import imp
import argparse
import sys, os

from gitApp.checks.Repository import Repository

if __name__ == "__main__":

    start = time.time()

    # TODO: checkout process in Jenkins
    # TODO: github bot with docker image
    # TODO: documentation
    # TODO: Requirements python
    # TODO: Add Comparison to previous commit
    # TODO: Check Variance
    # TODO: get SLURM conf to run on mpp3_batch from KNL_LOGIN
    # TODO: Visualize only differences with large change
    # TODO: ls-1 alpha wieder einsetzen

    gitPath = "../AutoPas"

    parser = argparse.ArgumentParser(description="Build, Measure performance and upload data to MongoDB for AutoPas")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--newest", action="store_true", help="run tests for only the latest commit")
    g.add_argument("--last", metavar="N", type=int, help="run on last N commits")
    g.add_argument("--sha", metavar="SHA", type=str, help="SHA to test")
    parser.add_argument("--config", metavar="path", help="location of db.config file, if not default")
    parser.add_argument("--threads", metavar="num", type=int, help="numper of OpenMP threads allowed (default=4)", default=4)
    args = parser.parse_args()

    THREADS = args.threads
    os.environ["OMP_NUM_THREADS"] = str(THREADS)
    print("Running Threads:", THREADS)

    if len(sys.argv) < 2:
        print("NO FLAGS SET")
        parser.print_help()
        exit(-1)

    if args.config is not None:
        dbPath = args.config
    else:
        dbPath = "database.config"

    # Database connection
    try:
        db = imp.load_source('db', dbPath)
    except:
        print("database.config MISSING. Create file based on: database.config.example")
        exit(-1)

    print("DB settings: ", db.collection, db.user, db.server)#, db.password)

    me.connect(db.collection, username=db.user, password=db.password, host=("mongodb://"+db.server))

    print("Getting repo history")

    repo = Repository(gitPath, branch="master")

    print("Starting main tests")

    if args.newest:
        print("Testing most recent commit")
        repo.testNewest()
    elif args.sha is not None:
        print("Testing SHA", args.sha)
        repo.testSHA(args.sha)
    elif args.last is not None:
        print("Testing last", args.last, "commits")
        repo.testLast(args.last)

    end = time.time()
    print("DURATION", end - start, "seconds")
