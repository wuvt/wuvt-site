# WARNING:
# Breaking this will cause WUVT to go off-air because Winamp.
# If you're not using Winamp, breaking this will make people mad.

# NOTE: the .php filenames are kept for legacy reasons

from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf_exempt
import datetime
import json
import redis

from wuvt import app
from wuvt import db
from wuvt import lib
from wuvt.trackman.lib import log_track
from wuvt.trackman.models import DJ, DJSet, Track


def trackinfo():
    track = Track.query.order_by(db.desc(Track.id)).first()
    if not track:
        return None

    data = track.serialize()
    data['description'] = app.config['STATION_NAME']
    data['contact'] = app.config['STATION_URL']
    return data


@app.context_processor
def inject_nowplaying():
    track = trackinfo()
    if not track:
        return {
            'current_track': u"Not Available",
            'current_dj': u"Not Available"
        }

    return {
        'current_track': u"{artist} - {title}".format(**track),
        'current_dj': track['dj'],
    }


@app.route('/last15')
def last15():
    tracks = Track.query.order_by(db.desc(Track.id)).limit(15).all()
    
    if request.wants_json():
        return jsonify({
            'tracks': [t.serialize() for t in tracks],
        })

    return render_template('last15.html', tracks=tracks)


@app.route('/playlists/latest_track')
@app.route('/playlists/latest_track.php')
def latest_track():
    if request.wants_json():
        return jsonify(trackinfo())

    return Response(u"{artist} - {title}".format(**trackinfo()),
            mimetype="text/plain")


@app.route('/playlists/latest_track_stream')
@app.route('/playlists/latest_track_stream.php')
def latest_track_stream():
    return Response(u"""\
title={title}
artist={artist}
album={album}
description={description}
contact={contact}
""".format(**trackinfo()), mimetype="text/plain")


# Playlist Archive (by date) {{{
@app.route('/playlists/date')
def playlists_date():
    return render_template('playlists_date_list.html')


@app.route('/playlists/date/<int:year>/<int:month>/<int:day>')
def playlists_date_sets(year, month, day):
    dtstart = datetime.datetime(year, month, day, 0, 0, 0)
    dtstart = dtstart - datetime.timedelta(seconds=30)
    dtend = datetime.datetime(year, month, day, 23, 59, 59)
    sets = DJSet.query.filter(DJSet.dtstart >= dtstart).\
            filter(DJSet.dtend <= dtend).all()
    return render_template('playlists_date_sets.html', date=dtend, sets=sets)
# }}}


# Playlist Archive (by DJ) {{{
@app.route('/playlists/dj')
def playlists_dj():
    djs = DJ.query.order_by(DJ.airname).filter(DJ.visible == True)
    return render_template('playlists_dj_list.html', djs=djs)


@app.route('/playlists/dj/<int:dj_id>')
def playlists_dj_sets(dj_id):
    dj = DJ.query.get(dj_id)
    if not dj:
        abort(404)
    sets = DJSet.query.filter(DJSet.dj_id == dj_id).all()
    return render_template('playlists_dj_sets.html', dj=dj, sets=sets)
# }}}


@app.route('/playlists/set/<int:set_id>')
def playlist(set_id):
    djset = DJSet.query.get(set_id)
    if not djset:
        abort(404)
    tracks = Track.query.filter(Track.djset_id == djset.id).all()
    return render_template('playlist.html', djset=djset, tracks=tracks)


@app.route('/trackman/automation/submit', methods=['POST'])
@csrf_exempt
def submit_automation_track():
    if 'password' not in request.form or \
        request.form['password'] != app.config['AUTOMATION_PASSWORD']:
        abort(403)

    red = redis.StrictRedis()
    automation = red.get('automation_enabled') == "true"
    if not automation:
        return Response("Automation is off\n", mimetype="text/plain")

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

    if 'label' in request.form and len(request.form['label']) > 0:
        label = request.form['label'].strip()
    else:
        label = "Not Available"

    if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr",
            "ua"):
        # ignore PSAs and other traffic
        return Response("Will not log traffic\n", mimetype="text/plain")

    dj = DJ.query.filter_by(name="Automation").first()
    log_track(dj.id, None, title, artist, album, label)

    return Response("Logged\n", mimetype="text/plain")
