#!/bin/bash

# update PerformanceTesting repo
#git pull

# start uwsgi processes
uwsgi --ini uwsgi_config.ini

# keep alive, if no -t on docker run
watch 'tail ../log/gitApp.log'
#/bin/bash