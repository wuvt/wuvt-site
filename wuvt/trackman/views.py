# WARNING:
# Breaking this will cause WUVT to go off-air because Winamp.
# If you're not using Winamp, breaking this will make people mad.

# NOTE: the .php filenames are kept for legacy reasons

from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf
import datetime
import json
import redis

from wuvt import app
from wuvt import db
from wuvt import lib
from wuvt import sse
from wuvt.trackman.models import DJ, Track


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


@app.route('/trackman/automation/submit', methods=['POST'])
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
    track = Track(dj.id, title, artist, album, label,
            listeners=lib.stream_listeners(app.config['ICECAST_STATS']))
    db.session.add(track)
    db.session.commit()

    # update last.fm (yay!)
    if len(app.config['LASTFM_APIKEY']) > 0:
        import pylast
        import hashlib
        import time

        h = hashlib.md5()
        h.update(app.config['LASTFM_PASSWORD'])
        password_hash = h.hexdigest()

        try:
            network = pylast.LastFMNetwork(
                    api_key=app.config['LASTFM_APIKEY'],
                    api_secret=app.config['LASTFM_SECRET'],
                    username=app.config['LASTFM_USERNAME'],
                    password_hash=password_hash)
            network.scrobble(artist=track.artist, title=track.title,
                    timestamp=int(time.mktime(track.datetime.timetuple())),
                    album=track.album)
        except Exception as e:
            print(e)

    # send server-sent event
    sse.send(json.dumps({'event': "track_change", 'track':
        track.serialize()}))

    return Response("Logged\n", mimetype="text/plain")
