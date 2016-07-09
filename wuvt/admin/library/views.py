from collections import defaultdict
from flask import abort, render_template, redirect, request, url_for
import string

from wuvt import app
from wuvt import db
from wuvt.admin import bp
from wuvt.auth import check_access
from wuvt.trackman.models import DJ, Track, TrackLog


@bp.route('/library')
@check_access('library')
def library_index():
    letters = list(string.digits + string.ascii_uppercase)
    return render_template('admin/library_index.html',
                           letters=letters + ['all'])


@bp.route('/library/<string:letter>')
@bp.route('/library/<string:letter>/<int:page>')
@check_access('library')
def library_letter(letter, page=1):
    artists_query = Track.query.with_entities(Track.artist)

    if len(letter) == 1:
        artists_query = artists_query.filter(
            Track.artist.ilike('{}%'.format(letter)))
    elif letter != 'all':
        abort(400)

    artists = artists_query.group_by(Track.artist).order_by(Track.artist).\
        paginate(page, app.config['ARTISTS_PER_PAGE'])
    artists.items = [x[0] for x in artists.items]
    return render_template('admin/library_letter.html', letter=letter,
                           artists=artists)


@bp.route('/library/djs')
@bp.route('/library/djs/<int:page>')
@check_access('library')
def library_djs(page=1):
    djs = DJ.query.order_by(DJ.airname).paginate(
        page, app.config['ARTISTS_PER_PAGE'])
    return render_template('admin/library_djs.html', djs=djs)


@bp.route('/library/dj/<int:id>')
@bp.route('/library/dj/<int:id>/<int:page>')
@check_access('library')
def library_dj(id, page=1):
    dj = DJ.query.get_or_404(id)
    tracks = TrackLog.query.join(Track).\
        filter(TrackLog.dj_id == id).\
        group_by(TrackLog.track_id).order_by(Track.artist, Track.title).\
        paginate(page, app.config['ARTISTS_PER_PAGE'])
    return render_template('admin/library_dj.html', dj=dj, tracks=tracks)


@bp.route('/library/artist')
@check_access('library')
def library_artist():
    artist = request.args['artist']
    track_dict = defaultdict(list)

    tracks = Track.query.filter(Track.artist == artist).\
        order_by(Track.album, Track.title).all()
    for track in tracks:
        track_dict[track.album].append(track)

    return render_template('admin/library_artist.html', artist=artist,
                           albums=sorted(track_dict.items()))


@bp.route('/library/track/<int:id>', methods=['GET', 'POST'])
@check_access('library')
def library_track(id):
    track = Track.query.get_or_404(id)
    tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
        order_by(TrackLog.played).all()
    error_fields = []

    if request.method == 'POST':
        artist = request.form['artist'].strip()
        if len(artist) <= 0:
            error_fields.append('artist')

        title = request.form['title'].strip()
        if len(title) <= 0:
            error_fields.append('title')

        album = request.form['album'].strip()
        if len(album) <= 0:
            error_fields.append('album')

        label = request.form['label'].strip()
        if len(label) <= 0:
            error_fields.append('label')

        # TODO: merge with any tracks that exactly match

        if len(error_fields) <= 0:
            track.artist = artist
            track.title = title
            track.album = album
            track.label = label
            db.session.commit()

            return redirect(url_for('admin.library_artist',
                                    artist=track.artist))

    return render_template('admin/library_track.html', track=track,
                           tracklogs=tracklogs, error_fields=error_fields)
