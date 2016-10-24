from flask import abort, redirect, request, Response, url_for
from functools import wraps
from wuvt import app
import netaddr
import re
import socket
import unidecode
import urlparse

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_slug_pattern = re.compile(r"[^ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~:/?#\[\]@!$&'()*+,;=\-]*")


class IPAccessDeniedException(Exception):
    pass


def is_safe_url(target):
    ref_url = urlparse.urlparse(request.host_url)
    test_url = urlparse.urlparse(urlparse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def local_only(f):
    @wraps(f)
    def local_wrapper(*args, **kwargs):
        if request.remote_addr not in \
                netaddr.IPSet(app.config['INTERNAL_IPS']):
            raise IPAccessDeniedException()
        else:
            return f(*args, **kwargs)
    return local_wrapper


def ajax_only(f):
    """This decorator verifies that the X-Requested-With header is present.
    JQuery adds this header, and we can use it to prevent cross-origin requests
    because it cannot be added without a CORS preflight check."""

    @wraps(f)
    def ajax_only_wrapper(*args, **kwargs):
        if request.headers.get('X-Requested-With', '') != "":
            return f(*args, **kwargs)
        else:
            return abort(403)
    return ajax_only_wrapper


def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug and validates that it is an acceptable
    character set as per rfc3986"""
    if _slug_pattern.match(text) is None:
        return False

    # from http://flask.pocoo.org/snippets/5/
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode.unidecode(word).split())
    return unicode(delim.join(result))


def sse_response(channel):
    if request.headers.get('accept') == 'text/event-stream':
        u = urlparse.urlparse(app.config['REDIS_URL'])

        server = u.hostname
        if ':' not in server:
            # uwsgi-sse-offload requires that we resolve hostnames for it, but
            # unfortunately, we have to assume that the first entry in DNS
            # works. To do this, we use gethostbyname since Redis only listens
            # on IPv4 by default. You can work around this by specifying an
            # IPv6 address directly.
            server = socket.gethostbyname(server)
            #addrinfo = socket.getaddrinfo(u[0], port)
            #server = addrinfo[0][4][0]

        if u.port is not None:
            port = u.port
        else:
            port = 6379

        if u.password is not None:
            password = u.password
        else:
            password = ""

        return Response("", mimetype="text/event-stream", headers={
            'Cache-Control': "no-cache",
            'X-SSE-Offload': 'y',
            'X-SSE-Server': '{0}:{1}'.format(server, port),
            'X-SSE-Channel': channel,
            'X-SSE-Password': password,
        })
    else:
        abort(400)
