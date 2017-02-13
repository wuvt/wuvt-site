from flask import abort, flash, g, get_flashed_messages, redirect, \
        render_template, request, url_for, session
from flask_login import login_required, login_user, logout_user
import orthrus

from wuvt import app
from wuvt import auth_manager
from wuvt import csrf
from wuvt import db
from wuvt.auth.blueprint import bp
from wuvt.models import User
from wuvt.view_utils import redirect_back, is_safe_url


def _find_or_create_user(username, name, email):
    user = User.query.filter(User.username == username).first()

    if user is None:
        # create new user in the database, since one doesn't already exist
        user = User(username, name, email)
        db.session.add(user)
        db.session.commit()
    else:
        # update existing user data in database
        user.name = name
        user.email = email
        db.session.commit()

    return user


@csrf.exempt
def oidc_callback():
    response = auth_manager.oidc._oidc_callback()

    id_token = getattr(g, 'oidc_id_token', None)
    if id_token is None:
        auth_manager.log_auth_failure("oidc", None, request)
        abort(401)

    user = _find_or_create_user(
        id_token['sub'], id_token['name'], id_token['email'])

    user_roles = []
    for role, groups in app.config['AUTH_ROLE_GROUPS'].items():
        for group in groups:
            if group in id_token['groups']:
                user_roles.append(role)

    login_user(user)
    session['username'] = id_token['sub']
    session['access'] = user_roles

    auth_manager.log_auth_success("oidc", user.username, request)
    return response


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if app.config['AUTH_METHOD'] == 'oidc':
        # pull all flashed messages off the session, otherwise they will be
        # displayed post login, which is not what we want
        get_flashed_messages()

        target = request.values.get('next', '')
        if not target or not is_safe_url(target):
            target = url_for('admin.index')

        return auth_manager.oidc.redirect_to_auth_server(target)

    if 'username' in request.form:
        if app.config['AUTH_METHOD'] == 'ldap':
            if len(request.form['password']) > 0:
                o = orthrus.Orthrus(
                    ldap_uri=app.config['LDAP_URI'],
                    user_template_dn=app.config['LDAP_AUTH_DN'],
                    group_base_dn=app.config['LDAP_BASE_DN'],
                    role_mapping=app.config['AUTH_ROLE_GROUPS'],
                    verify=app.config['LDAP_VERIFY'])

                try:
                    r = o.authenticate(request.form['username'],
                                       request.form['password'],
                                       ['uid', 'cn', 'mail'])

                    if r[0] is True:
                        user = _find_or_create_user(
                            r[1]['uid'][0], r[1]['cn'][0], r[1]['mail'][0])

                        login_user(user)
                        session['username'] = user.username
                        session['access'] = r[2]

                        auth_manager.log_auth_success("orthrus", user.username,
                                                      request)
                        return redirect_back('admin.index')
                    else:
                        auth_manager.log_auth_failure("orthrus",
                                                      request.form['username'],
                                                      request)
                        errors.append("Invalid username or password.")
                except Exception as e:
                    app.logger.error("wuvt-site: orthrus: {}".format(e))
                    errors.append("Authentication backend error.")
            else:
                auth_manager.log_auth_failure("orthrus",
                                              request.form['username'],
                                              request)
                errors.append("Invalid username or password.")
        else:
            user = User.query.filter(
                User.username == request.form['username']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                session['username'] = user.username
                session['access'] = auth_manager.all_roles

                auth_manager.log_auth_success("local", user.username, request)
                return redirect_back('admin.index')
            else:
                auth_manager.log_auth_failure("local",
                                              request.form['username'],
                                              request)
                errors.append("Invalid username or password.")

    return render_template('auth/login.html',
                           next=request.values.get('next') or "",
                           errors=errors)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    session.pop('access', None)

    if app.config['AUTH_METHOD'] == 'oidc':
        return redirect('/')
    else:
        flash("You have been logged out.")
        return redirect(url_for('.login'))
