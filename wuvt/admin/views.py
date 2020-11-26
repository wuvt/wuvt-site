import boto3
import datetime
import dateutil.parser
import os
from flask import abort, flash, jsonify, make_response, render_template, \
        redirect, request, url_for
from werkzeug import secure_filename

from wuvt import app, auth_manager, cache, db, redis_conn
from wuvt.auth import current_user, login_required
from wuvt.admin import bp
from wuvt.auth.models import User
from wuvt.blog import list_categories
from wuvt.blog.forms import ArticleForm
from wuvt.blog.models import Category, Article, ArticleRevision
from wuvt.donate.models import Order
from wuvt.forms import PageForm
from wuvt.models import Page, PageRevision
from wuvt.views import get_menus
from wuvt.view_utils import slugify
from wuvt.admin.auth import views as auth_views  # noqa: F401
import csv
import io


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
        uploaded = request.files['file']
        destdir = secure_filename(request.form['destination'])

        if destdir == 'default':
            destdir = ''

        if uploaded:
            filename = secure_filename(uploaded.filename)
            filepath = os.path.join(destdir, filename)

            if len(app.config['UPLOAD_S3_BUCKET']) > 0:
                aws_config = {}
                if len(app.config['UPLOAD_S3_ENDPOINT']) > 0:
                    aws_config['endpoint_url'] = app.config[
                        'UPLOAD_S3_ENDPOINT']
                if len(app.config['UPLOAD_S3_REGION']) > 0:
                    aws_config['region_name'] = app.config['UPLOAD_S3_REGION']

                s3 = boto3.resource('s3', **aws_config)
                s3.meta.client.upload_fileobj(
                    uploaded,
                    app.config['UPLOAD_S3_BUCKET'],
                    filepath)
            else:
                uploaded.save(os.path.join(app.config['UPLOAD_DIR'], filepath))

            upload_url = app.config['UPLOAD_URL'] + '/' + filepath
            flash('Your file has been uploaded to: ' + upload_url)

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

            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

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

            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

            cache.set('blog_categories', list_categories())

            flash("Category saved.")
            return redirect(url_for('admin.categories'))
    elif request.method == 'DELETE':
        db.session.delete(category)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

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
    form = PageForm()
    if request.method == 'POST' and form.validate():
        slug = form.slug.data
        if len(slug) <= 0:
            slug = slugify(form.title.data)

        # ensure slug is unique, add - until it is iff we are changing it
        if slug != page.slug:
            while Page.query.filter_by(slug=slug).count() > 0:
                slug += '-'

        page.slug = slug
        page.name = form.title.data
        page.menu = form.section.data
        page.published = form.published.data
        page.update_content(form.content.data)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        cache.set('menus', get_menus())

        revision = PageRevision(
            page_id=page.id,
            author_id=current_user.id,
            name=form.title.data,
            content=form.content.data)
        db.session.add(revision)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        flash("Page Saved")
        return redirect(url_for('admin.pages'))

    elif request.method == 'DELETE':
        db.session.delete(page)
        db.session.commit()

        cache.set('menus', get_menus())

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    return render_template('admin/page_edit.html',
                           sections=app.config['NAV_TOP_SECTIONS'],
                           page=page,
                           form=form)


@bp.route('/page/draft/<int:page_id>')
@auth_manager.check_access('admin', 'content')
def page_draft(page_id):
    page = Page.query.filter(Page.id == page_id).first()
    if not page:
        abort(404)

    if not page.content:
        abort(404)

    return render_template('page.html',
                           page=page)


@bp.route('/page/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin')
def page_add():
    form = PageForm()
    if form.is_submitted() and form.validate():
        slug = form.slug.data
        if len(slug) <= 0:
            slug = slugify(form.title.data)

        # ensure slug is unique, add - until it is
        while Page.query.filter_by(slug=slug).count() > 0:
            slug += '-'

        page = Page(
            name=form.title.data,
            slug=slug,
            content=form.content.data,
            published=form.published.data,
            menu=form.section.data)
        db.session.add(page)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        cache.set('menus', get_menus())

        revision = PageRevision(
            page_id=page.id,
            author_id=current_user.id,
            name=form.title.data,
            content=form.content.data)
        db.session.add(revision)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        flash("Page Saved")
        return redirect(url_for('admin.pages'))

    return render_template('admin/page_add.html',
                           sections=app.config['NAV_TOP_SECTIONS'],
                           form=form)


@bp.route('/article/add', methods=['GET', 'POST'])
@auth_manager.check_access('admin', 'content')
def article_add():
    form = ArticleForm()
    if form.is_submitted() and form.validate():
        slug = form.slug.data
        if len(slug) <= 0:
            slug = slugify(form.title.data)

        # ensure slug is unique, add - until it is
        while Article.query.filter_by(slug=slug).count() > 0:
            slug += '-'

        article = Article(
            title=form.title.data,
            slug=slug,
            category_id=form.category_id.data,
            author_id=form.author_id.data,
            summary=form.summary.data,
            content=form.content.data,
            published=form.published.data)
        article.front_page = form.front_page.data
        if article.published is True:
            article.datetime = datetime.datetime.utcnow()

        article.render_html()
        db.session.add(article)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        revision = ArticleRevision(
            article_id=article.id,
            author_id=current_user.id,
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data)
        revision.render_html()
        db.session.add(revision)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        flash("Article Saved")
        return redirect(url_for('admin.articles'))

    categories = Category.query.all()
    authors = User.query.all()
    return render_template('admin/article_add.html',
                           categories=categories,
                           authors=authors,
                           form=form)


@bp.route('/article/<int:art_id>', methods=['GET', 'POST', 'DELETE'])
@auth_manager.check_access('admin', 'content')
def article_edit(art_id):
    article = Article.query.get_or_404(art_id)
    form = ArticleForm()
    if request.method == 'POST' and form.validate():
        slug = form.slug.data
        if len(slug) <= 0:
            slug = slugify(form.title.data)

        # ensure slug is unique, add - until it is (if we're changing the slug)
        if article.slug != slug:
            while Article.query.filter(db.and_(
                    Article.slug == slug,
                    Article.id != article.id)).count() > 0:
                slug += '-'

        article.title = form.title.data
        article.slug = slug
        article.category_id = form.category_id.data
        article.author_id = form.author_id.data
        article.published = form.published.data
        article.summary = form.summary.data
        article.content = form.content.data
        article.front_page = form.front_page.data
        article.render_html()

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        revision = ArticleRevision(
            article_id=article.id,
            author_id=current_user.id,
            title=form.title.data,
            summary=form.summary.data,
            content=form.content.data)
        revision.render_html()
        db.session.add(revision)

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        flash("Article Saved")
        return redirect(url_for('admin.articles'))
    elif request.method == 'DELETE':
        db.session.delete(article)
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        return jsonify({
            '_csrf_token': app.jinja_env.globals['csrf_token'](),
        })

    categories = Category.query.all()
    authors = User.query.all()
    return render_template('admin/article_edit.html',
                           article=article,
                           categories=categories,
                           authors=authors,
                           form=form)


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
        if 'set_paid' in request.form:
            # TODO log who set as paid
            o = Order.query.get(request.form["id"])
            o.set_paid(method="check")
            db.session.add(o)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

        # TODO support setting asynchronously, rather than redirecting
        if 'set_shipped' in request.form:
            # TODO log who set as paid
            o = Order.query.get(request.form["id"])
            o.set_shipped()
            db.session.add(o)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

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


@bp.route('/library')
@bp.route('/library/<path:path>')
def library_redirect(path=None):
    if path is not None and len(path) > 0:
        return redirect('/trackman/library/{0}'.format(path))
    else:
        return redirect('/trackman/library/index')


@bp.route('/donate/csv')
@auth_manager.check_access('business')
def donate_csv_download():
    csvHeaders = ["id", "name", "email", "phone", "date", "address",
                  "useragent", "dj", "thanks", "firsttime", "dcomment",
                  "premiums", "address1", "address2", "city", "state", "zip",
                  "amount", "recurring", "paiddate", "shippeddate",
                  "shirtsize", "shirtcolor", "sweatshirtsize", "method",
                  "custid", "donor_comment"]
    orders = Order.query.\
        order_by(db.desc(Order.id))
    f = io.StringIO()
    writer = csv.writer(f)
    writer.writerow(csvHeaders)
    for o in orders:
        fields = [o.id, o.name, o.email, o.phone, o.placed_date, o.remote_addr,
                  o.user_agent, o.dj, o.thank_on_air, o.first_time,
                  o.donor_comment, o.premiums, o.address1, o.address2, o.city,
                  o.state, o.zipcode, o.amount, o.recurring, o.paid_date,
                  o.shipped_date, o.tshirtsize, o.tshirtcolor, o.sweatshirtsize,
                  o.method, o.custid, o.donor_comment]
        writer.writerow(fields)
    f.seek(0)
    filename = "donor-premiums.csv"
    return f.read(), {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition":
            "attachment; filename=\"{0}\"".format(filename),
    }
