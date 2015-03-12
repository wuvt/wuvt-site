# WARNING:
# Breaking this will cause WUVT to go off-air because Winamp.
# If you're not using Winamp, breaking this will make people mad.

# NOTE: the .php filenames are kept for legacy reasons

from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
import datetime
import json
import re

from wuvt import app
from wuvt import csrf
from wuvt import db
from wuvt import redis_conn
from wuvt.trackman.lib import log_track, list_archives
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog


def trackinfo():
    track = TrackLog.query.order_by(db.desc(TrackLog.played)).first()
    if not track:
        return {'artist': "", 'title': "", 'album': "", 'label': "", 'dj': "",
                'description': app.config['STATION_NAME'], 'contact': app.config['STATION_URL']}

    data = track.track.serialize()

    if track.djset == None:
        dj = DJ.query.filter_by(name="Automation").first()
        data['dj'] = dj.airname
        data['dj_id'] = 0
    else:
        data['dj'] = track.djset.dj.airname
        if track.djset.dj.visible:
            data['dj_id'] = track.djset.dj_id
        else:
            data['dj_id'] = 0

    data['description'] = app.config['STATION_NAME']
    data['contact'] = app.config['STATION_URL']
    return data

#############################################################################
### Playlist Information
#############################################################################

@app.context_processor
def inject_nowplaying():
    track = trackinfo()
    if not track:
        return {
            'current_track': u"Not Available",
            'current_dj': u"Not Available",
            'current_dj_id': 0,
        }

    return {
        'current_track': u"{artist} - {title}".format(**track),
        'current_dj': track['dj'],
        'current_dj_id': track['dj_id']
    }


@app.route('/last15')
def last15():
    tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()

    if request.wants_json():
        return jsonify({
            'tracks': [t.full_serialize() for t in tracks],
        })

    return render_template('last15.html', tracklogs=tracks)


@app.route('/playlists/latest_track')
@app.route('/playlists/latest_track.php')
def latest_track():
    if request.wants_json():
        return jsonify(trackinfo())

    return Response(u"{artist} - {title}".format(**trackinfo()),
            mimetype="text/plain")


@app.route('/playlists/latest_track_clean')
@app.route('/playlists/latest_track_clean.php')
def latest_track_clean():
    if request.wants_json():
        return jsonify(trackinfo())

    naughty_word_re = re.compile(
        r'shit|piss|fuck|cunt|cocksucker|tits|twat|asshole',
        re.IGNORECASE)
    output = u"{artist} - {title} [DJ: {dj}]".format(**trackinfo())
    output = naughty_word_re.sub(u'****', output)

    return Response(output, mimetype="text/plain")


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


@app.route('/playlists/date/data')
def playlists_date_data():
    start = datetime.datetime.strptime(request.args['start'], "%Y-%m-%dT%H:%M:%S.%fZ")
    end = datetime.datetime.strptime(request.args['end'], "%Y-%m-%dT%H:%M:%S.%fZ")

    sets = DJSet.query.filter(db.and_(DJSet.dtstart >= start,
                                      DJSet.dtstart <= end)).\
            order_by(db.desc(DJSet.dtstart)).limit(300).all()

    if request.wants_json():
        return jsonify({'sets': [s.serialize() for s in sets]})

    return Response("{start} {end}".format(start=start, end=end))



@app.route('/playlists/date/<int:year>/<int:month>/<int:day>')
def playlists_date_sets(year, month, day):
    dtstart = datetime.datetime(year, month, day, 0, 0, 0)
    dtstart = dtstart - datetime.timedelta(seconds=30)
    sets = DJSet.query.filter(DJSet.dtstart >= dtstart).all()

    return render_template('playlists_date_sets.html', sets=sets)
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
    djset = DJSet.query.get_or_404(set_id)
    tracks = TrackLog.query.filter(TrackLog.djset_id == djset.id).order_by(TrackLog.played).all()
    archives = list_archives(djset)
    return render_template('playlist.html', archives=archives, djset=djset, tracklogs=tracks)


#############################################################################
### Automation
#############################################################################

@app.route('/trackman/automation/submit', methods=['POST'])
@csrf.exempt
def submit_automation_track():
    if 'password' not in request.form or \
        request.form['password'] != app.config['AUTOMATION_PASSWORD']:
        abort(403)

    automation = redis_conn.get('automation_enabled') == "true"
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

    if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr",
            "ua"):
        # ignore PSAs and other traffic
        return Response("Will not log traffic\n", mimetype="text/plain")

    if 'label' in request.form and len(request.form['label']) > 0:
        label = request.form['label'].strip()
        tracks = Track.query.filter(Track.title == title).filter(Track.artist == artist).filter(Track.album == album).filter(Track.label == label)
        if len(tracks.all()) == 0:
            track = Track(title, artist, album, label)
            db.session.add(track)
            db.session.commit()
        else:
            track = tracks.one()

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
                track = tracks.one()
            else:
                track = notauto.one()

    dj = DJ.query.filter_by(name="Automation").first()

    log_track(track.id, None)

    return Response("Logged\n", mimetype="text/plain")
