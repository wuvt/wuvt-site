from flask import flash, redirect, render_template, request, url_for, session
from flask.ext.login import login_required, login_user, logout_user, current_user

from wuvt import redirect_back
from wuvt.auth import bp
from wuvt.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        user = User.query.filter(User.username == request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            session['username'] = request.form['username']
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
