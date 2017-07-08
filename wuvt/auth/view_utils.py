from flask import current_app, request


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
