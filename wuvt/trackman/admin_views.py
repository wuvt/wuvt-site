from flask import current_app, flash, json, jsonify, render_template, \
        redirect, request, session, url_for, make_response, abort

import datetime

from .. import db, redis_conn
from ..view_utils import local_only, sse_response
from . import private_bp, mail
from .forms import DJRegisterForm, DJReactivateForm
from .lib import enable_automation, check_onair
from .models import DJ, DJSet, TrackLog, Rotation


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
        return redirect(url_for('.log'))

    automation = redis_conn.get('automation_enabled') == "true"

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
        return redirect(url_for('.log'))

    automation = redis_conn.get('automation_enabled') == "true"

    djs = DJ.query.order_by(DJ.airname).all()
    return render_template('trackman/login_all.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           automation=automation, djs=djs)


@private_bp.route('/automation/start', methods=['POST'])
@local_only
def start_automation():
    automation = redis_conn.get('automation_enabled') == "true"
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

            flash("""\
Your session has ended; you were either automatically logged out for inactivity
or you pressed the Logout button somewhere else.
""")
            session.pop('dj_id', None)
            session.pop('djset_id', None)

            return redirect(url_for('.login'))

    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation
    return render_template('trackman/log.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           dj=dj,
                           rotations=rotations)


@private_bp.route('/js/log.js')
@local_only
def log_js():
    dj_id = session.get('dj_id', None)
    if dj_id is None:
        abort(404)

    djset_id = session.get('djset_id', None)

    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation

    resp = make_response(render_template('trackman/log.js',
                         trackman_name=current_app.config['TRACKMAN_NAME'],
                         dj_id=dj_id, djset_id=djset_id,
                         rotations=rotations))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@private_bp.route('/logout', methods=['POST'])
@local_only
def logout():
    dj_id = session.pop('dj_id', None)
    if dj_id is None:
        abort(404)

    djset_id = session.pop('djset_id', None)
    if djset_id is not None:
        djset = DJSet.query.get_or_404(djset_id)
        if djset.dtend is None:
            djset.dtend = datetime.datetime.utcnow()

            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

            redis_conn.publish('trackman_dj_live', json.dumps({
                'event': "session_end",
            }))

        if check_onair(djset_id):
            redis_conn.delete('onair_djset_id')

        # Reset the dj activity timeout period
        redis_conn.delete('dj_timeout')

        # Set dj_active expiration to NO_DJ_TIMEOUT to reduce automation start
        # time
        redis_conn.set('dj_active', 'false')
        redis_conn.expire(
            'dj_active', int(current_app.config['NO_DJ_TIMEOUT']))

        # email playlist
        if 'email_playlist' in request.form and \
                request.form.get('email_playlist') == 'true':
            tracks = TrackLog.query.\
                filter(TrackLog.djset_id == djset.id).\
                order_by(TrackLog.played).all()
            mail.send_playlist(djset, tracks)

    if request.wants_json():
        return jsonify(success=True)
    else:
        return redirect(url_for('.login'))


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
