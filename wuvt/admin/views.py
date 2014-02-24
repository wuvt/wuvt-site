from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
try:
    from flask.ext.login import login_required, login_user, logout_user
except:
    from flaskext.login import login_required, login_user, logout_user

from wuvt import app
from wuvt import db
from wuvt import slugify
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
    error_fields = []

    if request.method == 'POST':
        name = request.form['name'].strip()
        if len(name) <= 0:
            error_fields.append('name')

        if len(error_fields) <= 0:
            slug = slugify(name)

            # ensure slug is unique, add - until it is
            while Category.query.filter_by(slug=slug).count() > 0:
                slug += '-'

            db.session.add(Category(name, slug))
            db.session.commit()

            flash("Category added.")
            return redirect(url_for('admin.categories'))

    return render_template('admin/category_add.html',
                           error_fields=error_fields)


@bp.route('/categories/<int:cat_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def category_edit(cat_id):
    category = Category.query.get_or_404(cat_id)
    error_fields = []

    if request.method == 'POST':
        name = request.form['name'].strip()
        if len(name) <= 0:
            error_fields.append('name')

        slug = request.form['slug'].strip()
        if len(slug) <= 0:
            # generate a new slug if none is provided
            slug = slugify(name)

        if len(error_fields) <= 0:
            if slug != category.slug:
                # if slug has changed, ensure it is unique
                while Category.query.filter_by(slug=slug).count() > 0:
                    slug += '-'

            category.name = name
            category.slug = slug
            db.session.commit()

            flash("Category saved.")
            return redirect(url_for('admin.categories'))
    elif request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    return render_template('admin/category_edit.html',
                           category=category,
                           error_fields=error_fields)


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
    return redirect(url_for('.login'))
