import urllib.parse
from flask import current_app, redirect, request, session, url_for


def log_auth_success(method, user):
    return current_app.logger.warning(
        "wuvt-site: {method} user {user} logged in from {ip} using "
        "{ua}".format(
            method=method,
            user=user,
            ip=request.remote_addr,
            ua=request.user_agent))


def log_auth_failure(method, user):
    return current_app.logger.warning(
        "wuvt-site: Failed login for {method} user {user} from {ip} using "
        "{ua}".format(
            method=method,
            user=user,
            ip=request.remote_addr,
            ua=request.user_agent))


def is_safe_url(target):
    ref_url = urllib.parse.urlparse(request.host_url)
    test_url = urllib.parse.urlparse(
        urllib.parse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def redirect_back(endpoint, **values):
    target = session.pop('login_target', None)
    if target is not None and is_safe_url(target):
        return redirect(target)
    else:
        return redirect(url_for(endpoint, **values))
