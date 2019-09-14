from flask import Blueprint, render_template, request

from wuvt.auth import login_user, get_user_roles
from wuvt.auth.models import User
from wuvt.auth.view_utils import log_auth_success, log_auth_failure, \
        redirect_back


bp = Blueprint('auth_local', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        user = User.query.filter(
            User.username == request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user, get_user_roles(user))

            log_auth_success("local", user.username)
            return redirect_back('admin.index')
        else:
            log_auth_failure("local", request.form['username'])
            errors.append("Invalid username or password.")

    return render_template('auth/login.html', errors=errors)
