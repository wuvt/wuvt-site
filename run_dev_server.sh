#!/bin/sh
gunicorn --worker-class=gevent -w 2 -t 14400 -b 127.0.0.1:8080 wuvt:app
