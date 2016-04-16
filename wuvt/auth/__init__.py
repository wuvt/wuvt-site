from flask import abort, make_response, session, Blueprint
from flask.ext.login import current_user, UserMixin
from functools import wraps
import ldap

from wuvt import app
from wuvt import login_manager
from wuvt.models import User


bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


def build_dn(username):
    return app.config['LDAP_AUTH_DN'].format(ldap.dn.escape_dn_chars(username))


def build_group_query(groups):
    query = '(|'
    for group in groups:
        query += '(cn={})'.format(ldap.dn.escape_dn_chars(group))
    query += ')'
    return query


def ldap_group_test(client, groups, username):
    result = client.search_s(app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                             build_group_query(groups))
    for r in result:
        if 'memberUid' in r[1]:
            for u in r[1]['memberUid']:
                if u == username:
                    return True

    return False


def check_access(*sections):
    sections = set(sections)
    def access_decorator(f):
        @wraps(f)
        def access_wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return app.login_manager.unauthorized()

            access_sections = set(session.get('access', []))
            if sections.isdisjoint(access_sections):
                abort(403)

            resp = make_response(f(*args, **kwargs))
            resp.cache_control.no_cache = True
            resp.cache_control.no_store = True
            resp.cache_control.must_revalidate = True
            return resp
        return access_wrapper
    return access_decorator


def log_auth_success(method, user, req):
    return app.logger.warning(
        "{method} user {user} logged in from {ip} using {ua}".format(
            method=method,
            user=user,
            ip=req.remote_addr,
            ua=req.user_agent))


def log_auth_failure(method, user, req):
    return app.logger.warning(
        "Failed login for {method} user {user} from {ip} using {ua}".format(
            method=method,
            user=user,
            ip=req.remote_addr,
            ua=req.user_agent))


from wuvt.auth import views
