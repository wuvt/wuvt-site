# NOTE: the .php filenames are kept so old URLs keep working

from flask import abort, current_app, jsonify, render_template, redirect, \
        request, url_for, Response
import datetime
import re
from werkzeug.contrib.atom import AtomFeed

from .. import db
from ..view_utils import sse_response
from . import bp
from .models import DJSet, Track, TrackLog
from .view_utils import call_api, make_external, list_archives
from .api.v1 import charts, playlists


def trackinfo():
    return call_api(playlists.LatestTrack, 'GET')


#############################################################################
# Playlist Information
#############################################################################


@bp.route('/last15')
def last15():
    if request.wants_json():
        tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()
        return jsonify({
            'tracks': [t.full_serialize() for t in tracks],
        })

    result = call_api(playlists.Last15Tracks, 'GET')
    return render_template('last15.html', tracklogs=result['tracks'],
                           feedlink=url_for('.last15_feed'))


@bp.route('/last15.atom')
def last15_feed():
    result = call_api(playlists.Last15Tracks, 'GET')
    tracks = result['tracks']
    feed = AtomFeed(
        u"{0}: Last 15 Tracks".format(current_app.config['TRACKMAN_NAME']),
        feed_url=request.url,
        url=make_external(url_for('.last15')))

    for tracklog in tracks:
        feed.add(
            u"{artist}: '{title}'".format(
                artist=tracklog['track']['artist'],
                title=tracklog['track']['title']),
            u"'{title}' by {artist} on {album} spun by {dj}".format(
                album=tracklog['track']['album'],
                artist=tracklog['track']['artist'],
                title=tracklog['track']['title'],
                dj=tracklog['dj']['airname']),
            url=make_external(url_for('.playlist',
                                      set_id=tracklog['djset_id'],
                                      _anchor="t{}".format(tracklog['id']))),
            author=tracklog['dj']['airname'],
            updated=tracklog['played'],
            published=tracklog['played'])

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
        dj_link = u'<{url}|{dj}>'.format(
            dj=track['dj'],
            url=make_external(url_for('.playlists_dj_sets',
                                      dj_id=track['dj_id'])))
    else:
        dj_link = track['dj']

    return jsonify({
        "response_type": u"in_channel",
        "text": u"*{artist} - {title}*\nDJ: {dj_link}".format(
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
    today = datetime.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0)
    return render_template('playlists_date_list.html', today=today)


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
    results, status_code = call_api(
        playlists.PlaylistByDay, 'GET', year, month, day)

    now = datetime.datetime.utcnow()

    next_date = results['start'] + datetime.timedelta(hours=24)
    next_url = url_for('.playlists_date_sets', year=next_date.year,
                       month=next_date.month, day=next_date.day)
    if next_date > now:
        next_url = None

    if results['start'] < now:
        prev_date = results['start'] - datetime.timedelta(hours=24)
        prev_url = url_for('.playlists_date_sets', year=prev_date.year,
                           month=prev_date.month, day=prev_date.day)
    else:
        prev_url = None

    results.update({
        'prev_url': prev_url,
        'next_url': next_url,
    })

    if request.wants_json():
        return jsonify(results), status_code

    return render_template(
        'playlists_date_sets.html',
        date=results['start'],
        sets=results['sets'],
        prev_url=results['prev_url'],
        next_url=results['next_url']), status_code


@bp.route('/playlists/date/jump', methods=['POST'])
def playlists_date_jump():
    jumpdate = datetime.datetime.strptime(request.form['date'], "%Y-%m-%d")
    return redirect(url_for('.playlists_date_sets', year=jumpdate.year,
                            month=jumpdate.month, day=jumpdate.day))
# }}}


# Playlist Archive (by DJ) {{{
@bp.route('/playlists/dj')
def playlists_dj():
    results = call_api(playlists.PlaylistDJs, 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_list.html', djs=results['djs'])


@bp.route('/playlists/dj/all')
def playlists_dj_all():
    results = call_api(playlists.PlaylistAllDJs, 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_list_all.html', djs=results['djs'])


@bp.route('/playlists/dj/<int:dj_id>')
def playlists_dj_sets(dj_id):
    results = call_api(playlists.PlaylistsByDJ, 'GET', dj_id)

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_sets.html',
                           dj=results['dj'], sets=results['sets'])
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

    results = call_api(charts.AlbumCharts, 'GET', period, year, month)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_albums.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/albums')
def charts_albums_dj(dj_id):
    results = call_api(charts.DJAlbumCharts, 'GET', dj_id)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_albums_dj.html',
                           dj=results['dj'],
                           results=results['results'])


@bp.route('/playlists/charts/artists')
@bp.route('/playlists/charts/artists/<string:period>')
@bp.route('/playlists/charts/artists/<string:period>/<int:year>')
@bp.route('/playlists/charts/artists/<string:period>/<int:year>/<int:month>')
def charts_artists(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_artists_dj', dj_id=year))

    results = call_api(charts.ArtistCharts, 'GET', period, year, month)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_artists.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/artists')
def charts_artists_dj(dj_id):
    results = call_api(charts.DJArtistCharts, 'GET', dj_id)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_artists_dj.html',
                           dj=results['dj'],
                           results=results['results'])


@bp.route('/playlists/charts/tracks')
@bp.route('/playlists/charts/tracks/<string:period>')
@bp.route('/playlists/charts/tracks/<string:period>/<int:year>')
@bp.route('/playlists/charts/tracks/<string:period>/<int:year>/<int:month>')
def charts_tracks(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_tracks_dj', dj_id=year))

    results = call_api(charts.TrackCharts, 'GET', period, year, month)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_tracks.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/tracks')
def charts_tracks_dj(dj_id):
    results = call_api(charts.DJTrackCharts, 'GET', dj_id)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_tracks_dj.html',
                           dj=results['dj'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/spins')
def charts_dj_spins():
    results = call_api(charts.DJSpinCharts, 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_dj_spins.html', results=results['results'])


@bp.route('/playlists/charts/dj/vinyl_spins')
def charts_dj_vinyl_spins():
    results = call_api(charts.DJVinylSpinCharts, 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_dj_vinyl_spins.html',
                           results=results['results'])
# }}}


@bp.route('/playlists/set/<int:set_id>')
def playlist(set_id):
    if request.wants_json():
        djset = DJSet.query.get_or_404(set_id)
        tracks = TrackLog.query.filter(TrackLog.djset_id == djset.id).order_by(
            TrackLog.played).all()
        archives = list_archives(djset)

        data = djset.serialize()
        data.update({
            'archives': [a[0] for a in archives],
            'tracks': [t.full_serialize() for t in tracks],
        })
        return jsonify(data)

    results = call_api(playlists.Playlist, 'GET', set_id)
    return render_template('playlist.html',
                           archives=results['archives'],
                           djset=results,
                           tracklogs=results['tracks'])


@bp.route('/playlists/track/<int:track_id>')
def playlists_track(track_id):
    if request.wants_json():
        track = Track.query.get_or_404(track_id)
        tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
            order_by(TrackLog.played).all()
        data = track.serialize()
        data['plays'] = [tl.serialize() for tl in tracklogs]
        return jsonify(data)

    results = call_api(playlists.PlaylistTrack, 'GET', track_id)
    return render_template('playlists_track.html',
                           track=results,
                           tracklogs=results['plays'])
