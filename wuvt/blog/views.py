from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf
from urlparse import urljoin
from werkzeug.contrib.atom import AtomFeed

from wuvt import app
from wuvt import db
from wuvt import lib

from wuvt.models import User
from wuvt.blog.models import Article, Category


def make_external(url):
    return urljoin(request.url_root, url)


@app.context_processor
def inject_categories():
    categories = Category.query.filter(Category.parent_id == 0).\
            order_by(Category.name).all()
    return {'categories': categories}


@app.route('/category/<string:slug>')
def category(slug):
    category = Category.query.filter(Category.slug == slug).first()
    if not category:
        abort(404)

    categories = Category.query.filter(Category.parent_id == category.id).\
            order_by(Category.name).all()
    articles = Article.query.filter(Article.category_id == category.id).\
            order_by(db.asc(Article.id)).all()
    return render_template('index.html', #categories=categories,
            articles=articles, feedlink=url_for('category_feed', slug=slug))


@app.route('/category/<string:slug>.atom')
def category_feed(slug):
    category = Category.query.filter(Category.slug == slug).first()
    if not category:
        abort(404)

    feed = AtomFeed("WUVT: {0}".format(category.name),
            feed_url=request.url, url=request.url_root)

    articles = Article.query.filter(Article.category_id == category.id).\
            order_by(db.asc(Article.id)).all()
    for article in articles:
        feed.add(article.title, unicode(article.content),
                content_type='html',
                author=article.author.name,
                url=make_external(url_for('article', slug=article.slug)),
                updated=article.datetime,
                published=article.datetime)

    return feed.get_response()


@app.route('/article/<string:slug>')
def article(slug):
    article = Article.query.filter(Article.slug == slug).first()
    if not article:
        abort(404)

    categories = Category.query.\
            filter(Category.parent_id == article.category.parent_id).\
            order_by(Category.name).all()
    return render_template('index.html', categories=categories,
            articles=[article])

@app.route('/feed.atom')
def all_feed():
    feed = AtomFeed("WUVT: Recent Articles", feed_url=request.url,
            url=request.url_root)

    articles = Article.query.order_by(db.asc(Article.id)).limit(15).all()
    for article in articles:
        feed.add(article.title, unicode(article.content),
                content_type='html',
                author=article.author.name,
                url=make_external(url_for('article', slug=article.slug)),
                updated=article.datetime,
                published=article.datetime)

    return feed.get_response()
