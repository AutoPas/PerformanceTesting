#!/bin/bash

# start uwsgi processes
uwsgi --ini uwsgi_config.ini

# keep alive
/bin/bash