from flask import Blueprint, abort, g, render_template, url_for, session

from wuvt import app
from wuvt import auth_manager
from wuvt.auth import login_user
from wuvt.auth.user import _find_or_create_user
from wuvt.auth.utils import get_user_roles
from wuvt.auth.view_utils import log_auth_success, log_auth_failure, \
        is_safe_url


bp = Blueprint('auth_oidc', __name__)


@bp.route('/oidc_callback')
def oidc_callback():
    response = auth_manager.oidc.oidc._oidc_callback()

    id_token = getattr(g, 'oidc_id_token', None)
    if id_token is None:
        log_auth_failure("oidc", None)
        abort(401)

    if 'email' not in id_token:
        return render_template('auth/need_email.html'), 400

    user = _find_or_create_user(
        id_token['sub'], id_token['name'], id_token['email'])

    user_groups = id_token.get(app.config.get('OIDC_GROUPS_CLAIM', 'groups'))

    login_user(user, get_user_roles(user, user_groups))

    log_auth_success("oidc", user.username)
    return response


@bp.route('/login', methods=['GET', 'POST'])
def login():
    target = session.pop('login_target', None)
    if not target or not is_safe_url(target):
        target = url_for('admin.index')

    return auth_manager.oidc.oidc.redirect_to_auth_server(target)
