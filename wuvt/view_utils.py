from flask import abort, request
from functools import wraps
from wuvt import app
import netaddr


class IPAccessDeniedException(Exception):
    pass


def local_only(f):
    @wraps(f)
    def local_wrapper(*args, **kwargs):
        if request.remote_addr not in \
                netaddr.IPSet(app.config['INTERNAL_IPS']):
            raise IPAccessDeniedException()
        else:
            return f(*args, **kwargs)
    return local_wrapper
