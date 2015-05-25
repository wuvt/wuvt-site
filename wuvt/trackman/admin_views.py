from flask import flash, jsonify, render_template, redirect, request, \
    url_for, make_response
from sqlalchemy import func, desc

import datetime
import dateutil.parser

from wuvt import app
from wuvt import db
from wuvt import csrf
from wuvt import redis_conn
from wuvt.trackman import bp
from wuvt.trackman.lib import log_track, email_playlist, disable_automation, \
        enable_automation, logout_all, logout_all_but_current
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog, AirLog, Rotation, \
        TrackReport
from wuvt.trackman.view_utils import local_only, dj_interact


#############################################################################
### Login
#############################################################################

@bp.route('/', methods=['GET', 'POST'])
@local_only
@dj_interact
def login():
    if 'dj' in request.form and len(request.form['dj']) > 0:
        disable_automation()

        dj = DJ.query.get(request.form['dj'])

        # close open DJSets, and see if we have one we can use
        djset = logout_all_but_current(dj)
        if djset is None:
            djset = DJSet(dj.id)
            db.session.add(djset)
            db.session.commit()

        return redirect(url_for('trackman.log', setid=djset.id))

    automation = redis_conn.get('automation_enabled') == "true"

    djs = DJ.query.filter(DJ.visible == True).order_by(DJ.airname).all()
    return render_template('trackman/login.html',
                           trackman_name=app.config['TRACKMAN_NAME'],
                           automation=automation, djs=djs)


#############################################################################
### Automation Control
#############################################################################


@bp.route('/automation/start', methods=['POST'])
@local_only
def start_automation():
    logout_all()
    enable_automation()

    return redirect(url_for('trackman.login'))


@bp.route('/api/automation/log', methods=['POST'])
@local_only
@csrf.exempt
def automation_log():
    if 'password' not in request.form or \
            request.form['password'] != app.config['AUTOMATION_PASSWORD']:
        return jsonify(success=False, error="Invalid password")

    automation = redis_conn.get('automation_enabled') == "true"
    if not automation:
        return jsonify(success=False, error="Automation not enabled")

    if 'title' in request.form and len(request.form['title']) > 0:
        title = request.form['title'].strip()
    else:
        title = "Not Available"

    if 'artist' in request.form and len(request.form['artist']) > 0:
        artist = request.form['artist'].strip()
    else:
        artist = "Not Available"

    if 'album' in request.form and len(request.form['album']) > 0:
        album = request.form['album'].strip()
    else:
        album = "Not Available"

    if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr", "ua"):
        # TODO: implement airlog logging
        return jsonify(success=False,
                       error='AirLog logging not yet implemented')

    if 'label' in request.form and len(request.form['label']) > 0:
        label = request.form['label'].strip()
        tracks = Track.query.filter(Track.title == title).filter(Track.artist == artist).filter(Track.album == album).filter(Track.label == label)
        if len(tracks.all()) == 0:
            track = Track(title, artist, album, label)
            db.session.add(track)
            db.session.commit()
        else:
            track = tracks.first()

    else:
        # Handle automation not providing a label
        label = "Not Available"
        tracks = Track.query.filter(Track.title == title).filter(Track.artist == artist).filter(Track.album == album)
        if len(tracks.all()) == 0:
            track = Track(title, artist, album, label)
            db.session.add(track)
            db.session.commit()
        else:
            notauto = tracks.filter(Track.label != "Not Available")
            if len(notauto.all()) == 0:
                # The only option is "not available label"
                track = tracks.first()
            else:
                track = notauto.first()

    djset_id = redis_conn.get('automation_set')
    if djset_id != None:
        djset_id = int(djset_id)
    log_track(track.id, djset_id)

    return jsonify(success=True)


#############################################################################
### DJ Control
#############################################################################


@bp.route('/log/<int:setid>')
@local_only
def log(setid):
    djset = DJSet.query.get_or_404(setid)
    if djset.dtend is not None:
        # This is a logged out DJSet
        return redirect(url_for('trackman.login'))

    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation
    return render_template('trackman/log.html',
                           trackman_name=app.config['TRACKMAN_NAME'],
                           djset=djset,
                           rotations=rotations)

@bp.route('/js/log/<int:setid>.js')
def log_js(setid):
    djset = DJSet.query.get_or_404(setid)
    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation

    resp = make_response(render_template('trackman/log.js',
                           trackman_name=app.config['TRACKMAN_NAME'],
                           djset=djset,
                           rotations=rotations))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/edit/<int:tracklog_id>', methods=['GET'])
@local_only
def edit(tracklog_id):
    track = TrackLog.query.get_or_404(tracklog_id)

    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation

    return render_template('trackman/edit.html',
                           trackman_name=app.config['TRACKMAN_NAME'],
                           rotations=rotations, track=track)


@bp.route('/report/<int:dj_id>/<int:track_id>', methods=['GET', 'POST'])
@local_only
@dj_interact
def report_track(dj_id, track_id):
    track = Track.query.get_or_404(track_id)
    dj = DJ.query.get_or_404(dj_id)
    if request.method == 'GET':
        return render_template('trackman/report.html', track=track, dj=dj,
                               trackman_name=app.config['TRACKMAN_NAME'])
    else:
        # This is a POST
        if 'reason' not in request.form:
            return render_template('trackman/report.html', track=track, dj=dj,
                                   trackman_name=app.config['TRACKMAN_NAME'],
                                   error="A reason is required")

        reason = request.form['reason'].strip()
        if len(reason) == 0:
            return render_template('trackman/report.html', track=track, dj=dj,
                                   trackman_name=app.config['TRACKMAN_NAME'],
                                   error="A reason is required")

        report = TrackReport(dj_id, track_id, reason)
        db.session.add(report)
        db.session.commit()
        return render_template('trackman/reportsuccess.html', dj=dj)


@bp.route('/log/<int:setid>/end', methods=['POST'])
@local_only
def logout(setid):
    djset = DJSet.query.get_or_404(setid)
    if djset.dtend is None:
        djset.dtend = datetime.datetime.utcnow()
    else:
        # This has already been logged out
        return redirect(url_for('trackman.login'))
    db.session.commit()

    # Reset the dj activity timeout period
    redis_conn.delete('dj_timeout')

    # email playlist
    if 'email_playlist' in request.form and request.form.get('email_playlist') == 'true':
        email_playlist(djset)

    return redirect(url_for('trackman.login'))


@bp.route('/register', methods=['GET', 'POST'])
@local_only
def register():
    errors = {}

    if request.method == 'POST':
        airname = request.form['airname'].strip()
        if len(airname) <= 0:
            errors['airname'] = "You must enter an on-air name."

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
            return redirect(url_for('trackman.login'))

    return render_template('trackman/register.html',
                           trackman_name=app.config['TRACKMAN_NAME'],
                           errors=errors)


#############################################################################
### Trackman API
#############################################################################


@bp.route('/api/djset/<int:djset_id>', methods=['GET'])
@local_only
@dj_interact
def get_djset(djset_id):
    djset = DJSet.query.get(djset_id)
    if not djset:
        return jsonify(success=False, error="djset_id not found")
    if djset.dtend is not None:
        return jsonify(success=False, error="Session expired, please login again")

    if request.args.get('merged', False):
        logs = [i.full_serialize() for i in djset.tracks]
        logs.extend([i.serialize() for i in djset.airlog])
        logs = sorted(logs, key=lambda log: log.get('airtime', False) if log.get('airtime', False) else log.get('played', False), reverse=False)
        return jsonify(success=True, logs=logs)
    return jsonify(success=True,
                   tracklog=[i.serialize() for i in djset.tracks],
                   airlog=[i.serialize() for i in djset.airlog])


@bp.route('/api/airlog/edit/<int:airlog_id>', methods=['DELETE', 'POST'])
@local_only
@csrf.exempt
@dj_interact
def edit_airlog(airlog_id):
    airlog = AirLog.query.get(airlog_id)
    if not airlog:
        return jsonify(success=False, error="airlog_id not found")

    if request.method is 'DELETE':
        db.session.delete(airlog)
        db.session.commit()
        return jsonify(success=True)

    # Update aired time
    airtime = request.form.get('airtime', None)
    if airtime is not None:
        airlog.airtime = dateutil.parser.parse(airtime)

    # Update integers
    logtype = request.form.get('logtype', None)
    if logtype is not None:
        airlog.request = bool(logtype)

    logid = request.form.get('logid', None)
    if logid is not None:
        airlog.request = bool(logid)

    db.session.commit()

    return jsonify(success=True)


@bp.route('/api/airlog', methods=['POST'])
@local_only
@csrf.exempt
@dj_interact
def add_airlog():
    djset_id = int(request.form['djset_id'])
    logtype = int(request.form['logtype'])
    logid = int(request.form['logid'])

    airlog = AirLog(djset_id, logtype, logid=logid)
    db.session.add(airlog)
    db.session.commit()

    return jsonify(success=True, airlog_id=airlog.id)


@bp.route('/api/tracklog/edit/<int:tracklog_id>', methods=['POST', 'DELETE'])
@local_only
@csrf.exempt
@dj_interact
def edit_tracklog(tracklog_id):
    tracklog = TrackLog.query.get(tracklog_id)
    if not tracklog:
        return jsonify(success=False, error="tracklog_id not found")
    if tracklog.djset.dtend is not None:
        return jsonify(success=False, error="Session expired, please login again")

    if request.method == 'DELETE':
        # TODO: Check if the currently playing track changed
        db.session.delete(tracklog)
        db.session.commit()
        return jsonify(success=True)

    # This is a post time to do data sanitation!
    artist = request.form.get("artist", "").strip()
    title = request.form.get("title", "").strip()
    album = request.form.get("album", "").strip()
    label = request.form.get("label", "").strip()
    is_request = request.form.get('request', 'false') != 'false'
    vinyl = request.form.get('vinyl', 'false') != 'false'
    new = request.form.get('new', 'false') != 'false'
    rotation = request.form.get("rotation", 1)

    # Validate
    if len(artist) <= 0 or len(title) <= 0 or len(album) <= 0 or \
            len(label) <= 0:
        return jsonify(
            success=False,
            error="Must fill out artist, title, album, and label field")

    # First check if the artist et. al. are the same
    if artist != tracklog.track.artist or title != tracklog.track.title or \
            album != tracklog.track.album or label != tracklog.track.label:
        # This means we try to create a new track
        track = Track(title, artist, album, label)
        if not track.validate():
            return jsonify(success=False,
                           error="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")


        db.session.add(track)
        db.session.commit()
        tracklog.track_id = track.id

    # Update played time
    played = request.form.get('played', None)
    if played is not None:
        tracklog.played = dateutil.parser.parse(played)
    # Update boolean information
    tracklog.request = is_request
    tracklog.new = new
    tracklog.vinyl = vinyl

    # Update rotation
    rotation = Rotation.query.get(rotation)
    if not rotation:
        return jsonify(
            success=False,
            error="Rotation specified by rotation_id does not exist")
    tracklog.rotation_id = rotation.id

    db.session.commit()

    return jsonify(success=True)


@bp.route('/api/tracklog', methods=['POST'])
@local_only
@csrf.exempt
@dj_interact
def play_tracklog():
    track_id = int(request.form['track_id'])
    djset_id = int(request.form['djset_id'])

    is_request = request.form.get('request', 'false') != 'false'
    vinyl = request.form.get('vinyl', 'false') != 'false'
    new = request.form.get('new', 'false') != 'false'

    rotation = request.form.get('rotation', None)
    if rotation is not None:
        rotation = Rotation.query.get(int(rotation))

    # check to be sure the track and DJSet exist
    track = Track.query.get(track_id)
    djset = DJSet.query.get(djset_id)
    if not track or not djset:
        return jsonify(success=False, error="Track or DJSet do not exist")
    if djset.dtend is not None:
        return jsonify(success=False, error="Session expired, please login again")

    tracklog = log_track(track_id, djset_id, request=is_request, vinyl=vinyl, new=new, rotation=rotation)

    return jsonify(success=True, tracklog_id=tracklog.id)


@bp.route('/api/track/edit/<int:track_id>', methods=['POST'])
@local_only
@csrf.exempt
@dj_interact
def edit_track(track_id):
    track = Track.query.get(track_id)
    if not track:
        return jsonify(success=False, error="track_id not found")

    if request.method is 'DELETE':
        db.session.delete(track)
        db.session.commit()
        return jsonify(success=True)

    artist = request.form.get('artist', None)
    if artist is not None:
        track.artist = artist.strip()
    album = request.form.get('album', None)
    if album is not None:
        track.album = album.strip()
    title = request.form.get('title', None)
    if title is not None:
        track.title = title.strip()
    label = request.form.get('label', None)
    if label is not None:
        track.label = label.strip()

    if not track.validate():
        return jsonify(success=False,
                       error="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")

    db.session.commit()
    return jsonify(success=True)


@bp.route('/api/track', methods=['POST'])
@local_only
@csrf.exempt
@dj_interact
def add_track():
    title = request.form['title'].strip()
    album = request.form['album'].strip()
    artist = request.form['artist'].strip()
    label = request.form['label'].strip()

    track = Track(title, artist, album, label)
    if not track.validate():
        return jsonify(success=False,
                       error="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")

    db.session.add(track)
    db.session.commit()
    return jsonify(success=True, track_id=track.id)


@bp.route('/api/autologout', methods=['GET', 'POST'])
@local_only
@csrf.exempt
@dj_interact
def change_autologout():
    if request.method == 'GET':
        dj_timeout = redis_conn.get('dj_timeout')
        if dj_timeout is None:
            return jsonify(success=True, autologout=True)
        else:
            return jsonify(success=True, autologout=False)
    elif request.method == 'POST':
        if 'autologout' not in request.form:
            return jsonify(success=False, error='No autologout field given in POST')
        if request.form['autologout'] == 'enable':
            redis_conn.delete('dj_timeout')
            # This needs to be reexpired now since dj_timeout changed after dj_interact
            return jsonify(success=True, autologout=True)
        else:
            redis_conn.set('dj_timeout', app.config['EXTENDED_DJ_TIMEOUT'])
            return jsonify(success=True, autologout=False)


@bp.route('/api/search', methods=['GET'])
@local_only
@dj_interact
def search_tracks():
    # To verify some data was searched for
    somesearch = False
    Track.query
    # A join to sort the things
    tracks = db.session.query(Track, func.count(Track.plays)).outerjoin(TrackLog).group_by(Track).order_by(desc(func.count(Track.plays)))
    # Do as fuzzy as possible of a search
    artist = request.args.get('artist', '').strip()
    if len(artist) > 0:
        somesearch = True
        tracks = tracks.filter(func.lower(Track.artist) == func.lower(artist))

    title = request.args.get('title', '').strip()
    if len(title) > 0:
        somesearch = True
        tracks = tracks.filter(func.lower(Track.title) == func.lower(title))

    album = request.args.get('album', '').strip()
    if len(album) > 0:
        somesearch = True
        tracks = tracks.filter(func.lower(Track.album) == func.lower(album))

    label = request.args.get('label', '').strip()
    if len(label) > 0:
        somesearch = True
        tracks = tracks.filter(func.lower(Track.label) == func.lower(label))

    # This means there was a bad search, stop searching
    if somesearch is False:
        app.logger.info("An empty search was submitted to the API")
        return jsonify(success=False, error="No search entires")

    # Check if results

    tracks = tracks.limit(8).all()
    if len(tracks) == 0:
        tracks = db.session.query(Track, func.count(Track.plays)).outerjoin(TrackLog).group_by(Track).order_by(desc(func.count(Track.plays)))
        # if there are too few results, append some similar results
        artist = request.args.get('artist', '').strip()
        if len(artist) > 0:
            somesearch = True
            tracks = tracks.filter(Track.artist.ilike(''.join(['%', artist, '%'])))

        title = request.args.get('title', '').strip()
        if len(title) > 0:
            somesearch = True
            tracks = tracks.filter(Track.title.ilike(''.join(['%', title, '%'])))

        album = request.args.get('album', '').strip()
        if len(album) > 0:
            somesearch = True
            tracks = tracks.filter(Track.album.ilike(''.join(['%', album, '%'])))

        label = request.args.get('label', '').strip()
        if len(label) > 0:
            somesearch = True
            tracks = tracks.filter(Track.label.ilike(''.join(['%', label, '%'])))

        tracks = tracks.limit(8).all()
        if len(tracks) == 0:
            return jsonify(results=[])

    return jsonify(results=[i[0].serialize() for i in tracks],
                   success=True)
