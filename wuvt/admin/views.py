from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
try:
    from flask.ext.login import login_required, login_user, logout_user
except:
    from flaskext.login import login_required, login_user, logout_user

from wuvt import db
from wuvt import lib
from wuvt import redirect_back
from wuvt.admin import bp

from wuvt.models import User
from wuvt.blog.models import Category, Article


@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')


@bp.route('/categories')
@login_required
def categories():
    categories = Category.query.order_by('name').all()
    return render_template('admin/categories.html',
                           categories=categories)


@bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def category_add():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            pass

    return render_template('admin/category_add.html')



@bp.route('/categories/<int:cat_id>', methods=['GET', 'POST'])
@login_required
def category_edit(cat_id):
    category = Category.query.get(id == cat_id)
    return render_template('admin/category_edit.html',
                           category=category)


@bp.route('/articles')
@login_required
def articles():
    return render_template('admin/articles.html')


@bp.route('/pages')
@login_required
def pages():
    return render_template('admin/pages.html')


@bp.route('/users')
@login_required
def users():
    return render_template('admin/users.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []

    if 'username' in request.form:
        user = User.query.filter(User.username == request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect_back('admin.index')
        else:
            errors.append("Invalid username or password.")

    return render_template('admin/login.html',
                           next=request.values.get('next') or "",
                           errors=errors)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))
