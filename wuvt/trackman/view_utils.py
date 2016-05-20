from flask import current_app, request
from functools import wraps
from urlparse import urljoin
from .. import redis_conn


def dj_interact(f):
    @wraps(f)
    def dj_wrapper(*args, **kwargs):
        # Call in the function first incase it changes the timeout
        ret = f(*args, **kwargs)

        redis_conn.set('dj_active', 'true')
        # logout/login must delete this dj_timeout
        expire = redis_conn.get('dj_timeout')
        if redis_conn.get('dj_timeout') is None:
            expire = current_app.config['DJ_TIMEOUT']

        redis_conn.expire('dj_active', int(expire))

        return ret
    return dj_wrapper


def make_external(url):
    return urljoin(request.url_root, url)
