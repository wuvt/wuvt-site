from functools import wraps
from flask import abort, request
import netaddr

from wuvt import app

def localonly(f):
    @wraps(f)
    def _wrapper(*args, **kwargs):
        if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
            abort(403)
        else:
            return f(*args, **kwargs)
    return _wrapper

