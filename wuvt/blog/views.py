from flask import abort, current_app, redirect, render_template, request, \
        url_for
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from .. import cache, db
from . import bp
from .models import Article, Category


def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return [c.serialize() for c in categories]


def list_categories_cached():
    data = cache.get('blog_categories')
    if data is None:
        data = list_categories()
        cache.set('blog_categories', data)

    return data


def make_external(url):
    return urljoin(request.url_root, url)


@bp.route('/category/<string:slug>')
@bp.route('/category/<string:slug>/<int:page>')
def category(slug, page=1):
    category = Category.query.filter(Category.slug == slug).first()
    if not category:
        abort(404)

    articles = Article.query.filter(Article.category_id == category.id).\
        filter_by(published=True).\
        order_by(db.desc(Article.datetime)).\
        paginate(page, current_app.config['POSTS_PER_PAGE'])

    return render_template('category.html',
                           category=category,
                           articles=articles,
                           feedlink=url_for('.category_feed', slug=slug))


@bp.route('/category/<string:slug>.atom')
def category_feed(slug):
    category = Category.query.filter(Category.slug == slug).first()
    if not category:
        abort(404)

    feed = AtomFeed(
        "{station_name}: {category}".format(
            station_name=current_app.config['STATION_NAME'],
            category=category.name),
        feed_url=request.url,
        url=request.url_root)

    articles = Article.query.filter(Article.category_id == category.id).\
        filter_by(published=True).order_by(db.desc(Article.datetime)).all()
    for article in articles:
        feed.add(article.title, unicode(article.html_content),
                 content_type='html',
                 author=article.author.name,
                 url=make_external(url_for('.article', slug=article.slug)),
                 updated=article.datetime,
                 published=article.datetime)

    return feed.get_response()


@bp.route('/article/<string:slug>')
def article(slug):
    article = Article.query.filter(Article.slug == slug).first()
    if not article or not article.published:
        abort(404)

    if not article.content:
        article.content = article.summary

    categories = Category.query.order_by(Category.name).all()
    return render_template('article.html',
                           categories=categories,
                           article=article)


@bp.route('/')
@bp.route('/index/<int:page>')
def index(page=1):
    articles = Article.query.filter_by(published=True, front_page=True).\
        order_by(db.desc(Article.datetime)).paginate(
            page,
            current_app.config['POSTS_PER_PAGE'])
    return render_template('index.html', articles=articles)


@bp.route('/index.php')
def redir_index():
    return redirect(url_for('.index'))


@bp.route('/feed.atom')
def all_feed():
    feed = AtomFeed(
        "{0}: Recent Articles".format(current_app.config['STATION_NAME']),
        feed_url=request.url,
        url=request.url_root)

    articles = Article.query.filter_by(published=True).\
        order_by(db.desc(Article.datetime)).limit(15).all()
    for article in articles:
        feed.add(article.title, unicode(article.html_content or article.html_summary),
                 content_type='html',
                 author=article.author.name,
                 url=make_external(url_for('.article', slug=article.slug)),
                 updated=article.datetime,
                 published=article.datetime)

    return feed.get_response()
