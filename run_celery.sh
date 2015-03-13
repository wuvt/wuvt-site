#!/bin/sh
celery -A wuvt.trackman.tasks.celery worker -B -l info
