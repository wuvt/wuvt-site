import re
import datetime
from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response, session, g
from flask.ext.login import login_required, login_user, logout_user, current_user

from wuvt import app
from wuvt import db
from wuvt import slugify
from wuvt import redirect_back
from wuvt import config
from wuvt.admin import bp

from wuvt.models import User, Page
from wuvt.blog.models import Category, Article

from markdown import markdown

@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')

@bp.route('/upload')
@login_required
def index():
    return render_template('admin/upload.html')

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



@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def user_add():
    error_fields = []
    if (current_user.username != 'admin'):
        abort(401)

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
            return redirect(url_for('admin.users'))

    return render_template('admin/user_add.html', error_fields=error_fields)
        

@bp.route('/users/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    user = User.query.get_or_404(id)
    error_fields = []

    # Only admins can edit users other than themselves
    if (current_user.username != 'admin') and (current_user.id != id) :
        abort(401)


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
            return redirect(url_for('admin.users'))

    else:
        return render_template('admin/user_edit.html', user=user, error_fields=error_fields)

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
    articles = Article.query.all()
    return render_template('admin/articles.html',
                           articles=articles)

@bp.route('/articles/draft/<int:art_id>')
@login_required
def article_draft(art_id):
    article = Article.query.filter(Article.id == art_id).first()
    if not article:
        abort(404)

    if not article.content:
        article.content = article.summary

    categories = Category.query.order_by(Category.name).all()
    return render_template('article.html',
                           categories=categories,
                           article=article)

@bp.route('/page/<int:page_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def page_edit(page_id):
    page = Page.query.get_or_404(page_id)
    error_fields = []

    if request.method == 'POST':
        # Title
        title = request.form.get('title', "").strip()
        if len(title) <= 0:
            error_fields.append('title')

        # Slug
        slug = request.form.get('slug', "")
        if slug != "":
            slug = slugify(slug)
            if len(slug) <= 0 or slug == False:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # Menu
        section = request.form['section'].strip()
        
        content = request.form.get('content', "").strip()

        if len(error_fields) <= 0:
            
            # ensure slug is unique, add - until it is iff we are changing it
            if slug != page.slug:
                while Page.query.filter_by(slug=slug).count() > 0:
                    slug += '-'

            page.slug = slug
            page.name = title
            page.menu = section
            page.content = content
            
            page.update_content(content)    # render HTML
            db.session.commit()

            flash("Page Saved")
            return redirect(url_for('admin.pages'))
   
    elif request.method == 'DELETE':
        db.session.delete(page)
        db.session.commit()

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })


    sections = config.NAV_TOP_SECTIONS
    print(sections)

    return render_template('admin/page_edit.html',
                           sections=sections,
                           page=page,
                           error_fields=error_fields)

@bp.route('/page/add', methods=['GET', 'POST'])
@login_required
def page_add():
    error_fields = []

    if request.method == 'POST':
        # Title
        title = request.form.get('title', "").strip()
        if len(title) <= 0:
            error_fields.append('title')

        # Slug
        slug = request.form.get('slug', "")
        if slug != "":
            slug = slugify(slug)
            if len(slug) <= 0 or slug == False:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # Menu
        section = request.form['section'].strip()
        
        content = request.form.get('content', "").strip()

        if len(error_fields) <= 0:
            # ensure slug is unique, add - until it is
            while Page.query.filter_by(slug=slug).count() > 0:
                slug += '-'
            
            page = Page(title, slug, content, True, section)
            
            db.session.add(page)
            db.session.commit()

            flash("Page Saved")
            return redirect(url_for('admin.pages'))
   
    sections = config.NAV_TOP_SECTIONS
    print(sections)

    return render_template('admin/page_add.html',
                           sections=sections,
                           error_fields=error_fields)

@bp.route('/article/add', methods=['GET', 'POST'])
@login_required
def article_add():
    error_fields = []
    # article = Article()

    if request.method == 'POST':
        # Title
        title = request.form.get('title', "").strip()
        if len(title) <= 0:
            error_fields.append('title')

        # Slug
        slug = request.form.get('slug', "")
        if slug != "":
            slug = slugify(slug)
            if len(slug) <= 0 or slug == False:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # author_id
        author_id = request.form['author_id'].strip()
        if User.query.filter_by(id=author_id).count() != 1:
            error_fields.append('author_id')

        # Category_id
        category_id = request.form['category_id'].strip()
        if Category.query.filter_by(id=category_id).count() != 1:
            error_fields.append('category_id')

        # datetime (should update to published time)
        published = request.form.get('published', False)
        if published != False:
            published = True
        # front page
        front_page = request.form.get('front_page', False)
        if front_page != False:
            front_page = True

        # summary
        summary = request.form.get('summary', "").strip()
        content = request.form.get('content', "").strip()


        if len(error_fields) <= 0:
            # ensure slug is unique, add - until it is
            while Article.query.filter_by(slug=slug).count() > 0:
                slug += '-'
            
            article = Article(title, slug, category_id, author_id, summary, content, published)
            # Why can't we just have a parameterless constructor so we don't
            # have to add constructors for each new field
            article.front_page = front_page
            if article.published == True:
                article.datetime = datetime.datetime.now()
            
            db.session.add(article)
            article.render_html()   # markdown to html
            db.session.commit()

            flash("Article Saved")
            return redirect(url_for('admin.articles'))
    elif request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    categories = Category.query.all()
    authors = User.query.all()
    return render_template('admin/article_add.html',
                           categories=categories,
                           authors=authors,
                           error_fields=error_fields)

@bp.route('/article/<int:art_id>', methods=['GET', 'POST', 'DELETE'])
@login_required
def article_edit(art_id):
    article = Article.query.get_or_404(art_id)
    error_fields = []

    if request.method == 'POST':
        # Title
        title = request.form.get('title', "").strip()
        if len(title) <= 0:
            error_fields.append('title')

        # Slug
        slug = request.form.get('slug', "").strip()
        if slug != "" or slug != article.slug:
            slug = slugify(slug)
            if len(slug) <= 0 or slug == False:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # author_id
        author_id = request.form.get('author_id', "").strip()
        if User.query.filter_by(id=author_id).count() != 1:
            error_fields.append('author_id')

        # Category_id
        category_id = request.form.get('category_id', "").strip()
        if Category.query.filter_by(id=category_id).count() != 1:
            error_fields.append('category_id')

        # datetime (should update to published time)
        published = request.form.get('published', False)
        if published != False:
            published = True
        if article.published == False and published != None:
            article.datetime = datetime.datetime.now()
        # front page
        front_page = request.form.get('front_page', False)
        if front_page != False:
            front_page = True

        # summary
        summary = request.form.get('summary', "").strip()
        print('summary: {0}', summary)
        content = request.form.get('content', "").strip()
        print('content: {0}', content)

        # markdown

        if len(error_fields) <= 0:

            # ensure slug is unique, add - until it is (if we're changing the slug)
            if article.slug != slug:
                while Article.query.filter_by(slug=slug).filter(Article.id != article.id).count() > 1:
                    slug += '-'

            article.title = title
            article.slug = slug
            article.category_id = category_id
            article.author_id = author_id
            article.published = published
            article.summary = summary
            article.content = content
            article.front_page = front_page
            db.session.commit()
            article.render_html()
            db.session.commit()

            flash("Article Saved")
            return redirect(url_for('admin.articles'))
    elif request.method == 'DELETE':
        db.session.delete(article)
        db.session.commit()

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    categories = Category.query.all()
    authors = User.query.all()
    return render_template('admin/article_edit.html',
                           article=article,
                           categories=categories,
                           authors=authors,
                           error_fields=error_fields)

@bp.route('/pages')
@login_required
def pages():
    pages = Page.query.all()
    return render_template('admin/pages.html', pages=pages)


@bp.route('/users')
@login_required
def users():
    if current_user.username == 'admin':
        users = User.query.order_by('name').all()

    else:
        users = User.query.filter(User.username == current_user.username).order_by('name').all()
    
    return render_template('admin/users.html', users=users)

#        return 'you are not authorized to modify users' # TODO 401


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

    return render_template('admin/login.html',
                           next=request.values.get('next') or "",
                           errors=errors)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('userrname', None)
    flash("You have been logged out.")
    return redirect(url_for('.login'))
