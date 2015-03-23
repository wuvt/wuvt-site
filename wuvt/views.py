from flask import abort, flash, jsonify, render_template, redirect, \
    request, url_for, Response, send_from_directory

from sqlalchemy import desc

from wuvt import app
from wuvt import db
from wuvt import sse

from wuvt.models import User, Page
from wuvt.blog.models import Article, Category

from wuvt.blog.views import *
from wuvt.trackman.views import *


@app.context_processor
def inject_menus():
    menus = {}
    pages = db.session.query(Page.name, Page.slug, Page.menu).\
        filter(Page.menu is not None).order_by(Page.name).all()
    for page in pages:
        menu = str(page.menu)
        if menu not in menus:
            menus[menu] = []
        menus[menu].append(page)

    return {'menus': menus}


@app.route('/index.php')
def redir_index():
    return redirect(url_for('index'))


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/')
@app.route('/index/<int:page>')
def index(page=1):
    articles = Article.query.filter_by(published=True, front_page=True).\
        order_by(desc(Article.datetime)).paginate(page,
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
    if request.headers.get('accept') == 'text/event-stream':
        response = Response(sse.event_stream(), mimetype="text/event-stream",
                            headers={'X-Accel-Buffering': "no"})
        return response
    else:
        abort(400)


@app.errorhandler(400)
def error400(error):
    return render_template('error400.html'), 400


@app.errorhandler(403)
def error403(error):
    return render_template('error403.html'), 403


@app.errorhandler(404)
def error404(error):
    return render_template('error404.html'), 404


@app.errorhandler(405)
def error405(error):
    return render_template('error405.html'), 405
