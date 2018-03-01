import base64
import datetime
import os
from flask import abort, flash, make_response, redirect, request, session, \
    url_for, _request_ctx_stack
from functools import wraps

from .models import User, UserSession
from .mixins import AnonymousUserMixin
from .blueprint import bp
from .utils import current_user, current_user_roles, \
    _user_context_processor, _user_roles_context_processor


class AuthManager(object):
    def __init__(self, app=None, db=None):
        self.bp = bp
        self.all_roles = set()

        self.exempt_methods = set(['OPTIONS'])
        self.login_message = "Please login to access this page."
        self.login_message_category = 'message'
        self.login_view = "auth.login"

        if db is not None:
            self.db = db
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

        app.auth_manager = self
        app.context_processor(_user_context_processor)
        app.context_processor(_user_roles_context_processor)

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
        flash(self.login_message, self.login_message_category)
        return redirect(url_for(self.login_view, next=request.url))

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

        _request_ctx_stack.top.user = None
        _request_ctx_stack.top.user_roles = set([])
        return True
