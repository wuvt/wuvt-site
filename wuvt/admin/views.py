import datetime
import dateutil.parser
import os
from flask import abort, flash, jsonify, make_response, render_template, \
        redirect, request, url_for
from flask_login import login_required
from werkzeug import secure_filename

from wuvt import app, auth_manager, cache, db, redis_conn
from wuvt.admin import bp
from wuvt.auth.models import User
from wuvt.blog import list_categories
from wuvt.blog.models import Category, Article
from wuvt.donate.models import Order
from wuvt.models import Page
from wuvt.views import get_menus
from wuvt.view_utils import slugify

from wuvt.admin.auth import views as auth_views
from wuvt.admin.charts import views as charts_views
from wuvt.admin.library import views as library_views


@bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')


@bp.route('/upload', methods=['GET', 'POST'])
@auth_manager.check_access('admin', 'content')
def upload():
    if request.method == 'GET':
        return render_template('admin/upload.html')
    else:
        file = request.files['file']
        dir = request.form['destination']

        if dir == 'default':
            dir = ''

        if file:
            filename = secure_filename(file.filename)
            newpath = os.path.join(app.config['UPLOAD_DIR'], dir, filename)
            webroot_path = os.path.join('/static/media', dir, filename)
            file.save(newpath)
            flash('Your file has been uploaded to: ' + webroot_path)

        return render_template('admin/upload.html')


@bp.route('/categories')
@auth_manager.check_access('admin', 'content')
def categories():
    categories = Category.query.order_by('name').all()
    return render_template('admin/categories.html',
                           categories=categories)


@bp.route('/js/categories.js')
@auth_manager.check_access('admin')
def categories_js():
    resp = make_response(render_template('admin/categories.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/categories/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def category_add():
    error_fields = []

    if request.method == 'POST':
        name = request.form['name'].strip()
        if len(name) <= 0:
            error_fields.append('name')

        published = request.form.get('published', False)
        if published is not False:
            published = True

        if len(error_fields) <= 0:
            slug = slugify(name)

            # ensure slug is unique, add - until it is
            while Category.query.filter_by(slug=slug).count() > 0:
                slug += '-'

            db.session.add(Category(name, slug, published))
            db.session.commit()

            cache.set('blog_categories', list_categories())

            flash("Category added.")
            return redirect(url_for('admin.categories'))

    return render_template('admin/category_add.html',
                           error_fields=error_fields)


@bp.route('/categories/<int:cat_id>', methods=['GET', 'POST', 'DELETE'])
@auth_manager.check_access('admin')
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

        published = request.form.get('published', False)
        if published is not False:
            published = True

        if len(error_fields) <= 0:
            if slug != category.slug:
                # if slug has changed, ensure it is unique
                while Category.query.filter_by(slug=slug).count() > 0:
                    slug += '-'

            category.name = name
            category.slug = slug
            category.published = published
            db.session.commit()

            cache.set('blog_categories', list_categories())

            flash("Category saved.")
            return redirect(url_for('admin.categories'))
    elif request.method == 'DELETE':
        db.session.delete(category)
        db.session.commit()

        cache.set('blog_categories', list_categories())

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    return render_template('admin/category_edit.html',
                           category=category,
                           error_fields=error_fields)


@bp.route('/articles')
@auth_manager.check_access('admin', 'content')
def articles():
    articles = Article.query.order_by(Article.datetime.desc()).all()
    return render_template('admin/articles.html',
                           articles=articles)


@bp.route('/js/articles.js')
@auth_manager.check_access('admin', 'content')
def articles_js():
    resp = make_response(render_template('admin/articles.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/articles/draft/<int:art_id>')
@auth_manager.check_access('admin', 'content')
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
@auth_manager.check_access('admin', 'content')
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
            if len(slug) <= 0 or slug is None:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # Menu
        section = request.form['section'].strip()

        published = request.form.get('published', False)
        if published is not False:
            published = True

        content = request.form.get('content', "").strip()

        if len(error_fields) <= 0:
            # ensure slug is unique, add - until it is iff we are changing it
            if slug != page.slug:
                while Page.query.filter_by(slug=slug).count() > 0:
                    slug += '-'

            page.slug = slug
            page.name = title
            page.menu = section
            page.published = published
            page.content = content

            page.update_content(content)    # render HTML
            db.session.commit()

            cache.set('menus', get_menus())

            flash("Page Saved")
            return redirect(url_for('admin.pages'))

    elif request.method == 'DELETE':
        db.session.delete(page)
        db.session.commit()

        cache.set('menus', get_menus())

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    sections = app.config['NAV_TOP_SECTIONS']

    return render_template('admin/page_edit.html',
                           sections=sections,
                           page=page,
                           error_fields=error_fields)


@bp.route('/page/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
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
            if len(slug) <= 0 or slug is None:
                error_fields.append('slug')
        elif len(slug) <= 0 and len(title) > 0:
            slug = slugify(title)

        # Menu
        section = request.form['section'].strip()

        published = request.form.get('published', False)
        if published is not False:
            published = True

        content = request.form.get('content', "").strip()

        if len(error_fields) <= 0:
            # ensure slug is unique, add - until it is
            while Page.query.filter_by(slug=slug).count() > 0:
                slug += '-'

            page = Page(title, slug, content, published, section)

            db.session.add(page)
            db.session.commit()

            cache.set('menus', get_menus())

            flash("Page Saved")
            return redirect(url_for('admin.pages'))

    sections = app.config['NAV_TOP_SECTIONS']

    return render_template('admin/page_add.html',
                           sections=sections,
                           error_fields=error_fields)


@bp.route('/article/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin', 'content')
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
            if len(slug) <= 0 or slug is None:
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
        if published is not False:
            published = True
        # front page
        front_page = request.form.get('front_page', False)
        if front_page is not False:
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
            if article.published is True:
                article.datetime = datetime.datetime.utcnow()

            db.session.add(article)
            article.render_html()   # markdown to html
            db.session.commit()

            flash("Article Saved")
            return redirect(url_for('admin.articles'))

    categories = Category.query.all()
    authors = User.query.all()
    return render_template('admin/article_add.html',
                           categories=categories,
                           authors=authors,
                           error_fields=error_fields)


@bp.route('/article/<int:art_id>', methods=['GET', 'POST', 'DELETE'])
@auth_manager.check_access('admin', 'content')
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
            if len(slug) <= 0 or slug is None:
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
        if published is not False:
            published = True
        #if article.published is False and published is not None:
        #    article.datetime = datetime.datetime.utcnow()
        # front page
        front_page = request.form.get('front_page', False)
        if front_page is not False:
            front_page = True

        # summary
        summary = request.form.get('summary', "").strip()
        content = request.form.get('content', "").strip()

        # markdown

        if len(error_fields) <= 0:

            # ensure slug is unique, add - until it is (if we're changing the slug)
            if article.slug != slug:
                while Article.query.filter(db.and_(
                        Article.slug == slug,
                        Article.id != article.id)).count() > 0:
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
@auth_manager.check_access('admin', 'content')
def pages():
    pages = Page.query.all()
    return render_template('admin/pages.html', pages=pages)


@bp.route('/js/pages.js')
@auth_manager.check_access('admin', 'content')
def pages_js():
    resp = make_response(render_template('admin/pages.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/donations', methods=['GET', 'POST'])
@auth_manager.check_access('business')
def donation_index():
    if not app.config['DONATE_ENABLE']:
        abort(404)

    if request.method == 'POST':
        if 'reset_stats' in request.form:
            redis_conn.set('donation_stats_start',
                           datetime.datetime.utcnow().isoformat())
        return redirect(url_for('.donation_index'))

    stats = Order.query.with_entities(
        db.func.sum(Order.amount).label('total_paid'),
        db.func.max(Order.amount).label('max_paid'))

    donation_stats_start = redis_conn.get('donation_stats_start')
    if donation_stats_start is not None:
        last_stats_reset = dateutil.parser.parse(donation_stats_start)
        stats = stats.filter(Order.placed_date > last_stats_reset)
    else:
        last_stats_reset = None

    stats = stats.all()

    total = stats[0][0]
    if total is None:
        total = 0

    max_donation = stats[0][1]
    if max_donation is None:
        max_donation = 0

    donations = Order.query.all()

    return render_template('admin/donation_index.html',
                           donations=donations,
                           total=total,
                           max=max_donation,
                           last_stats_reset=last_stats_reset)
