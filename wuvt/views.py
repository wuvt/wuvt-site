from flask import abort, jsonify, make_response, render_template, request, \
        send_from_directory
import redis.exceptions
import sqlalchemy.exc

from . import app, cache, db, redis_conn
from .models import Page
from .view_utils import IPAccessDeniedException


def get_menus():
    menus = {}
    pages = Page.query.\
        with_entities(Page.name, Page.slug, Page.menu, Page.published).\
        filter(Page.menu is not None).order_by(Page.name).all()
    for page in pages:
        menu = str(page.menu)
        if menu not in menus:
            menus[menu] = []
        menus[menu].append(page)

    return menus


@app.context_processor
def inject_menus():
    menus = cache.get('menus')
    if menus is None:
        menus = get_menus()
        cache.set('menus', menus)

    return {'menus': menus}


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/<string:slug>')
def page(slug):
    page = Page.query.filter(Page.slug == slug).first()
    if not page or page.published == False:
        abort(404)

    return render_template('page.html', page=page)


@app.route('/js/init.js')
def init_js():
    resp = make_response(render_template('init.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


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


@app.errorhandler(500)
def error500(error):
    if request.wants_json():
        return jsonify({'errors': "500 Internal Server Error"}), 500

    return render_template('error500.html'), 500


@app.route('/healthz')
def healthcheck():
    try:
        db_status = db.session.scalar(db.select([1]))
    except sqlalchemy.exc.DBAPIError:
        db_status = None

    try:
        redis_status = redis_conn.info()
    except redis.exceptions.ConnectionError:
        redis_status = None

    if db_status is not None and redis_status is not None:
        return "OK"
    else:
        return "fail", 500
