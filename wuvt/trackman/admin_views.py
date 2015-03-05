from flask import abort, flash, jsonify, render_template, \
        render_template_string, redirect, request, url_for, Response, session
from sqlalchemy import func, desc
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import email.utils
import datetime
import json
import redis
import smtplib
import netaddr
import dateutil.parser

from wuvt import app
from wuvt import db
from wuvt import csrf
from wuvt.trackman import bp
from wuvt.trackman.lib import log_track
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog, AirLog, Rotation
from wuvt.trackman.view_utils import localonly


#############################################################################
### Login
#############################################################################

@bp.route('/', methods=['GET', 'POST'])
@localonly
def login():
#    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
#        abort(403)

    red = redis.StrictRedis()

    if 'dj' in request.form:
        red.set("automation_enabled", "false")

        dj = DJ.query.get(request.form['dj'])
        djset = DJSet(dj.id)
        db.session.add(djset)
        db.session.commit()

        return redirect(url_for('trackman.log', setid=djset.id))

    automation = red.get('automation_enabled') == "true"

    djs = DJ.query.filter(DJ.visible == True).order_by(DJ.airname).all()
    return render_template('trackman/login.html',
            trackman_name=app.config['TRACKMAN_NAME'],
            automation=automation, djs=djs)

#############################################################################
### Automation Control
#############################################################################

@bp.route('/automation/start', methods=['POST'])
def start_automation():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    red = redis.StrictRedis()
    red.set('automation_enabled', "true")

    return redirect(url_for('trackman.login'))

#############################################################################
### DJ Control
#############################################################################

@bp.route('/log/<int:setid>', methods=['GET', 'POST'])
@localonly
def log(setid):

    djset = DJSet.query.get_or_404(setid)
    errors = {}

    if 'artist' in request.form:
        session['email_playlist'] = 'email_playlist' in request.form

        artist = request.form['artist'].strip()
        if len(artist) <= 0:
            errors['artist'] = "You must enter an artist."

        title = request.form['title'].strip()
        if len(title) <= 0:
            errors['title'] = "You must enter a song title."

        album = request.form['album'].strip()
        if len(album) <= 0:
            errors['album'] = "You must enter an album."

        label = request.form['label'].strip()
        if len(label) <= 0:
            errors['label'] = "You must enter a label."

        if len(errors.items()) <= 0:
            log_track(djset.dj_id, djset.id, title, artist, album, label,
                    'request' in request.form, 'vinyl' in request.form)

    if 'email_playlist' in session:
        email_playlist = session['email_playlist']
    else:
        email_playlist = False

    tracks = djset.tracks.order_by(TrackLog.played).all()

    # TODO rotation listing
    rotations = {}
    for i in Rotation.query.order_by(Rotation.id).all():
        rotations[i.id] = i.rotation
    return render_template('trackman/log.html',
            trackman_name=app.config['TRACKMAN_NAME'], djset=djset,
            rotations=rotations, email_playlist=email_playlist)


@bp.route('/log/<int:setid>/<int:trackid>',
        methods=['DELETE', 'GET', 'POST'])
def edit(setid, trackid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    track = Track.query.get_or_404(trackid)
    if track.djset_id != djset.id:
        abort(404)

    errors = {}

    if request.method == 'DELETE':
        db.session.delete(track)
        db.session.commit()
        return Response("deleted")
    elif request.method == 'POST':
        artist = request.form['artist'].strip()
        if len(artist) <= 0:
            errors['artist'] = "You must enter an artist."

        title = request.form['title'].strip()
        if len(title) <= 0:
            errors['title'] = "You must enter a song title."

        album = request.form['album'].strip()
        if len(album) <= 0:
            errors['album'] = "You must enter an album."

        label = request.form['label'].strip()
        if len(label) <= 0:
            errors['label'] = "You must enter a label."

        if len(errors.items()) <= 0:
            track.artist = artist
            track.title = title
            track.album = album
            track.label = label
            track.request = 'request' in request.form
            track.vinyl = 'vinyl' in request.form
            db.session.commit()

            return redirect(url_for('trackman.log', setid=djset.id))

    return render_template('trackman/edit.html',
            trackman_name=app.config['TRACKMAN_NAME'], djset=djset,
            track=track, errors=errors)


@bp.route('/log/<int:setid>/end', methods=['POST'])
def logout(setid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    djset.dtend = datetime.datetime.now()
    db.session.commit()

    # email playlist
    if 'email_playlist' in session and session['email_playlist']:
        msg = MIMEMultipart('alternative')
        msg['Date'] = email.utils.formatdate()
        msg['From'] = app.config['MAIL_FROM']
        msg['To'] = djset.dj.email
        msg['Message-Id'] = email.utils.make_msgid()
        msg['X-Mailer'] = "Trackman"
        msg['Subject'] = "[{name}] {djname} - Playlist from {dtend}".format(
            name=app.config['TRACKMAN_NAME'],
            djname=djset.dj.airname,
            dtend=datetime.datetime.strftime(djset.dtend, "%Y-%m-%d"))

        tracks = Track.query.filter(Track.djset_id == djset.id).all()

        msg.attach(MIMEText(
            render_template('email/playlist.txt',
                            djset=djset, tracks=tracks).encode('utf-8'),
            'text'))
        msg.attach(MIMEText(
            render_template('email/playlist.html',
                            djset=djset, tracks=tracks).encode('utf-8'),
            'html'))

        s = smtplib.SMTP(app.config['SMTP_SERVER'])
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()

    session['email_playlist'] = False

    return redirect(url_for('trackman.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

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
            trackman_name=app.config['TRACKMAN_NAME'], errors=errors)

#############################################################################
### Trackman API
#############################################################################

@bp.route('/api/djset/<int:djset_id>', methods=['GET'])
@localonly
def get_djset(djset_id):
    djset = DJSet.query.get(djset_id)
    if not djset:
        return jsonify(success=False, error="djset_id not found")

    if request.args.get('merged', False):
        logs = [i.full_serialize() for i in djset.tracks]
        logs.extend([i.serialize() for i in djset.airlog])
        logs = sorted(logs, key=lambda log: log.get('airtime', False) if log.get('airtime', False) else log.get('played', False), reverse=False)
        return jsonify(success=True, logs=logs)
    return jsonify(success=True, tracklog=[i.serialize() for i in djset.tracks], airlog=[i.serialize() for i in djset.airlog])


@bp.route('/api/airlog/edit/<int:airlog_id>', methods=['DELETE', 'POST'])
@localonly
@csrf.exempt
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
        tracklog.airtime = dateutil.parser.parse(airtime)
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
@localonly
@csrf.exempt
def add_airlog():
    djset_id = int(request.form['djset_id'])
    logtype = int(request.form['logtype'])
    logid = int(request.form['logid'])

    airlog = Airlog(djset_id, logtype, logid=logid)
    db.session.add(airlog)
    db.session.commit()

    return jsonify(success=True, airlog_id=airlog.id)


@bp.route('/api/tracklog/edit/<int:tracklog_id>', methods=['POST', 'DELETE'])
@localonly
@csrf.exempt
def edit_tracklog(tracklog_id):
    tracklog = TrackLog.query.get(tracklog_id)
    if not tracklog:
        return jsonify(success=False, error="tracklog_id not found")

    if request.method is 'DELETE':
        db.session.delete(tracklog)
        db.session.commit()
        return jsonify(success=True)

    # Update track
    track_id = request.form.get('track_id', None)
    if track_id is not None:
        track = Track.query.get(track_id)
        if not track:
            return jsonify(success=False, error="Track specified by track_id does not exist")
        tracklog.track_id = int(track_id)
    # Update played time
    played = request.form.get('played', None)
    if played is not None:
        tracklog.played = dateutil.parser.parse(played)
    # Update boolean information
    is_request = request.form.get('request', None)
    if is_request is not None:
        tracklog.request = bool(is_request)
    vinyl = request.form.get('vinyl', None)
    if vinyl is not None:
        tracklog.request = bool(vinyl)
    new = request.form.get('new', None)
    if new is not None:
        tracklog.request = bool(new)
    # Update rotation
    rotation_id = request.form.get('rotation_id', None)
    if rotation_id is not None:
        rotation = Rotation.query.get(rotation_id)
        if not rotation:
            return jsonify(success=False, error="Rotation specified by rotation_id does not exist")
        tracklog.rotation_id = rotation_id

    return jsonify(success=True)

@bp.route('/api/tracklog', methods=['POST'])
@localonly
@csrf.exempt
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

    tracklog = TrackLog(track_id, djset_id, request=is_request, vinyl=vinyl, new=new, rotation=rotation)
    db.session.add(tracklog)
    db.session.commit()

    return jsonify(success=True, tracklog_id=tracklog.id)

@bp.route('/api/track/edit/<int:track_id>', methods=['POST'])
@localonly
@csrf.exempt
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
        track.artist = artist
    album = request.form.get('album', None)
    if album is not None:
        track.album = album
    title = request.form.get('title', None)
    if title is not None:
        track.title = title
    label = request.form.get('label', None)
    if label is not None:
        track.label = label

    db.session.commit()
    return jsonify(success=True)


@bp.route('/api/track', methods=['POST'])
@localonly
@csrf.exempt
def add_track():
    # TODO: sanitation and verification
    title = request.form['title']
    album = request.form['album']
    artist = request.form['artist']
    label = request.form['label']

    track = Track(title, artist, album, label)
    db.session.add(track)
    db.session.commit()
    return jsonify(success=True, track_id=track.id)


@bp.route('/api/search', methods=['GET'])
@localonly
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
    if somesearch == False:
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
            return jsonify(results = [])

    return jsonify(results = [i[0].serialize() for i in tracks], success = True)



