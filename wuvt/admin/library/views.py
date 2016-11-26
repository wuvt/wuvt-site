from flask import abort, current_app, flash, render_template, redirect, \
    request, url_for
import string
import uuid

from wuvt import db
from wuvt.admin import bp
from wuvt.auth import check_access
from wuvt.trackman.models import DJ, Track, TrackLog, TrackReport
from wuvt.trackman.lib import deduplicate_track_by_id
from wuvt.trackman.musicbrainz import musicbrainzngs


def validate_uuid(uuid_str):
    try:
        value = uuid.UUID(uuid_str)
    except ValueError:
        return False

    return value.hex == uuid_str.replace('-', '')


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
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])
    artists.items = [x[0] for x in artists.items]
    return render_template('admin/library_letter.html', letter=letter,
                           artists=artists)


@bp.route('/library/djs')
@bp.route('/library/djs/<int:page>')
@check_access('library')
def library_djs(page=1):
    djs = DJ.query.order_by(DJ.airname).paginate(
        page, current_app.config['ARTISTS_PER_PAGE'])
    return render_template('admin/library_djs.html', djs=djs)


@bp.route('/library/dj/<int:id>')
@bp.route('/library/dj/<int:id>/<int:page>')
@check_access('library')
def library_dj(id, page=1):
    dj = DJ.query.get_or_404(id)
    subquery = TrackLog.query.\
        with_entities(TrackLog.track_id).\
        filter(TrackLog.dj_id == id).\
        group_by(TrackLog.track_id).subquery()
    tracks = Track.query.join(subquery).order_by(Track.artist, Track.title).\
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])

    return render_template('admin/library_dj.html', dj=dj, tracks=tracks)


@bp.route('/library/artist')
@check_access('library')
def library_artist():
    artist = request.args['artist']
    tracks = Track.query.filter(Track.artist == artist).\
        order_by(Track.album, Track.title).all()

    return render_template('admin/library_artist.html', artist=artist,
                           tracks=tracks)


@bp.route('/library/labels')
@bp.route('/library/labels/<int:page>')
@check_access('library')
def library_labels(page=1):
    labels = Track.query.with_entities(Track.label).\
        group_by(Track.label).order_by(Track.label).\
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])
    labels.items = [x[0] for x in labels.items]
    return render_template('admin/library_labels.html', labels=labels)


@bp.route('/library/label')
@check_access('library')
def library_label():
    label = request.args['label']
    page = int(request.args.get('page', 1))
    tracks = Track.query.filter(Track.label == label).\
        order_by(Track.album, Track.title).\
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])

    return render_template('admin/library_label.html', label=label,
                           tracks=tracks)


@bp.route('/library/fixup')
@check_access('library')
def library_fixup():
    return render_template('admin/library_fixup.html')


@bp.route('/library/fixup/<string:key>')
@bp.route('/library/fixup/<string:key>/<int:page>')
@check_access('library')
def library_fixup_tracks(key, page=1):
    if key == 'bad_album':
        title = "Invalid Album"
        query = Track.query.filter(db.or_(
            Track.album == "?",
            Track.album == "7\"",
            Track.album == "Not Available",
            Track.album == "s/t",
            Track.album == "Self-Titled"
        ))
    elif key == 'bad_label':
        title = "Invalid Label"
        query = Track.query.filter(db.or_(
            Track.label == "?",
            Track.label == "NONE",
            Track.label == "None",
            Track.label == "Not Available",
            Track.label == "idk",
            Track.label == "n/a",
            Track.label == "none",
            Track.label == "Record Label",
            Track.label == "same",
            Track.label == "-",
            Track.label == "--",
            Track.label == "---"
        ))
    elif key == 'one_play':
        title = "Only One Play"
        query = Track.query.join(Track.plays).having(
            db.func.count(TrackLog.id) == 1).group_by(Track)
    else:
        abort(404)

    tracks = query.order_by(Track.artist, Track.title).\
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])

    return render_template('admin/library_fixup_tracks.html', key=key,
                           title=title, tracks=tracks)


@bp.route('/library/track/<int:id>', methods=['GET', 'POST'])
@check_access('library')
def library_track(id):
    track = Track.query.get_or_404(id)
    edit_from = request.args.get('from', None)
    error_fields = []
    data = {}

    fields = ['artist', 'title', 'album', 'label', 'artist_mbid',
              'recording_mbid', 'release_mbid', 'releasegroup_mbid']
    for field in fields:
        data[field] = request.args.get(field, getattr(track, field))

    if request.method == 'POST':
        for field in fields:
            data[field] = request.form[field]

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

        musicbrainz_fields = [
            'artist_mbid',
            'recording_mbid',
            'release_mbid',
            'releasegroup_mbid',
        ]

        for field in musicbrainz_fields:
            value = request.form[field].strip()
            if value != getattr(track, field):
                if len(value) > 0:
                    if validate_uuid(value):
                        setattr(track, field, value)
                    else:
                        error_fields.append(field)
                else:
                    setattr(track, field, None)

        if len(error_fields) <= 0:
            track.artist = artist
            track.title = title
            track.album = album
            track.label = label
            db.session.commit()

            # merge with any tracks that exactly match
            deduplicate_track_by_id(id)

            if edit_from == 'label':
                return redirect(url_for('admin.library_label',
                                        label=track.label))
            else:
                return redirect(url_for('admin.library_artist',
                                        artist=track.artist))

    return render_template('admin/library_track.html',
                           track=track,
                           edit_from=edit_from,
                           error_fields=error_fields,
                           data=data)


@bp.route('/library/track/<int:id>/musicbrainz', methods=['GET', 'POST'])
@check_access('library')
def library_track_musicbrainz(id):
    musicbrainzngs.set_hostname(current_app.config['MUSICBRAINZ_HOSTNAME'])

    track = Track.query.get_or_404(id)
    edit_from = request.args.get('from', None)

    if request.method == 'POST':
        if request.form.get('clear_mbids', None) == "true":
            track.artist_mbid = None
            track.recording_mbid = None
            track.release_mbid = None
            track.releasegroup_mbid = None
            db.session.commit()

            flash("The MusicBrainz IDs for the track have been cleared.")
            return redirect(url_for('admin.library_track', id=track.id,
                                    **{'from': edit_from}))

        result = musicbrainzngs.get_recording_by_id(
            request.form['recording_mbid'],
            includes=['artist-credits', 'releases'])

        if 'artist-credit' in result['recording']:
            if len(result['recording']['artist-credit']) == 1:
                # if there's only one artist, use that ID
                track.artist_mbid = \
                    result['recording']['artist-credit'][0]['artist']['id']
            else:
                track.artist_mbid = None
                for entry in result['recording']['artist-credit']:
                    # it seems it's sometimes possible for us to get something
                    # that isn't well-formed, so deal with that case
                    if type(entry) == dict and \
                            entry['artist'] == dict and \
                            entry['artist'].get('name', None) == track.artist:
                        # if there's an exact artist match, use that ID
                        # otherwise artist will be left blank
                        track.artist_mbid = entry['artist']['id']
                        break
        else:
            track.artist_mbid = None
            current_app.logger.warning(
                "No artist-credit in MusicBrainz result")

        track.recording_mbid = result['recording']['id']

        selected_release_mbid = request.form.get(
            'recording_{}_release'.format(track.recording_mbid),
            '').strip()
        if len(selected_release_mbid) > 0:
            for release in result['recording']['release-list']:
                if release['id'] == selected_release_mbid:
                    track.release_mbid = release['id']
                    rresult = musicbrainzngs.get_release_by_id(
                        track.release_mbid,
                        includes=['release-groups'])
                    track.releasegroup_mbid = \
                        rresult['release']['release-group']['id']
                    break
        else:
            track.release_mbid = None
            track.releasegroup_mbid = None

        db.session.commit()

        return redirect(url_for('admin.library_track', id=track.id,
                                **{'from': edit_from}))

    results = musicbrainzngs.search_recordings(artist=track.artist,
                                               recording=track.title,
                                               release=track.album)

    return render_template('admin/library_track_musicbrainz.html',
                           track=track,
                           edit_from=edit_from,
                           results=results['recording-list'])


@bp.route('/library/track/<int:id>/similar', methods=['GET', 'POST'])
@bp.route('/library/track/<int:id>/similar/<int:page>', methods=['GET', 'POST'])
@check_access('library')
def library_track_similar(id, page=1):
    track = Track.query.get_or_404(id)
    edit_from = request.args.get('from', None)

    if request.method == 'POST':
        merge = [int(x) for x in request.form.getlist('merge[]')]
        if len(merge) > 0:
            # update TrackLogs
            TrackLog.query.filter(TrackLog.track_id.in_(merge)).update(
                {TrackLog.track_id: track.id}, synchronize_session=False)

            # update TrackReports
            TrackReport.query.filter(TrackReport.track_id.in_(merge)).update(
                {
                    TrackReport.track_id: track.id,
                    TrackReport.resolution: "Merged track",
                    TrackReport.open: False
                },
                synchronize_session=False)

            # delete existing Track entries
            Track.query.filter(Track.id.in_(merge)).delete(
                synchronize_session=False)

            db.session.commit()

            current_app.logger.warning(
                "Trackman: Merged tracks {0} into track {1}".format(
                    ", ".join([str(x) for x in merge]),
                    track.id))
            flash("Tracks merged.")

            return redirect(url_for('admin.library_track', id=track.id,
                                    **{'from': edit_from}))

    similar_tracks = Track.query.\
        filter(db.and_(
            db.func.lower(Track.artist) == db.func.lower(track.artist),
            db.func.lower(Track.album) == db.func.lower(track.album),
            db.func.lower(Track.title) == db.func.lower(track.title)
        )).\
        group_by(Track.id).order_by(Track.artist).\
        paginate(page, current_app.config['ARTISTS_PER_PAGE'])

    return render_template('admin/library_track_similar.html', track=track,
                           edit_from=edit_from, similar_tracks=similar_tracks)


@bp.route('/library/track/<int:id>/spins')
@check_access('library')
def library_track_spins(id):
    track = Track.query.get_or_404(id)
    edit_from = request.args.get('from', None)
    tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
        order_by(TrackLog.played).all()

    return render_template('admin/library_track_spins.html', track=track,
                           edit_from=edit_from, tracklogs=tracklogs)
