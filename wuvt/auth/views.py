from flask import flash, redirect, render_template, request, url_for, session
from flask_login import login_required, login_user, logout_user
import orthrus

from wuvt import app
from wuvt import db
from wuvt.auth import bp, log_auth_success, log_auth_failure
from wuvt.models import User
from wuvt.view_utils import redirect_back


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        if app.config['LDAP_AUTH']:
            if len(request.form['password']) > 0:
                o = orthrus.Orthrus(
                    ldap_uri=app.config['LDAP_URI'],
                    user_template_dn=app.config['LDAP_AUTH_DN'],
                    group_base_dn=app.config['LDAP_BASE_DN'],
                    role_mapping={
                        'admin': app.config['LDAP_GROUPS_ADMIN'],
                        'business': app.config['LDAP_GROUPS_BUSINESS'],
                        'library': app.config['LDAP_GROUPS_LIBRARY'],
                        'radiothon': app.config['LDAP_GROUPS_RADIOTHON'],
                    },
                    verify=app.config['LDAP_VERIFY'])

                try:
                    r = o.authenticate(request.form['username'],
                                       request.form['password'],
                                       ['uid', 'cn', 'mail'])

                    if r[0] is True:
                        user = User.query.filter(
                            User.username == r[1]['uid'][0]).first()

                        if user is None:
                            # create new user in the database, since one does
                            # not already exist for this orthrus user
                            user = User(r[1]['uid'][0],
                                        r[1]['cn'][0],
                                        r[1]['mail'][0])
                            db.session.add(user)
                            db.session.commit()
                        else:
                            # update existing user data in database
                            user.name = r[1]['cn'][0]
                            user.email = r[1]['mail'][0]
                            db.session.commit()

                        login_user(user)
                        session['username'] = user.username
                        session['access'] = r[2]

                        log_auth_success("orthrus", user.username, request)
                        return redirect_back('admin.index')
                    else:
                        log_auth_failure("orthrus", request.form['username'],
                                         request)
                        errors.append("Invalid username or password.")
                except Exception as e:
                    app.logger.error("wuvt-site: orthrus: {}".format(e))
                    errors.append("Authentication backend error.")
            else:
                log_auth_failure("orthrus", request.form['username'], request)
                errors.append("Invalid username or password.")
        else:
            user = User.query.filter(
                User.username == request.form['username']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                session['username'] = user.username
                session['access'] = ['admin', 'library', 'missioncontrol',
                                     'business']

                log_auth_success("DB", user.username, request)
                return redirect_back('admin.index')
            else:
                log_auth_failure("DB", request.form['username'], request)
                errors.append("Invalid username or password.")

    return render_template('auth/login.html',
                           next=request.values.get('next') or "",
                           errors=errors)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('username', None)
    flash("You have been logged out.")
    return redirect(url_for('.login'))
