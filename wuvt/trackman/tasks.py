from datetime import timedelta

from celery.decorators import periodic_task

from wuvt.celeryconfig import make_celery
from wuvt import redis_conn
from wuvt import app
from wuvt.trackman.lib import logout_recent, enable_automation
from wuvt.trackman.models import DJ, DJSet

celery = make_celery(app)

@periodic_task(run_every=timedelta(minutes=1))
def autologout_check():
    active = redis_conn.get('dj_active')
    automation = redis_conn.get('automation_enabled')
    # active is None if dj_active has expired (no activity)
    if active is None:
        if automation is None:
            # This should never happen
            pass
        elif automation == "true":
            # automation is running, carry on
            # if automation is enabled then logout_recent was already called
            pass
        else:
            # Automation is not running, end djset if exists and start automation
            logout_recent()
            enable_automation()



