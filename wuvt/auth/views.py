from flask import Blueprint, current_app, flash, redirect, url_for, session
from wuvt.auth import login_required, logout_user


bp = Blueprint('auth', __name__)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('access', None)

    if current_app.config['AUTH_METHOD'] in ('google', 'oidc'):
        return redirect('/')
    else:
        flash("You have been logged out.")
        return redirect(url_for('admin.index'))
