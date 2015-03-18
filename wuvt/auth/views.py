from flask import flash, redirect, render_template, request, url_for, session
from flask.ext.login import login_required, login_user, logout_user, current_user
import ldap

from wuvt import app
from wuvt import db
from wuvt import redirect_back
from wuvt.auth import bp
from wuvt.auth import build_dn
from wuvt.auth import ldap_group_test
from wuvt.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        if app.config['LDAP_AUTH']:
            dn = build_dn(request.form['username'])

            try:
                client = ldap.initialize(app.config['LDAP_URI'])
                client.set_option(ldap.OPT_REFERRALS, 0)
                client.simple_bind_s(dn, request.form['password'])
            except ldap.INVALID_CREDENTIALS:
                client.unbind()
                errors.append("Invalid username or password.")
            except ldap.SERVER_DOWN:
                errors.append("Could not contact the LDAP server.")
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
                session['access_admin'] = ldap_group_test(
                    client, app.config['LDAP_GROUPS_ADMIN'], user.username)
                session['access_missioncontrol'] = ldap_group_test(
                    client, app.config['LDAP_GROUPS_RADIOTHON'], user.username)

                client.unbind()

                return redirect_back('admin.index')
        else:
            user = User.query.filter(
                User.username == request.form['username']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                session['username'] = user.username
                session['access_admin'] = True
                session['access_missioncontrol'] = True

                return redirect_back('admin.index')
            else:
                errors.append("Invalid username or password.")

    return render_template('auth/login.html',
                           next=request.values.get('next') or "",
                           errors=errors)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('userrname', None)
    flash("You have been logged out.")
    return redirect(url_for('.login'))
