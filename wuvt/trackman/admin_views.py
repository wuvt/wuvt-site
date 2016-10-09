from flask import current_app, flash, json, jsonify, render_template, \
        redirect, request, session, url_for, make_response

import datetime

from .. import db, redis_conn
from ..view_utils import local_only, sse_response
from . import private_bp, mail
from .lib import disable_automation, enable_automation, logout_all_except
from .models import DJ, DJSet, Track, TrackLog, Rotation, TrackReport
from .view_utils import dj_interact


@private_bp.route('/', methods=['GET', 'POST'])
@local_only
def login():
    if 'dj' in request.form and len(request.form['dj']) > 0:
        disable_automation()

        dj = DJ.query.get(request.form['dj'])

        current_app.logger.warning(
            "Trackman: {airname} logged in from {ip} using {ua}".format(
                airname=dj.airname,
                ip=request.remote_addr,
                ua=request.user_agent))

        # close open DJSets, and see if we have one we can use
        djset = logout_all_except(dj.id)
        if djset is None:
            djset = DJSet(dj.id)
            db.session.add(djset)
            db.session.commit()

        session['djset_id'] = djset.id

        return redirect(url_for('.log', setid=djset.id))

    automation = redis_conn.get('automation_enabled') == "true"

    djs = DJ.query.filter(DJ.visible == True).order_by(DJ.airname).all()
    return render_template('trackman/login.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           automation=automation, djs=djs)


@private_bp.route('/automation/start', methods=['POST'])
@local_only
def start_automation():
    automation = redis_conn.get('automation_enabled') == "true"
    if not automation:
        enable_automation()

        current_app.logger.warning(
            "Trackman: Automation started from {ip} using {ua}".format(
                ip=request.remote_addr,
                ua=request.user_agent))

    return redirect(url_for('.login'))


@private_bp.route('/log/<int:setid>')
@local_only
@dj_interact
def log(setid):
    djset = DJSet.query.get_or_404(setid)
    if djset.dtend is not None:
        # This is a logged out DJSet

        if setid == session.get('djset_id', None):
            flash("""\
Your session has ended; you were either automatically logged out for inactivity
or you pressed the Logout button somewhere else.
""")
            session.pop('djset_id', None)

        return redirect(url_for('.login'))

    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation
    return render_template('trackman/log.html',
                           trackman_name=current_app.config['TRACKMAN_NAME'],
                           djset=djset,
                           rotations=rotations)


@private_bp.route('/js/log/<int:setid>.js')
@local_only
def log_js(setid):
    djset = DJSet.query.get_or_404(setid)
    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation

    resp = make_response(render_template('trackman/log.js',
                         trackman_name=current_app.config['TRACKMAN_NAME'],
                         djset=djset,
                         rotations=rotations))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@private_bp.route('/report/<int:dj_id>/<int:track_id>', methods=['GET', 'POST'])
@local_only
@dj_interact
def report_track(dj_id, track_id):
    track = Track.query.get_or_404(track_id)
    dj = DJ.query.get_or_404(dj_id)
    if request.method == 'GET':
        return render_template('trackman/report.html', track=track, dj=dj,
                               trackman_name=current_app.config['TRACKMAN_NAME'])
    else:
        # This is a POST
        if 'reason' not in request.form:
            return render_template('trackman/report.html', track=track, dj=dj,
                                   trackman_name=current_app.config['TRACKMAN_NAME'],
                                   error="A reason is required")

        reason = request.form['reason'].strip()
        if len(reason) == 0:
            return render_template('trackman/report.html', track=track, dj=dj,
                                   trackman_name=current_app.config['TRACKMAN_NAME'],
                                   error="A reason is required")

        report = TrackReport(dj_id, track_id, reason)
        db.session.add(report)
        db.session.commit()
        return render_template('trackman/reportsuccess.html', dj=dj)


@private_bp.route('/log/<int:setid>/end', methods=['POST'])
@local_only
def logout(setid):
    session.pop('djset_id', None)

    djset = DJSet.query.get_or_404(setid)
    if djset.dtend is None:
        djset.dtend = datetime.datetime.utcnow()
    else:
        # This has already been logged out
        return redirect(url_for('.login'))
    db.session.commit()

    redis_conn.publish('trackman_dj_live', json.dumps({
        'event': "session_end",
    }))

    # Reset the dj activity timeout period
    redis_conn.delete('dj_timeout')

    # Set dj_active expiration to NO_DJ_TIMEOUT to reduce automation start time
    redis_conn.set('dj_active', 'false')
    redis_conn.expire('dj_active', int(current_app.config['NO_DJ_TIMEOUT']))

    # email playlist
    if 'email_playlist' in request.form and \
            request.form.get('email_playlist') == 'true':
        tracks = TrackLog.query.filter(TrackLog.djset_id == djset.id).order_by(
            TrackLog.played).all()
        mail.send_playlist(djset, tracks)

    if request.wants_json():
        return jsonify(success=True)
    else:
        return redirect(url_for('.login'))


@private_bp.route('/register', methods=['GET', 'POST'])
@local_only
def register():
    errors = {}

    if request.method == 'POST':
        airname = request.form['airname'].strip()
        if len(airname) <= 0:
            errors['airname'] = "You must enter an on-air name."

        matching = DJ.query.filter(DJ.airname == airname).count()
        print(matching)
        if matching > 0:
            errors['airname'] = "Your on-air name must be unique."

        name = request.form['name'].strip()
        if len(name) <= 0:
            errors['name'] = "You must enter your name."

        email = request.form['email'].strip()
        if len(email) <= 0:
            errors['email'] = "You must enter your email address."

        phone = request.form['phone'].strip()
        if len(phone) <= 0:
            errors['phone'] = "You must enter your phone number."

        genres = request.form['genres'].strip()
        if len(genres) <= 0:
            errors['genres'] = "You must enter the genres you can DJ."

        if len(errors.items()) <= 0:
            newdj = DJ(airname, name)
            newdj.email = email
            newdj.phone = phone
            newdj.genres = genres
            db.session.add(newdj)
            db.session.commit()

            flash("DJ added")
            return redirect(url_for('.login'))

    if request.wants_json():
        if len(errors) <= 0:
            return jsonify(success=True)
        else:
            return jsonify(success=False, errors=errors)
    else:
        return render_template(
            'trackman/register.html',
            trackman_name=current_app.config['TRACKMAN_NAME'],
            errors=errors)


@private_bp.route('/api/live')
@local_only
def dj_live():
    return sse_response('trackman_dj_live')
