# NOTE: the .php filenames are kept so old URLs keep working

from flask import abort, jsonify, redirect, render_template, request, \
    Response, url_for
import datetime
import dateutil
import re

from wuvt import app
from wuvt import csrf
from wuvt import db
from wuvt import redis_conn
from wuvt.trackman.lib import log_track, list_archives, generate_cuesheet, \
    generate_playlist_cuesheet
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog


def trackinfo():
    track = TrackLog.query.order_by(db.desc(TrackLog.played)).first()
    if not track:
        return {'artist': "", 'title': "", 'album': "", 'label': "", 'dj': "",
                'dj_id': 0, 'description': app.config['STATION_NAME'],
                'contact': app.config['STATION_URL']}

    data = track.track.serialize()
    data['listeners'] = track.listeners

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
    naughty_word_re = re.compile(
        r'shit|piss|fuck|cunt|cocksucker|tits|twat|asshole',
        re.IGNORECASE)

    track = trackinfo()
    for k, v in track.items():
        if type(v) == str or type(v) == unicode:
            track[k] = naughty_word_re.sub(u'****', v)

    if request.wants_json():
        return jsonify(track)

    output = u"{artist} - {title} [DJ: {dj}]".format(**track)
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
    try:
        start = datetime.datetime.strptime(request.args['start'], "%Y-%m-%dT%H:%M:%S.%fZ")
        end = datetime.datetime.strptime(request.args['end'], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        abort(400)

    sets = DJSet.query.filter(db.and_(DJSet.dtstart >= start,
                                      DJSet.dtstart <= end)).\
        order_by(db.desc(DJSet.dtstart)).limit(300).all()

    if request.wants_json():
        return jsonify({'sets': [s.serialize() for s in sets]})

    return Response("{start} {end}".format(start=start, end=end))


@app.route('/playlists/date/<int:year>/<int:month>/<int:day>')
def playlists_date_sets(year, month, day):
    dtstart = datetime.datetime(year, month, day, 0, 0, 0)
    sets = DJSet.query.filter(DJSet.dtstart >= dtstart).all()

    if request.wants_json():
        return jsonify({
            'dtstart': dtstart,
            'sets': [s.serialize() for s in sets],
        })

    return render_template('playlists_date_sets.html', date=dtstart, sets=sets)
# }}}


# Playlist Archive (by DJ) {{{
@app.route('/playlists/dj')
def playlists_dj():
    djs = DJ.query.order_by(DJ.airname).filter(DJ.visible == True)

    if request.wants_json():
        return jsonify({'djs': [dj.serialize() for dj in djs]})

    return render_template('playlists_dj_list.html', djs=djs)


@app.route('/playlists/dj/all')
def playlists_dj_all():
    djs = DJ.query.order_by(DJ.airname).all()

    if request.wants_json():
        return jsonify({'djs': [dj.serialize() for dj in djs]})

    return render_template('playlists_dj_list_all.html', djs=djs)


@app.route('/playlists/dj/<int:dj_id>')
def playlists_dj_sets(dj_id):
    dj = DJ.query.get(dj_id)
    if not dj:
        abort(404)
    sets = DJSet.query.filter(DJSet.dj_id == dj_id).all()

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'sets': [s.serialize() for s in sets],
        })

    return render_template('playlists_dj_sets.html', dj=dj, sets=sets)
# }}}


# Charts {{{
def charts_period(period):
    if period is not None:
        end = datetime.datetime.utcnow()

        if period == 'weekly':
            start = end - datetime.timedelta(weeks=1)
        elif period == 'monthly':
            start = end - dateutil.relativedelta.relativedelta(months=1)
        elif period == 'yearly':
            start = end - dateutil.relativedelta.relativedelta(years=1)
        else:
            abort(404)
    else:
        if 'start' in request.args:
            try:
                start = datetime.datetime.strptime(request.args['start'],
                                                   "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                abort(400)
        else:
            first_track = TrackLog.query.order_by(TrackLog.played).first()
            start = first_track.played

        if 'end' in request.args:
            try:
                end = datetime.datetime.strptime(request.args['end'],
                                                 "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                abort(400)
        else:
            end = datetime.datetime.utcnow()

    return start, end


@app.route('/playlists/charts')
def charts_index():
    periodic_charts = [
        ('charts_albums', "Top albums"),
        ('charts_artists', "Top artists"),
        ('charts_tracks', "Top tracks"),
    ]
    return render_template('charts.html', periodic_charts=periodic_charts)


@app.route('/playlists/charts/albums')
@app.route('/playlists/charts/albums/<string:period>')
def charts_albums(period=None):
    start, end = charts_period(period)
    results = Track.query.\
        with_entities(Track.artist, Track.album, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).\
        group_by(Track.artist, Track.album).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({'results': results})

    return render_template('chart_albums.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/albums/dj/<int:dj_id>')
def charts_albums_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = Track.query.\
        with_entities(Track.artist, Track.album, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(TrackLog.dj_id == dj.id).\
        group_by(Track.artist, Track.album).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_albums_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/artists')
@app.route('/playlists/charts/artists/<string:period>')
def charts_artists(period=None):
    start, end = charts_period(period)
    results = Track.query.\
        with_entities(Track.artist, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).\
        group_by(Track.artist).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({'results': results})

    return render_template('chart_artists.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/artists/dj/<int:dj_id>')
def charts_artists_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = Track.query.\
        with_entities(Track.artist, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(TrackLog.dj_id == dj.id).\
        group_by(Track.artist).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_artists_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/tracks')
@app.route('/playlists/charts/tracks/<string:period>')
def charts_tracks(period=None):
    start, end = charts_period(period)
    results = Track.query.with_entities(Track, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).\
        group_by(TrackLog.track_id).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/tracks/dj/<int:dj_id>')
def charts_tracks_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = Track.query.\
        with_entities(Track, db.func.count(TrackLog.id)).\
        join(TrackLog).filter(TrackLog.dj_id == dj.id).\
        group_by(TrackLog.track_id).\
        order_by(db.func.count(TrackLog.id).desc()).limit(250)

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/dj/spins')
def charts_dj_spins():
    results = TrackLog.query.\
        with_entities(TrackLog.dj_id, DJ, db.func.count(TrackLog.id)).\
        join(DJ).filter(DJ.visible == True).group_by(TrackLog.dj_id).\
        order_by(db.func.count(TrackLog.id).desc()).all()

    if request.wants_json():
        return jsonify({
            'results': [(x[1].serialize(), x[2]) for x in results],
        })

    return render_template('chart_dj_spins.html', results=results)
# }}}


@app.route('/playlists/set/<int:set_id>')
def playlist(set_id):
    djset = DJSet.query.get_or_404(set_id)
    tracks = TrackLog.query.filter(TrackLog.djset_id == djset.id).order_by(
        TrackLog.played).all()
    archives = list_archives(djset)

    if request.wants_json():
        data = djset.serialize()
        data.update({
            'archives': [a[0] for a in archives],
            'tracks': [t.full_serialize() for t in tracks],
        })
        return jsonify(data)

    return render_template('playlist.html', archives=archives, djset=djset,
                           tracklogs=tracks)


@app.route('/playlists/cue/<string:filename>.cue')
def playlist_cuesheet_ts(filename):
    match_re = re.compile(r'^(\d{10}0001)(.*)$')
    m = match_re.match(filename)
    if not m:
        abort(400)

    try:
        start = datetime.datetime.strptime(m.group(1), "%Y%m%d%H0001")
    except:
        abort(400)

    # assume time in URL is local time, so convert to UTC for DB lookup
    start = start.replace(tzinfo=dateutil.tz.tzlocal()).astimezone(
        dateutil.tz.tzutc()).replace(tzinfo=None)
    end = start + datetime.timedelta(hours=1)

    prev = db.session.query(TrackLog.id).filter(TrackLog.played <= start).\
        order_by(db.desc(TrackLog.played)).limit(1)
    tracks = TrackLog.query.filter(db.and_(
        TrackLog.id >= prev.as_scalar(),
        TrackLog.played <= end)).order_by(TrackLog.played).all()

    return Response(generate_cuesheet(filename, start, tracks),
                    mimetype="audio/x-cue")


@app.route('/playlists/cue/set/<int:set_id><string:ext>.cue')
def playlist_cuesheet(set_id, ext):
    djset = DJSet.query.get_or_404(set_id)
    if djset.dtend is None:
        abort(404)

    return Response(generate_playlist_cuesheet(djset, ext),
                    mimetype="audio/x-cue")


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

    if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr", "ua"):
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

    log_track(track.id, None)

    return Response("Logged\n", mimetype="text/plain")
