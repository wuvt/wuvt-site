from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf

from wuvt import app
from wuvt import db
from wuvt import lib

from wuvt.models import User
from wuvt.blog.models import Article, Category


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
    return render_template('index.html', categories=categories,
            articles=articles)


@app.route('/article/<string:slug>')
def article(slug):
    article = Article.query.filter(Article.slug == slug).first()
    if not article:
        abort(404)

    categories = Category.query.order_by(Category.name).all()
    return render_template('index.html', categories=categories,
            articles=[article])
