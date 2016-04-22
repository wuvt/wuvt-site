from flask import flash, redirect, render_template, request, url_for, session
from flask.ext.login import login_required, login_user, logout_user
import ldap

from wuvt import app
from wuvt import db
from wuvt.auth import bp, build_dn, ldap_group_test, log_auth_success, \
        log_auth_failure
from wuvt.models import User
from wuvt.view_utils import redirect_back


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        if app.config['LDAP_AUTH']:
            if len(request.form['password']) > 0:
                dn = build_dn(request.form['username'])

                try:
                    client = ldap.initialize(app.config['LDAP_URI'])
                    client.set_option(ldap.OPT_REFERRALS, 0)

                    if app.config.get('LDAP_TLS_CACERT', None) is not None:
                        client.set_option(ldap.OPT_X_TLS_CACERTFILE,
                                          app.config['LDAP_TLS_CACERT'])

                    if app.config['LDAP_STARTTLS']:
                        client.start_tls_s()

                    client.simple_bind_s(dn, request.form['password'])
                except ldap.INVALID_CREDENTIALS:
                    client.unbind()
                    log_auth_failure("LDAP", request.form['username'], request)
                    errors.append("Invalid username or password.")
                except (ldap.CONNECT_ERROR, ldap.SERVER_DOWN) as e:
                    errors.append("Could not contact the LDAP server.")
                    app.logger.error("Could not contact the LDAP server: "
                        "{}".format(e))
                else:
                    result = client.search_s(dn, ldap.SCOPE_SUBTREE)
                    user = User.query.filter(
                        User.username == result[0][1]['uid'][0]).first()

                    if user is None:
                        # create new user in the database, since one does not
                        # already exist for this LDAP user
                        user = User(result[0][1]['uid'][0],
                                    result[0][1]['cn'][0],
                                    result[0][1]['mail'][0])
                        db.session.add(user)
                        db.session.commit()
                    else:
                        # update existing user data in database
                        user.name = result[0][1]['cn'][0]
                        user.email = result[0][1]['mail'][0]
                        db.session.commit()

                    login_user(user)
                    session['username'] = user.username
                    session['access'] = []

                    if ldap_group_test(client, app.config['LDAP_GROUPS_ADMIN'],
                                       user.username):
                        session['access'].append('admin')

                    if ldap_group_test(client,
                                       app.config['LDAP_GROUPS_LIBRARY'],
                                       user.username):
                        session['access'].append('library')

                    if ldap_group_test(client,
                                       app.config['LDAP_GROUPS_RADIOTHON'],
                                       user.username):
                        session['access'].append('missioncontrol')
                    if ldap_group_test(client,
                                       app.config['LDAP_GROUPS_BUSINESS'],
                                       user.username):
                        session['access'].append('business')

                    log_auth_success("LDAP", user.username, request)
                    client.unbind()

                    return redirect_back('admin.index')
            else:
                log_auth_failure("LDAP", request.form['username'], request)
                errors.append("Invalid username or password.")
        else:
            user = User.query.filter(
                User.username == request.form['username']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                session['username'] = user.username
                session['access'] = ['admin', 'library', 'missioncontrol', 'business']

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
