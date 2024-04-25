import base64
import datetime
import os
from flask import abort, make_response, redirect, request, session, \
    url_for, _request_ctx_stack
from functools import wraps

from .models import GroupRole, User, UserRole, UserSession
from .mixins import AnonymousUserMixin
from .utils import current_user, current_user_roles, \
    _user_context_processor, _user_roles_context_processor


class AuthManager(object):
    def __init__(self, app=None, db=None):
        self.all_roles = set()

        self.exempt_methods = set(['OPTIONS'])

        if db is not None:
            self.db = db
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        app.auth_manager = self
        app.context_processor(_user_context_processor)
        app.context_processor(_user_roles_context_processor)

        if app.config.get('AUTH_METHOD') == 'google':
            app.config.setdefault('GOOGLE_ALLOWED_DOMAINS', [])

            from authlib.integrations.flask_client import OAuth
            self.oauth = OAuth(app)

            from loginpass import create_flask_blueprint
            from loginpass.google import Google
            from .google import handle_authorize

            google_bp = create_flask_blueprint([Google], self.oauth,
                                               handle_authorize)
            app.register_blueprint(google_bp, url_prefix='/auth')

            self.login_view = 'loginpass.login'
            self.login_view_kwargs = {'name': "google"}
        elif app.config.get('AUTH_METHOD') == 'oidc':
            from authlib.integrations.flask_client import OAuth
            self.oauth = OAuth(app)

            from loginpass import create_flask_blueprint
            from .oidc import create_oidc_backend, handle_authorize

            backend = create_oidc_backend('oidc',
                                          app.config['OIDC_CLIENT_SECRETS'],
                                          app.config.get('OIDC_SCOPES'))
            oidc_bp = create_flask_blueprint([backend], self.oauth,
                                             handle_authorize)
            app.register_blueprint(oidc_bp, url_prefix='/auth')

            self.login_view = 'loginpass.login'
            self.login_view_kwargs = {'name': "oidc"}
        else:
            from . import local_views
            app.register_blueprint(local_views.bp, url_prefix='/auth/local')

            self.login_view = 'auth_local.login'

        from . import views
        app.register_blueprint(views.bp, url_prefix='/auth')

    def generate_session_id(self):
        return base64.urlsafe_b64encode(os.urandom(64)).decode('ascii')

    def load_user_session(self):
        ctx = _request_ctx_stack.top

        session_id = session.get('user_session_id')
        if session_id is None or type(session_id) != str:
            ctx.user = AnonymousUserMixin()
            ctx.user_roles = set([])
        else:
            now = datetime.datetime.utcnow()
            user_session = UserSession.query.get(session_id)
            if user_session is not None and \
                    now > user_session.login_at and now < user_session.expires:
                ctx.user = user_session.user
                ctx.user_roles = user_session.roles
            else:
                ctx.user = AnonymousUserMixin()
                ctx.user_roles = set([])

    def load_user(self, user_id):
        return User.query.get(user_id)

    def unauthorized(self):
        session['login_target'] = request.url
        return redirect(url_for(self.login_view, **self.login_view_kwargs))

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

        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            expires=datetime.datetime.utcnow() + self.app.permanent_session_lifetime,
            user_agent=str(request.user_agent),
            remote_addr=request.remote_addr,
            roles=roles)
        self.db.session.add(user_session)

        try:
            self.db.session.commit()
        except:
            self.db.session.rollback()
            raise

        session['user_session_id'] = session_id
        _request_ctx_stack.top.user = user
        _request_ctx_stack.top.user_roles = roles
        return True

    def logout_user(self):
        session_id = session.pop('user_session_id', None)
        if session_id is not None or type(session_id) != str:
            user_session = UserSession.query.get(session_id)
            if user_session is not None:
                self.db.session.delete(user_session)
                try:
                    self.db.session.commit()
                except:
                    self.db.session.rollback()
                    raise

        _request_ctx_stack.top.user = AnonymousUserMixin()
        _request_ctx_stack.top.user_roles = set([])
        return True

    def cleanup_expired_sessions(self):
        now = datetime.datetime.utcnow()
        user_sessions = UserSession.query.filter(UserSession.expires <= now)
        for user_session in user_sessions:
            self.db.session.delete(user_session)
        self.db.session.commit()

    def get_user_roles(self, user, user_groups=None):
        if user.username in self.app.config['AUTH_SUPERADMINS']:
            return list(self.all_roles)

        user_roles = set([])

        if user_groups is not None:
            for role, groups in list(
                    self.app.config['AUTH_ROLE_GROUPS'].items()):
                for group in groups:
                    if group in user_groups:
                        user_roles.add(role)

            for group in user_groups:
                group_roles_db = GroupRole.query.filter(GroupRole.group == group)
                for entry in group_roles_db:
                    user_roles.add(entry.role)

        user_roles_db = UserRole.query.filter(UserRole.user_id == user.id)
        for entry in user_roles_db:
            user_roles.add(entry.role)

        return list(user_roles)
