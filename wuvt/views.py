from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf

from wuvt import app
from wuvt import lib

from wuvt.models import User
from wuvt.blog.models import Article, Category
from wuvt.trackman.views import *


@app.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    articles = Article.query.order_by(db.asc(Article.id)).limit(5).all()
    return render_template('index.html', categories=categories,
            articles=articles)


@app.route('/category/<string:slug>')
def category(slug):
    # TODO: implement
    categories = Category.query.order_by(Category.name).all()
    return render_template('index.html', categories=categories)


@app.route('/live')
def livestream():
    response = Response(sse.event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = "no-cache"
    response.headers['Connection'] = "keep-alive"
    response.headers['X-Accel-Buffering'] = "no"
    return response
