# Portions of this file are taken from Flask-Login
# Flask-Login is Copyright (c) 2011 Matthew Frasier

from flask import current_app, has_request_context, request, \
    _request_ctx_stack
from functools import wraps
from werkzeug.local import LocalProxy


current_user = LocalProxy(lambda: _get_user())
current_user_roles = LocalProxy(lambda: _get_user_roles())


def _get_user():
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
        current_app.auth_manager.load_user_session()

    return getattr(_request_ctx_stack.top, 'user', None)


def _get_user_roles():
    if has_request_context() and \
            not hasattr(_request_ctx_stack.top, 'user_roles'):
        current_app.auth_manager.load_user_session()

    return getattr(_request_ctx_stack.top, 'user_roles', None)


def _user_context_processor():
    return dict(current_user=_get_user())


def _user_roles_context_processor():
    return dict(current_user_roles=_get_user_roles())


def login_required(f):
    @wraps(f)
    def login_required_wrapper(*args, **kwargs):
        if request.method in current_app.auth_manager.exempt_methods:
            return f(*args, **kwargs)
        elif not current_user.is_authenticated:
            return current_app.auth_manager.unauthorized()
        return f(*args, **kwargs)
    return login_required_wrapper


def check_access(*roles):
    return current_app.auth_manager.check_access(*roles)


def login_user(user, roles):
    return current_app.auth_manager.login_user(user, roles)


def logout_user():
    return current_app.auth_manager.logout_user()


def get_user_roles(user, user_groups=None):
    return current_app.auth_manager.get_user_roles(user, user_groups)
