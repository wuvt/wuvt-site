import base64
import datetime
import os
from flask import abort, flash, json, make_response, redirect, request, \
    session, url_for, _request_ctx_stack
from flask_oidc import OpenIDConnect
from functools import wraps

from .models import User
from .mixins import AnonymousUserMixin
from .blueprint import bp
from .utils import current_user, current_user_roles, \
    _user_context_processor, _user_roles_context_processor


class AuthManager(object):
    def __init__(self, app=None, redis_conn=None):
        self.bp = bp
        self.all_roles = set()

        self.exempt_methods = set(['OPTIONS'])
        self.login_message = u"Please login to access this page."
        self.login_message_category = 'message'

        if redis_conn is not None:
            self.redis_conn = redis_conn
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        from . import views

        self.app = app

        app.auth_manager = self
        app.config.setdefault('AUTH_METHOD', 'local')
        app.config.setdefault('AUTH_SUPERADMINS', ['admin'])
        app.config.setdefault('AUTH_ROLE_GROUPS', {
            'admin': ['webmasters'],
            'content': ['webmasters'],
            'business': ['business'],
            'library': ['librarians'],
            'missioncontrol': ['missioncontrol'],
        })

        app.context_processor(_user_context_processor)
        app.context_processor(_user_roles_context_processor)

        if app.config['AUTH_METHOD'] == 'oidc':
            import flask_oidc
            flask_oidc.logger = app.logger

            with app.app_context():
                app.config.setdefault('OIDC_SCOPES',
                                      ['openid', 'profile', 'email'])
                app.config.update({
                    'OIDC_RESOURCE_SERVER_ONLY': True,
                    'OIDC_RESOURCE_CHECK_AUD': True,
                })

                app.before_request(self._oidc_before_request)

            self.oidc = OpenIDConnect(app)

    def _oidc_before_request(self):
        if self.app.config['OVERWRITE_REDIRECT_URI'] is False:
            self.app.config['OVERWRITE_REDIRECT_URI'] = url_for(
                'auth.oidc_callback', _external=True)

    def generate_session_id(self):
        return base64.urlsafe_b64encode(os.urandom(64))

    def load_user_session(self):
        ctx = _request_ctx_stack.top

        session_id = session.get('user_session_id')
        if session_id is None:
            ctx.user = AnonymousUserMixin()
            ctx.user_roles = set([])
        else:
            raw_data = self.redis_conn.get('user_session:{}'.format(
                session_id))
            try:
                data = json.loads(raw_data)
            except (TypeError, ValueError):
                ctx.user = AnonymousUserMixin()
                ctx.user_roles = set([])
            else:
                ctx.user = self.load_user(data['user_id'])
                ctx.user_roles = set(data['roles'])

    def load_user(self, user_id):
        return User.query.get(user_id)

    def unauthorized(self):
        flash(self.login_message, self.login_message_category)
        return redirect(url_for('auth.login', next=request.url))

    def check_access(self, *roles):
        roles = set(roles)
        self.all_roles.update(roles)

        def access_decorator(f):
            @wraps(f)
            def access_wrapper(*args, **kwargs):
                if request.method in self.exempt_methods:
                    return f(*args, **kwargs)
                elif not current_user.is_authenticated:
                    return self.unauthorized()

                if roles.isdisjoint(current_user_roles):
                    abort(403)

                resp = make_response(f(*args, **kwargs))
                resp.cache_control.no_cache = True
                resp.cache_control.no_store = True
                resp.cache_control.must_revalidate = True
                return resp
            return access_wrapper
        return access_decorator

    def login_user(self, user, roles):
        session_id = self.generate_session_id()
        session['user_session_id'] = session_id

        session_data = {
            'user_id': user.id,
            'roles': list(roles),
            'login_at': datetime.datetime.utcnow(),
            'user_agent': str(request.user_agent),
            'remote_addr': request.remote_addr,
        }

        session_key = 'user_session:{}'.format(session_id)
        self.redis_conn.set(session_key, json.dumps(session_data))
        self.redis_conn.expire(session_key,
                               self.app.permanent_session_lifetime)

        _request_ctx_stack.top.user = user
        _request_ctx_stack.top.user_roles = roles
        return True

    def logout_user(self):
        session_id = session.pop('user_session_id', None)
        if session_id is not None:
            self.redis_conn.delete('user_session:{}'.format(session_id))

        _request_ctx_stack.top.user = None
        _request_ctx_stack.top.user_roles = set([])
        return True
