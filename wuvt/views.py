from flask import abort, flash, jsonify, make_response, render_template, \
    redirect, request, url_for, Response, send_from_directory
import socket
import urlparse

from . import app
from . import db
from .models import User, Page
from .blog.models import Article, Category
from .blog.views import *
from .view_utils import IPAccessDeniedException


@app.context_processor
def inject_menus():
    menus = {}
    pages = db.session.query(Page.name, Page.slug, Page.menu, Page.published).\
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
        order_by(db.desc(Article.datetime)).paginate(page,
                                              app.config['POSTS_PER_PAGE'])
    return render_template('index.html', articles=articles)


@app.route('/<string:slug>')
def page(slug):
    page = Page.query.filter(Page.slug == slug).first()
    if not page:
        abort(404)

    return render_template('page.html', page=page)


@app.route('/js/init.js')
def init_js():
    resp = make_response(render_template('init.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@app.route('/live')
def livestream():
    if request.headers.get('accept') == 'text/event-stream':
        # uwsgi-sse-offload requires that we resolve hostnames for it.
        u = urlparse.urlparse(app.config['REDIS_URL']).netloc.split(':', 1)
        server = u[0]
        port = int(u[1])

        if ':' not in server:
            # Unfortunately, we have to assume that the first entry in DNS
            # works; we use gethostbyname since redis only listens on IPv4
            # by default. You can work around this by specifying an IPv6
            # address directly.
            server = socket.gethostbyname(server)
            #addrinfo = socket.getaddrinfo(u[0], port)
            #server = addrinfo[0][4][0]

        return Response("", mimetype="text/event-stream", headers={
            'Cache-Control': "no-cache",
            'X-SSE-Offload': 'y',
            'X-SSE-Server': '{0}:{1}'.format(server, port),
            'X-SSE-Channel': "trackman_live",
        })
    else:
        abort(400)


@app.errorhandler(400)
def error400(error):
    if request.wants_json():
        return jsonify({'errors': "400 Bad Request"}), 400

    return render_template('error400.html'), 400


@app.errorhandler(403)
def error403(error):
    if request.wants_json():
        return jsonify({'errors': "403 Forbidden"}), 403

    return render_template('error403.html'), 403


@app.errorhandler(404)
def error404(error):
    if request.wants_json():
        return jsonify({'errors': "404 Not Found"}), 404

    return render_template('error404.html'), 404


@app.errorhandler(405)
def error405(error):
    if request.wants_json():
        return jsonify({'errors': "405 Method Not Allowed"}), 405

    return render_template('error405.html'), 405


@app.errorhandler(IPAccessDeniedException)
def error403_ipaccess(error):
    if request.wants_json():
        return jsonify({'errors': "403 Forbidden"}), 403

    return render_template('error403_ipaccess.html'), 403
