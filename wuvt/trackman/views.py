# NOTE: the .php filenames are kept so old URLs keep working

from flask import abort, current_app, jsonify, render_template, redirect, \
        request, url_for, Response
import datetime
import dateutil
import re
from werkzeug.contrib.atom import AtomFeed

from .. import cache, db
from ..view_utils import sse_response
from . import bp, charts
from .lib import get_current_tracklog, serialize_trackinfo
from .models import DJ, DJSet, Track, TrackLog
from .view_utils import make_external, list_archives, generate_cuesheet, \
        generate_playlist_cuesheet


def trackinfo():
    data = cache.get('trackman_now_playing')
    if data is None:
        data = serialize_trackinfo(get_current_tracklog())
        cache.set('trackman_now_playing', data)

    return data


#############################################################################
# Playlist Information
#############################################################################


@bp.route('/last15')
def last15():
    tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()

    if request.wants_json():
        return jsonify({
            'tracks': [t.full_serialize() for t in tracks],
        })

    return render_template('last15.html', tracklogs=tracks,
                           feedlink=url_for('.last15_feed'))


@bp.route('/last15.atom')
def last15_feed():
    tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()
    feed = AtomFeed(
        u"{0}: Last 15 Tracks".format(current_app.config['TRACKMAN_NAME']),
        feed_url=request.url,
        url=make_external(url_for('.last15')))

    for tracklog in tracks:
        feed.add(
            u"{artist}: '{title}'".format(
                artist=tracklog.track.artist,
                title=tracklog.track.title),
            u"'{title}' by {artist} on {album} spun by {dj}".format(
                album=tracklog.track.album,
                artist=tracklog.track.artist,
                title=tracklog.track.title,
                dj=tracklog.dj.airname),
            url=make_external(url_for('.playlist',
                                      set_id=tracklog.djset_id,
                                      _anchor="t{}".format(tracklog.id))),
            author=tracklog.dj.airname,
            updated=tracklog.played,
            published=tracklog.played)

    return feed.get_response()


@bp.route('/playlists/latest_track')
@bp.route('/playlists/latest_track.php')
def latest_track():
    if request.wants_json():
        return jsonify(trackinfo())

    return Response(u"{artist} - {title}".format(**trackinfo()),
                    mimetype="text/plain")


@bp.route('/playlists/latest_track_clean')
@bp.route('/playlists/latest_track_clean.php')
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


@bp.route('/playlists/latest_track_slack')
def latest_track_slack():
    track = trackinfo()

    if track['dj_id'] > 0:
        dj_link = '<{url}|{dj}>'.format(
            dj=track['dj'],
            url=make_external(url_for('.playlists_dj_sets',
                                      dj_id=track['dj_id'])))
    else:
        dj_link = track['dj']

    return jsonify({
        "response_type": "in_channel",
        "text": "*{artist} - {title}*\nDJ: {dj_link}".format(
            dj_link=dj_link, **track),
    })


@bp.route('/playlists/latest_track_stream')
@bp.route('/playlists/latest_track_stream.php')
def latest_track_stream():
    return Response(u"""\
title={title}
artist={artist}
album={album}
description={description}
contact={contact}
""".format(**trackinfo()), mimetype="text/plain")


@bp.route('/playlists/live')
@bp.route('/live')
def live():
    return sse_response('trackman_live')


# Playlist Archive (by date) {{{
@bp.route('/playlists/date')
def playlists_date():
    return render_template('playlists_date_list.html')


@bp.route('/playlists/date/data')
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


@bp.route('/playlists/date/<int:year>/<int:month>/<int:day>')
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
@bp.route('/playlists/dj')
def playlists_dj():
    djs = DJ.query.order_by(DJ.airname).filter(DJ.visible == True)

    if request.wants_json():
        return jsonify({'djs': [dj.serialize() for dj in djs]})

    return render_template('playlists_dj_list.html', djs=djs)


@bp.route('/playlists/dj/all')
def playlists_dj_all():
    djs = DJ.query.order_by(DJ.airname).all()

    if request.wants_json():
        return jsonify({'djs': [dj.serialize() for dj in djs]})

    return render_template('playlists_dj_list_all.html', djs=djs)


@bp.route('/playlists/dj/<int:dj_id>')
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
@bp.route('/playlists/charts')
def charts_index():
    periodic_charts = [
        ('trackman.charts_albums', "Top albums"),
        ('trackman.charts_artists', "Top artists"),
        ('trackman.charts_tracks', "Top tracks"),
    ]
    return render_template('charts.html', periodic_charts=periodic_charts)


@bp.route('/playlists/charts/albums')
@bp.route('/playlists/charts/albums/<string:period>')
@bp.route('/playlists/charts/albums/<string:period>/<int:year>')
@bp.route('/playlists/charts/albums/<string:period>/<int:year>/<int:month>')
def charts_albums(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_albums_dj', dj_id=year))

    try:
        start, end = charts.get_range(period, year, month)
    except ValueError:
        abort(404)

    results = charts.get(
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


@bp.route('/playlists/charts/dj/<int:dj_id>/albums')
def charts_albums_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = charts.get(
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


@bp.route('/playlists/charts/artists')
@bp.route('/playlists/charts/artists/<string:period>')
@bp.route('/playlists/charts/artists/<string:period>/<int:year>')
@bp.route('/playlists/charts/artists/<string:period>/<int:year>/<int:month>')
def charts_artists(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_artists_dj', dj_id=year))

    try:
        start, end = charts.get_range(period, year, month)
    except ValueError:
        abort(404)

    results = charts.get(
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


@bp.route('/playlists/charts/dj/<int:dj_id>/artists')
def charts_artists_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)
    results = charts.get(
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


@bp.route('/playlists/charts/tracks')
@bp.route('/playlists/charts/tracks/<string:period>')
@bp.route('/playlists/charts/tracks/<string:period>/<int:year>')
@bp.route('/playlists/charts/tracks/<string:period>/<int:year>/<int:month>')
def charts_tracks(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_tracks_dj', dj_id=year))

    try:
        start, end = charts.get_range(period, year, month)
    except ValueError:
        abort(404)

    subquery = TrackLog.query.\
        with_entities(TrackLog.track_id,
                      db.func.count(TrackLog.id).label('count')).\
        filter(TrackLog.dj_id > 1,
               TrackLog.played >= start,
               TrackLog.played <= end).\
        group_by(TrackLog.track_id).subquery()
    results = charts.get(
        'tracks_{start}_{end}'.format(start=start, end=end),
        Track.query.with_entities(Track, subquery.c.count).
        join(subquery).order_by(db.desc(subquery.c.count)))

    if request.wants_json():
        return jsonify({
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks.html', start=start, end=end,
                           results=results)


@bp.route('/playlists/charts/dj/<int:dj_id>/tracks')
def charts_tracks_dj(dj_id):
    dj = DJ.query.get_or_404(dj_id)

    subquery = TrackLog.query.\
        with_entities(TrackLog.track_id,
                      db.func.count(TrackLog.id).label('count')).\
        filter(TrackLog.dj_id == dj.id).\
        group_by(TrackLog.track_id).subquery()
    results = charts.get(
        'tracks_dj_{}'.format(dj_id),
        Track.query.with_entities(Track, subquery.c.count).
        join(subquery).order_by(db.desc(subquery.c.count)))

    if request.wants_json():
        return jsonify({
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_tracks_dj.html', dj=dj, results=results)


@bp.route('/playlists/charts/dj/spins')
def charts_dj_spins():
    subquery = TrackLog.query.\
        with_entities(TrackLog.dj_id,
                      db.func.count(TrackLog.id).label('count')).\
        group_by(TrackLog.dj_id).subquery()

    results = charts.get(
        'dj_spins',
        DJ.query.with_entities(DJ, subquery.c.count).
        join(subquery).filter(DJ.visible == True).
        order_by(db.desc(subquery.c.count)))

    if request.wants_json():
        return jsonify({
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_dj_spins.html', results=results)


@bp.route('/playlists/charts/dj/vinyl_spins')
def charts_dj_vinyl_spins():
    subquery = TrackLog.query.\
        with_entities(TrackLog.dj_id,
                      db.func.count(TrackLog.id).label('count')).\
        filter(TrackLog.vinyl == True).\
        group_by(TrackLog.dj_id).subquery()

    results = charts.get(
        'dj_vinyl_spins',
        DJ.query.with_entities(DJ, subquery.c.count).
        join(subquery).filter(DJ.visible == True).
        order_by(db.desc(subquery.c.count)))

    if request.wants_json():
        return jsonify({
            'results': [(x[0].serialize(), x[1]) for x in results],
        })

    return render_template('chart_dj_vinyl_spins.html', results=results)
# }}}


@bp.route('/playlists/set/<int:set_id>')
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


@bp.route('/playlists/cue/<string:filename>.cue')
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
        dateutil.tz.tzutc())
    end = start + datetime.timedelta(hours=1)

    prev = db.session.query(TrackLog.id).filter(TrackLog.played <= start).\
        order_by(db.desc(TrackLog.played)).limit(1)
    tracks = TrackLog.query.filter(db.and_(
        TrackLog.id >= prev.as_scalar(),
        TrackLog.played <= end)).order_by(TrackLog.played).all()

    return Response(generate_cuesheet(filename, start, tracks),
                    mimetype="audio/x-cue")


@bp.route('/playlists/cue/set/<int:set_id><string:ext>.cue')
def playlist_cuesheet(set_id, ext):
    djset = DJSet.query.get_or_404(set_id)
    if djset.dtend is None:
        abort(404)

    return Response(generate_playlist_cuesheet(djset, ext),
                    mimetype="audio/x-cue")


@bp.route('/playlists/track/<int:track_id>')
def playlists_track(track_id):
    track = Track.query.get_or_404(track_id)
    tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
        order_by(TrackLog.played).all()

    if request.wants_json():
        data = track.serialize()
        data['plays'] = [tl.serialize() for tl in tracklogs]
        return jsonify(data)

    return render_template('playlists_track.html', track=track,
                           tracklogs=tracklogs)
