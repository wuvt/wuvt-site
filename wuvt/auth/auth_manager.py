from flask import abort, make_response, session, url_for
from flask_login import current_user, LoginManager
from flask_oidc import OpenIDConnect
from functools import wraps

from .models import User
from .blueprint import bp


class AuthManager(object):
    def __init__(self, app=None):
        self.bp = bp
        self.all_roles = set()

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        from . import views

        self.app = app

        app.config.setdefault('AUTH_METHOD', 'local')
        app.config.setdefault('AUTH_SUPERADMINS', ['admin'])
        app.config.setdefault('AUTH_ROLE_GROUPS', {
            'admin': ['webmasters'],
            'content': ['webmasters'],
            'business': ['business'],
            'library': ['librarians'],
            'missioncontrol': ['missioncontrol'],
        })

        self.login_manager = LoginManager()
        self.login_manager.login_view = "auth.login"
        self.login_manager.init_app(app)
        self.login_manager.user_loader(load_user)

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

                from .views import oidc_callback
                app.before_request(self._before_request)
                bp.route('/oidc_callback')(oidc_callback)

            self.oidc = OpenIDConnect(app)

    def _before_request(self):
        if self.app.config['OVERWRITE_REDIRECT_URI'] == False:
            self.app.config['OVERWRITE_REDIRECT_URI'] = url_for(
                'auth.oidc_callback', _external=True)

    def check_access(self, *roles):
        roles = set(roles)
        self.all_roles.update(roles)

        def access_decorator(f):
            @wraps(f)
            def access_wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return self.login_manager.unauthorized()

                access_roles = set(session.get('access', []))
                if roles.isdisjoint(access_roles):
                    abort(403)

                resp = make_response(f(*args, **kwargs))
                resp.cache_control.no_cache = True
                resp.cache_control.no_store = True
                resp.cache_control.must_revalidate = True
                return resp
            return access_wrapper
        return access_decorator

    def log_auth_success(self, method, user, req):
        return self.app.logger.warning(
            "wuvt-site: {method} user {user} logged in from {ip} using "
            "{ua}".format(
                method=method,
                user=user,
                ip=req.remote_addr,
                ua=req.user_agent))

    def log_auth_failure(self, method, user, req):
        return self.app.logger.warning(
            "wuvt-site: Failed login for {method} user {user} from {ip} using "
            "{ua}".format(
                method=method,
                user=user,
                ip=req.remote_addr,
                ua=req.user_agent))


def load_user(userid):
    return User.query.get(userid)
