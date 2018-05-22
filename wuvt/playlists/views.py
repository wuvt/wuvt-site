# NOTE: the .php filenames are kept so old URLs keep working

from flask import current_app, jsonify, make_response, render_template, \
        redirect, request, url_for, Response
import datetime
import dateutil.parser
import re
import requests
from werkzeug.contrib.atom import AtomFeed

from . import bp
from .view_utils import call_api, make_external, \
        tracklog_serialize, tracklog_full_serialize


def trackinfo():
    return call_api("/playlists/latest_track", 'GET')


#############################################################################
# Playlist Information
#############################################################################


@bp.route('/last15')
def last15():
    result = call_api("/playlists/last15", 'GET')

    if request.wants_json():
        return jsonify({
            'tracks': [tracklog_full_serialize(t) for t in result['tracks']],
        })

    return render_template('last15.html', tracklogs=result['tracks'],
                           feedlink=url_for('.last15_feed'))


@bp.route('/last15.atom')
def last15_feed():
    result = call_api("/playlists/last15", 'GET')
    tracks = result['tracks']
    feed = AtomFeed(
        "{0}: Last 15 Tracks".format(current_app.config['STATION_SHORT_NAME']),
        feed_url=request.url,
        url=make_external(url_for('.last15')))

    for tracklog in tracks:
        feed.add(
            "{artist}: '{title}'".format(
                artist=tracklog['track']['artist'],
                title=tracklog['track']['title']),
            "'{title}' by {artist} on {album} spun by {dj}".format(
                album=tracklog['track']['album'],
                artist=tracklog['track']['artist'],
                title=tracklog['track']['title'],
                dj=tracklog['dj']['airname']),
            url=make_external(url_for('.playlist',
                                      set_id=tracklog['djset_id'],
                                      _anchor="t{}".format(tracklog['id']))),
            author=tracklog['dj']['airname'],
            updated=dateutil.parser.parse(tracklog['played']),
            published=dateutil.parser.parse(tracklog['played']))

    return feed.get_response()


@bp.route('/playlists/latest_track')
@bp.route('/playlists/latest_track.php')
def latest_track():
    if request.wants_json():
        return jsonify(trackinfo())

    return Response("{artist} - {title}".format(**trackinfo()),
                    mimetype="text/plain")


@bp.route('/playlists/latest_track_clean')
@bp.route('/playlists/latest_track_clean.php')
def latest_track_clean():
    naughty_word_re = re.compile(
        r'shit|piss|fuck|cunt|cocksucker|tits|twat|asshole',
        re.IGNORECASE)

    track = trackinfo()
    for k, v in list(track.items()):
        if type(v) == str or type(v) == str:
            track[k] = naughty_word_re.sub('****', v)

    if request.wants_json():
        return jsonify(track)

    output = "{artist} - {title} [DJ: {dj}]".format(**track)
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
    return Response("""\
title={title}
artist={artist}
album={album}
description={description}
contact={contact}
""".format(**trackinfo()), mimetype="text/plain")


@bp.route('/playlists/live')
@bp.route('/live')
def live():
    url = "{0}/live".format(current_app.config['TRACKMAN_URL'])
    return redirect(url, 303)


# Playlist Archive (by date) {{{
@bp.route('/playlists/date')
def playlists_date():
    today = datetime.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0)
    return render_template('playlists_date_list.html', today=today)


@bp.route('/js/playlists_by_date_init.js')
def playlists_by_date_init_js():
    resp = make_response(render_template('playlists_by_date_init.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/playlists/date/<int:year>/<int:month>/<int:day>')
def playlists_date_sets(year, month, day):
    r = requests.get('{0}/api/playlists/date/{1}/{2}/{3}'.format(
            current_app.config['TRACKMAN_URL'],
            year, month, day))
    status_code = r.status_code
    results = r.json()

    now = datetime.datetime.utcnow()
    start_date = dateutil.parser.parse(results['dtstart']).replace(tzinfo=None)
    next_date = start_date + datetime.timedelta(hours=24)
    next_url = url_for('.playlists_date_sets', year=next_date.year,
                       month=next_date.month, day=next_date.day)
    if next_date > now:
        next_url = None

    if start_date < now:
        prev_date = start_date - datetime.timedelta(hours=24)
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
        date=results['dtstart'],
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
    results = call_api("/playlists/dj", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_list.html', djs=results['djs'])


@bp.route('/playlists/dj/all')
def playlists_dj_all():
    results = call_api("/playlists/dj/all", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_list_all.html', djs=results['djs'])


@bp.route('/playlists/dj/<int:dj_id>')
def playlists_dj_sets(dj_id):
    results = call_api("/playlists/dj/{0}", 'GET', dj_id)

    def cast_dates(t):
        if t['dtstart'] is not None:
            t['dtstart'] = dateutil.parser.parse(t['dtstart'])
        if t['dtend'] is not None:
            t['dtend'] = dateutil.parser.parse(t['dtend'])
        return t
    results['sets'] = [cast_dates(t) for t in results['sets']]

    if request.wants_json():
        return jsonify(results)

    return render_template('playlists_dj_sets.html',
                           dj=results['dj'], sets=results['sets'])
# }}}


# Charts {{{
@bp.route('/playlists/charts')
def charts_index():
    periodic_charts = [
        ('playlists.charts_albums', "Top albums"),
        ('playlists.charts_artists', "Top artists"),
        ('playlists.charts_tracks', "Top tracks"),
    ]
    return render_template('charts.html', periodic_charts=periodic_charts)


@bp.route('/playlists/charts/albums')
@bp.route('/playlists/charts/albums/<string:period>')
@bp.route('/playlists/charts/albums/<string:period>/<int:year>')
@bp.route('/playlists/charts/albums/<string:period>/<int:year>/<int:month>')
def charts_albums(period=None, year=None, month=None):
    if period == 'dj' and year is not None:
        return redirect(url_for('.charts_albums_dj', dj_id=year))

    if period is not None and year is not None and month is not None:
        results = call_api("/charts/albums/{0}/{1}/{2}", 'GET',
                           period, year, month)
    elif period is not None and year is not None:
        results = call_api("/charts/albums/{0}/{1}", 'GET',
                           period, year, month)
    elif period is not None:
        results = call_api("/charts/albums/{0}", 'GET',
                           period)
    else:
        results = call_api("/charts/albums", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_albums.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/albums')
def charts_albums_dj(dj_id):
    results = call_api("/charts/dj/{0}/albums", 'GET', dj_id)

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

    if period is not None and year is not None and month is not None:
        results = call_api("/charts/artists/{0}/{1}/{2}", 'GET',
                           period, year, month)
    elif period is not None and year is not None:
        results = call_api("/charts/artists/{0}/{1}", 'GET',
                           period, year, month)
    elif period is not None:
        results = call_api("/charts/artists/{0}", 'GET',
                           period)
    else:
        results = call_api("/charts/artists", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_artists.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/artists')
def charts_artists_dj(dj_id):
    results = call_api("/charts/dj/{0}/artists", 'GET', dj_id)

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

    if period is not None and year is not None and month is not None:
        results = call_api("/charts/tracks/{0}/{1}/{2}", 'GET',
                           period, year, month)
    elif period is not None and year is not None:
        results = call_api("/charts/tracks/{0}/{1}", 'GET',
                           period, year, month)
    elif period is not None:
        results = call_api("/charts/tracks/{0}", 'GET',
                           period)
    else:
        results = call_api("/charts/tracks", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_tracks.html',
                           start=results['start'],
                           end=results['end'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/<int:dj_id>/tracks')
def charts_tracks_dj(dj_id):
    results = call_api("/charts/dj/{0}/tracks", 'GET', dj_id)

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_tracks_dj.html',
                           dj=results['dj'],
                           results=results['results'])


@bp.route('/playlists/charts/dj/spins')
def charts_dj_spins():
    results = call_api("/charts/dj/spins", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_dj_spins.html', results=results['results'])


@bp.route('/playlists/charts/dj/vinyl_spins')
def charts_dj_vinyl_spins():
    results = call_api("/charts/dj/vinyl_spins", 'GET')

    if request.wants_json():
        return jsonify(results)

    return render_template('chart_dj_vinyl_spins.html',
                           results=results['results'])
# }}}


@bp.route('/playlists/set/<int:set_id>')
def playlist(set_id):
    results = call_api("/playlists/set/{0:d}", 'GET', set_id)

    if request.wants_json():
        results.update({
            'archives': [a[0] for a in results['archives']],
            'tracks': [
                tracklog_full_serialize(t) for t in results['tracks']],
        })
        return jsonify(results)

    return render_template('playlist.html',
                           archives=results['archives'],
                           djset=results,
                           tracklogs=results['tracks'])


@bp.route('/playlists/track/<int:track_id>')
def playlists_track(track_id):
    results = call_api("/playlists/track/{0:d}", 'GET', track_id)

    def cast_played(t):
        t['played'] = dateutil.parser.parse(t['played'])
        return t

    results['plays'] = [cast_played(t) for t in results['plays']]

    if request.wants_json():
        results['added'] = str(results['added'])
        results['plays'] = [tracklog_serialize(tl) for tl in results['plays']]
        return jsonify(results)

    return render_template('playlists_track.html',
                           track=results,
                           tracklogs=results['plays'])
