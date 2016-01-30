# NOTE: the .php filenames are kept so old URLs keep working

from flask import abort, jsonify, render_template, request, Response
import datetime
import dateutil
import re

from wuvt import app
from wuvt import csrf
from wuvt import db
from wuvt import redis_conn
from wuvt.trackman.lib import log_track, list_archives, generate_cuesheet, \
    generate_playlist_cuesheet, get_chart_range, get_chart
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog


def trackinfo():
    track = TrackLog.query.order_by(db.desc(TrackLog.id)).first()
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


@app.route('/last3hours')
def last3hours():
    start = datetime.datetime.utcnow() - datetime.timedelta(hours=3)
    tracks = TrackLog.query.filter(TrackLog.played >= start).order_by(
            db.desc(TrackLog.id)).all()

    if request.wants_json():
        return jsonify({
            'tracks': [t.full_serialize() for t in tracks],
        })

    return render_template('last3hours.html', tracklogs=tracks)


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
    sets = DJSet.query.filter(DJSet.dj_id == dj_id).order_by(
        DJSet.dtstart).all()

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'sets': [s.serialize() for s in sets],
        })

    return render_template('playlists_dj_sets.html', dj=dj, sets=sets)
# }}}


# Charts {{{
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
    try:
        start, end = get_chart_range(period, request)
    except ValueError:
        abort(400)

    results = get_chart(
        'albums_{0}_{1}'.format(start, end),
        Track.query.with_entities(
            Track.artist, Track.album, db.func.count(TrackLog.id)).
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).
        group_by(Track.artist, Track.album).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'results': [(x[0], x[1], x[2]) for x in results],
        })

    return render_template('chart_albums.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/albums/dj/<int:dj_id>')
def charts_albums_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = get_chart(
        'albums_dj_{}'.format(dj_id),
        Track.query.with_entities(
            Track.artist, Track.album, db.func.count(TrackLog.id)).
        join(TrackLog).filter(TrackLog.dj_id == dj.id).
        group_by(Track.artist, Track.album).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0], x[1], x[2]) for x in results],
        })

    return render_template('chart_albums_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/artists')
@app.route('/playlists/charts/artists/<string:period>')
def charts_artists(period=None):
    try:
        start, end = get_chart_range(period, request)
    except ValueError:
        abort(400)

    results = get_chart(
        'artists_{0}_{1}'.format(start, end),
        Track.query.with_entities(Track.artist, db.func.count(TrackLog.id)).
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).
        group_by(Track.artist).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'results': [(x[0], x[1]) for x in results],
        })

    return render_template('chart_artists.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/artists/dj/<int:dj_id>')
def charts_artists_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = get_chart(
        'artists_dj_{}'.format(dj_id),
        Track.query.with_entities(Track.artist, db.func.count(TrackLog.id)).
        join(TrackLog).filter(TrackLog.dj_id == dj.id).
        group_by(Track.artist).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0], x[1]) for x in results],
        })

    return render_template('chart_artists_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/tracks')
@app.route('/playlists/charts/tracks/<string:period>')
def charts_tracks(period=None):
    try:
        start, end = get_chart_range(period, request)
    except ValueError:
        abort(400)

    results = get_chart(
        'tracks_{start}_{end}'.format(start=start, end=end),
        Track.query.with_entities(Track, db.func.count(TrackLog.id)).
        join(TrackLog).filter(db.and_(
            TrackLog.dj_id > 1,
            TrackLog.played >= start,
            TrackLog.played <= end)).
        group_by(TrackLog.track_id).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks.html', start=start, end=end,
                           results=results)


@app.route('/playlists/charts/tracks/dj/<int:dj_id>')
def charts_tracks_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = get_chart(
        'tracks_dj_{}'.format(dj_id),
        Track.query.with_entities(Track, db.func.count(TrackLog.id)).
        join(TrackLog).filter(TrackLog.dj_id == dj.id).
        group_by(TrackLog.track_id).
        order_by(db.func.count(TrackLog.id).desc()))

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks_dj.html', dj=dj, results=results)


@app.route('/playlists/charts/dj/spins')
def charts_dj_spins():
    results = get_chart(
        'dj_spins',
        TrackLog.query.with_entities(
            TrackLog.dj_id, DJ, db.func.count(TrackLog.id)).
        join(DJ).filter(DJ.visible == True).group_by(TrackLog.dj_id).
        order_by(db.func.count(TrackLog.id).desc()))

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
