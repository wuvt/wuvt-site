from datetime import timedelta
from flask import current_app, request, session
from flask_restful import abort
from functools import wraps
from urlparse import urljoin
from .. import format_datetime
from .lib import perdelta, renew_dj_lease


def dj_interact(f):
    @wraps(f)
    def dj_wrapper(*args, **kwargs):
        # Call in the function first in case it changes the timeout
        ret = f(*args, **kwargs)
        renew_dj_lease()
        return ret
    return dj_wrapper


def make_external(url):
    return urljoin(request.url_root, url)


def list_archives(djset):
    if len(current_app.config['ARCHIVE_URL_FORMAT']) <= 0:
        return

    start = djset.dtstart.replace(minute=0, second=0, microsecond=0)

    if djset.dtend is None:
        end = start
    else:
        end = djset.dtend.replace(minute=0, second=0, microsecond=0)

    for loghour in perdelta(start, end, timedelta(hours=1)):
        yield (loghour.strftime(current_app.config['ARCHIVE_URL_FORMAT']),
               "-".join([format_datetime(loghour, "%Y-%m-%d %H:00"),
                         format_datetime(loghour + timedelta(hours=1),
                                         "%Y-%m-%d %H:00")]),)


def require_dj_session(f):
    @wraps(f)
    def require_dj_session_wrapper(*args, **kwargs):
        if session.get('dj_id', None) is None:
            abort(403, message="You must login as a DJ to use that feature.")
        else:
            return f(*args, **kwargs)
    return require_dj_session_wrapper
