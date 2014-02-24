from flask import abort, flash, jsonify, render_template, redirect, \
    request, url_for, Response

from wuvt import app
from wuvt import db
from wuvt import login_manager
from wuvt import sse

from wuvt.models import User, Page
from wuvt.blog.models import Article, Category

from wuvt.blog.views import *
from wuvt.trackman.views import *


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


@app.context_processor
def inject_menus():
    menus = {}
    pages = db.session.query(Page.name, Page.slug, Page.menu).\
        filter(Page.menu is not None).all()
    for page in pages:
        menu = str(page.menu)
        if menu not in menus:
            menus[menu] = []
        menus[menu].append(page)

    return {'menus': menus}


@app.route('/')
@app.route('/index/<int:page>')
def index(page=1):
    articles = Article.query.order_by(db.asc(Article.id)).paginate(
        page,
        app.config['POSTS_PER_PAGE'])
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


@app.errorhandler(403)
def error403(error):
    return render_template('error403.html'), 403


@app.errorhandler(404)
def error404(error):
    return render_template('error404.html'), 404
