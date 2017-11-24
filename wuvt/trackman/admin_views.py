from flask import current_app, flash, jsonify, render_template, \
        redirect, request, session, url_for, make_response, abort

from .. import db, redis_conn
from . import private_bp
from .forms import DJRegisterForm, DJReactivateForm
from .lib import enable_automation, renew_dj_lease
from .models import DJ, DJSet
from .view_utils import local_only, sse_response


@private_bp.route('/', methods=['GET', 'POST'])
@local_only
def login():
    if 'dj' in request.form and len(request.form['dj']) > 0:
        dj = DJ.query.get(request.form['dj'])

        current_app.logger.warning(
            "Trackman: {airname} logged in from {ip} using {ua}".format(
                airname=dj.airname,
                ip=request.remote_addr,
                ua=request.user_agent))

        session['dj_id'] = dj.id
        renew_dj_lease()

        return redirect(url_for('.log'))

    automation = redis_conn.get('automation_enabled') == b"true"

    djs = DJ.query.filter(DJ.visible == True).order_by(DJ.airname).all()
    return render_template('trackman/login.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           automation=automation, djs=djs)


@private_bp.route('/login/all', methods=['GET', 'POST'])
@local_only
def login_all():
    if 'dj' in request.form and len(request.form['dj']) > 0:
        if int(request.form['dj']) == 1:
            # start automation if we selected DJ with ID 1
            return redirect(url_for('.start_automation'), 307)

        dj = DJ.query.get(request.form['dj'])
        dj.visible = True
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        current_app.logger.warning(
            "Trackman: {airname} logged in from {ip} using {ua}".format(
                airname=dj.airname,
                ip=request.remote_addr,
                ua=request.user_agent))

        session['dj_id'] = dj.id
        renew_dj_lease()

        return redirect(url_for('.log'))

    automation = redis_conn.get('automation_enabled') == b"true"

    djs = DJ.query.order_by(DJ.airname).all()
    return render_template('trackman/login_all.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           automation=automation, djs=djs)


@private_bp.route('/automation/start', methods=['POST'])
@local_only
def start_automation():
    automation = redis_conn.get('automation_enabled') == b"true"
    if not automation:
        current_app.logger.warning(
            "Trackman: Start automation from {ip} using {ua}".format(
                ip=request.remote_addr,
                ua=request.user_agent))

        enable_automation()

    return redirect(url_for('.login'))


@private_bp.route('/log')
@local_only
def log():
    dj_id = session.get('dj_id', None)
    if dj_id is None:
        return redirect(url_for('.login'))

    dj = DJ.query.get_or_404(dj_id)
    if dj.phone is None or dj.email is None:
        return redirect(url_for('.reactivate_dj'))

    djset_id = session.get('djset_id', None)
    if djset_id is not None:
        djset = DJSet.query.get_or_404(djset_id)
        if djset.dtend is not None:
            # This is a logged out DJSet
            session.pop('djset_id', None)

    renew_dj_lease()

    return render_template('trackman/log.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           dj=dj)


@private_bp.route('/js/log.js')
@local_only
def log_js():
    dj_id = session.get('dj_id', None)
    if dj_id is None:
        abort(404)

    djset_id = session.get('djset_id', None)

    resp = make_response(render_template('trackman/log.js',
                         trackman_name=current_app.config['TRACKMAN_NAME'],
                         dj_id=dj_id, djset_id=djset_id))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@private_bp.route('/register', methods=['GET', 'POST'])
@local_only
def register():
    form = DJRegisterForm()
    if form.is_submitted():
        if form.validate():
            newdj = DJ(form.airname.data, form.name.data)
            newdj.email = form.email.data
            newdj.phone = form.phone.data
            newdj.genres = form.genres.data
            db.session.add(newdj)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

            if request.wants_json():
                return jsonify(success=True)
            else:
                flash("DJ added")
                return redirect(url_for('.login'))
        elif request.wants_json():
            return jsonify(success=False, errors=form.errors)

    return render_template(
        'trackman/register.html',
        trackman_name=current_app.config['TRACKMAN_NAME'],
        form=form)


@private_bp.route('/reactivate_dj', methods=['GET', 'POST'])
@local_only
def reactivate_dj():
    dj_id = session.get('dj_id', None)
    if dj_id is None:
        return redirect(url_for('.login'))

    dj = DJ.query.get_or_404(dj_id)
    form = DJReactivateForm()

    # if neither phone nor email is missing, someone is doing silly things
    if dj.email is not None and dj.phone is not None:
        return redirect(url_for('.log'))

    if form.is_submitted():
        if form.validate():
            dj.email = form.email.data
            dj.phone = form.phone.data
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

            if request.wants_json():
                return jsonify(success=True)
            else:
                return redirect(url_for('.log'))
        elif request.wants_json():
            return jsonify(success=False, errors=form.errors)

    return render_template(
        'trackman/reactivate.html',
        trackman_name=current_app.config['TRACKMAN_NAME'],
        form=form,
        dj=dj)


@private_bp.route('/api/live')
@local_only
def dj_live():
    return sse_response('trackman_dj_live')
