from collections import Mapping
from datetime import timedelta
from flask import current_app, request, session
from flask_restful import abort, Resource
from functools import wraps
from urllib.parse import urljoin
from .lib import perdelta, renew_dj_lease, check_onair
from ..view_utils import local_only, sse_response


def dj_interact(f):
    @wraps(f)
    def dj_wrapper(*args, **kwargs):
        # Call in the function first in case it changes the timeout
        ret = f(*args, **kwargs)

        if check_onair(session.get('djset_id', None)):
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
               loghour,
               loghour + timedelta(hours=1))


def require_dj_session(f):
    @wraps(f)
    def require_dj_session_wrapper(*args, **kwargs):
        if session.get('dj_id', None) is None:
            abort(403, message="You must login as a DJ to use that feature.")
        else:
            return f(*args, **kwargs)
    return require_dj_session_wrapper


def require_onair(f):
    @wraps(f)
    def require_onair_wrapper(*args, **kwargs):
        if not check_onair(session.get('djset_id', None)):
            abort(403, message="You must be on-air to use that feature.",
                  onair=False)
        else:
            return f(*args, **kwargs)
    return require_onair_wrapper


def call_api(resource, method, *args, **kwargs):
    if not isinstance(resource, Resource):
        resource = resource()

    # Taken from flask
    #noinspection PyUnresolvedReferences
    meth = getattr(resource, method.lower(), None)
    if meth is None and method == 'HEAD':
        meth = getattr(resource, 'get', None)
    assert meth is not None, 'Unimplemented method %r' % method

    if isinstance(resource.method_decorators, Mapping):
        decorators = resource.method_decorators.get(method.lower(), [])
    else:
        decorators = resource.method_decorators

    for decorator in decorators:
        meth = decorator(meth)

    # The instance is not included in this call to match flask_restful's
    # behavior. If that ever changes, this should be updated.
    # See https://github.com/flask-restful/flask-restful/issues/585
    return meth(*args, **kwargs)


def tracklog_serialize(t):
    """Basic TrackLog serializer for deprecated API version 0."""
    return {
        'tracklog_id': t['id'],
        'track_id': t['track_id'],
        'played': t['played'],
        'djset': t['djset_id'],
        'dj_id': t['dj_id'],
        'request': t['request'],
        'vinyl': t['vinyl'],
        'new': t['new'],
        'listeners': t['listeners'],
    }


def tracklog_full_serialize(t):
    """Full TrackLog serializer for deprecated API version 0."""
    track = t['track']
    track['added'] = str(track['added'])
    return {
        'tracklog_id': t['id'],
        'track_id': t['track_id'],
        'track': track,
        'played': t['played'],
        'djset': t['djset_id'],
        'dj_id': t['dj_id'],
        'dj_visible': t['dj']['visible'],
        'dj': t['dj']['airname'],
        'request': t['request'],
        'vinyl': t['vinyl'],
        'new': t['new'],
        'rotation_id': t['rotation_id'],
        'listeners': t['listeners'],
    }
