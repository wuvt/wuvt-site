from flask import redirect, request, url_for
from functools import wraps
from wuvt import app
import netaddr
import re
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
