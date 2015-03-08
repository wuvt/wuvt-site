from functools import wraps
from flask import abort, request
import netaddr
from wuvt import redis_conn

from wuvt import app

def local_only(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
            abort(403)
        else:
            return f(*args, **kwargs)
    return _wrapper

def dj_interact(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        redis_conn.set('dj_active', 'true')
        # logout/login must delete this dj_timeout
        expire = redis_conn.get('dj_timeout')
        if redis_conn.get('dj_timeout') is None:
            expire = app.config('DJ_TIMEOUT')

        redis_con.expire('dj_active', expire)

        return f(*args, **kwargs)
    return _wrapper
