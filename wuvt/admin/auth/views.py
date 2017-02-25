from flask import abort, flash, jsonify, make_response, redirect, \
    render_template, request, url_for
from flask_login import current_user

from wuvt import app, auth_manager, db
from wuvt.admin import bp
from wuvt.auth.models import User, UserRole, GroupRole


@bp.route('/roles/users/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def role_add_user():
    error_fields = []

    if request.method == 'POST':
        role = request.form['role']
        if not role in auth_manager.all_roles:
            error_fields.append('role')

        user = User.query.get(request.form['user'])
        if user is None:
            error_fields.append('user')

        if len(error_fields) <= 0:
            user_id = int(request.form['user'])

            existing = UserRole.query.filter_by(
                user_id=user_id, role=role).count()
            if existing > 0:
                flash("That role was already assigned to that user.")
            else:
                db.session.add(UserRole(user_id, role))
                db.session.commit()

                flash("The role has been assigned to the user.")

            return redirect(url_for('.roles'), 303)

    users = User.query.order_by('name').all()

    return render_template('admin/role_add_user.html', users=users,
                           roles=sorted(auth_manager.all_roles),
                           error_fields=error_fields)


@bp.route('/roles/users/remove/<int:id>', methods=['POST', 'DELETE'])
@auth_manager.check_access('admin')
def role_remove_user(id):
    user_role = UserRole.query.get_or_404(id)
    db.session.delete(user_role)
    db.session.commit()

    if request.method == 'DELETE' or request.wants_json():
        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })
    else:
        return redirect(url_for('.roles', 303))


@bp.route('/roles/groups/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def role_add_group():
    error_fields = []

    if request.method == 'POST':
        role = request.form['role']
        if not role in auth_manager.all_roles:
            error_fields.append('role')

        group = request.form['group'].strip()
        if len(request.form['group']) <= 0 or len(group) > 254:
            error_fields.append('group')

        if len(error_fields) <= 0:
            existing = GroupRole.query.filter_by(
                group=group, role=role).count()
            if existing > 0:
                flash("That role was already assigned to that group.")
            else:
                db.session.add(GroupRole(group, role))
                db.session.commit()

                flash("The role has been assigned to the group.")

            return redirect(url_for('.roles'), 303)

    return render_template('admin/role_add_group.html',
                           roles=sorted(auth_manager.all_roles),
                           error_fields=error_fields)


@bp.route('/roles/groups/remove/<int:id>', methods=['POST', 'DELETE'])
@auth_manager.check_access('admin')
def role_remove_group(id):
    group_role = GroupRole.query.get_or_404(id)
    db.session.delete(group_role)
    db.session.commit()

    if request.method == 'DELETE' or request.wants_json():
        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })
    else:
        return redirect(url_for('.roles', 303))


@bp.route('/roles')
@auth_manager.check_access('admin')
def roles():
    user_roles = UserRole.query.join(User).order_by('role').all()
    group_roles = GroupRole.query.order_by('role').all()

    return render_template('admin/roles.html', user_roles=user_roles,
                           group_roles=group_roles)


@bp.route('/js/roles.js')
@auth_manager.check_access('admin')
def roles_js():
    resp = make_response(render_template('admin/roles.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/users/new', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def user_add():
    if app.config['AUTH_METHOD'] != "local":
        abort(404)

    error_fields = []
    if current_user.username != 'admin':
        abort(403)

    if request.method == 'POST':
        username = request.form['username'].strip()

        if len(username) <= 2:
            error_fields.append('username')

        if len(username) > 8:
            error_fields.append('username')

        if not username.isalnum():
            error_fields.append('username')

        if User.query.filter_by(username=username).count() > 0:
            error_fields.append('username')

        name = request.form['name'].strip()

        if len(name) <= 0:
            error_fields.append('name')

        email = request.form['email'].strip()

        if len(email) <= 3:
            error_fields.append('email')

        password = request.form['password'].strip()

        if len(password) <= 0:
            error_fields.append('password')

        # Create user if no errors
        if len(error_fields) <= 0:
            db.session.add(User(username, name, email))
            db.session.commit()
            user = User.query.filter_by(username=username).first()
            user.set_password(password)
            db.session.commit()

            flash("User added.")
            return redirect(url_for('admin.users'), 303)

    return render_template('admin/user_add.html', error_fields=error_fields)


@bp.route('/users/<int:id>', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def user_edit(id):
    if app.config['AUTH_METHOD'] != "local":
        abort(404)

    user = User.query.get_or_404(id)
    error_fields = []

    # Only admins can edit users other than themselves
    if current_user.username != 'admin' and current_user.id != id:
        abort(403)

    if request.method == 'POST':
        name = request.form['name'].strip()
        if len(name) <= 0:
            error_fields.append('name')

        # You can't change a username or ID

        pw = request.form['newpass'].strip()

        email = request.form['email'].strip()
        if len(email) <= 0:
            error_fields.append('email')

        # TODO allow users to be disabled

        if len(error_fields) == 0:
            # update user's: name, email
            user.name = name
            user.email = email

            # if user entered a new pw
            if len(pw) > 0:
                user.set_password(pw)
            # TODO reset password to pw

            db.session.commit()

            flash('User updated.')
            return redirect(url_for('admin.users'), 303)

    else:
        return render_template('admin/user_edit.html', user=user,
                               error_fields=error_fields)


@bp.route('/users')
@auth_manager.check_access('admin')
def users():
    if app.config['AUTH_METHOD'] != "local":
        abort(404)

    if current_user.username == 'admin':
        users = User.query.order_by('name').all()
        is_admin = True
    else:
        users = User.query.filter(
            User.username == current_user.username).order_by('name').all()
        is_admin = False

    return render_template('admin/users.html', users=users, is_admin=is_admin)
