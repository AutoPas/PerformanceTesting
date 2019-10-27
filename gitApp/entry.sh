#!/bin/bash

# update PerformanceTesting repo
#git pull

# start uwsgi processes
uwsgi --ini uwsgi_config.ini

# keep alive, if no -t on docker run
sleep infinity
#/bin/bash