from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf

from wuvt import app
from wuvt import db
from wuvt import lib

from wuvt.models import User, Page
from wuvt.blog.models import Article, Category
from wuvt.blog.views import *
from wuvt.trackman.views import *


@app.route('/')
def index():
    articles = Article.query.order_by(db.asc(Article.id)).limit(5).all()
    return render_template('index.html', articles=articles)


@app.route('/<string:slug>')
def page(slug):
    page = Page.query.filter(Page.slug == slug).first()
    if not page:
        abort(404)

    return render_template('page.html', page=page)


@app.route('/live')
def livestream():
    response = Response(sse.event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = "no-cache"
    response.headers['Connection'] = "keep-alive"
    response.headers['X-Accel-Buffering'] = "no"
    return response


@app.errorhandler(404)
def error404(error):
    return render_template('error404.html'), 404
