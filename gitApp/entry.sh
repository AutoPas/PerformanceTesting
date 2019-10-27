#!/bin/bash

# update PerformanceTesting repo
#git pull

# start uwsgi processes
uwsgi --ini uwsgi_config.ini

# keep alive, if no -t on docker run
/bin/bash
watch 'tail ../log/gitApp.log'
#/bin/bash