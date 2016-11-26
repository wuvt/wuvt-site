import requests
import urlparse
from datetime import datetime, timedelta
from flask import current_app, json

from .. import cache, db, redis_conn
from . import mail
from .models import AirLog, Track, TrackLog, DJ, DJSet


def get_duplicates(model, attrs, ignore_case=False):
    if ignore_case:
        model_attrs = [db.func.lower(getattr(model, attr)) for attr in attrs]
    else:
        model_attrs = [getattr(model, attr) for attr in attrs]

    dups = model.query.with_entities(
        *model_attrs).group_by(
        *model_attrs).having(db.and_(
            *[db.func.count(attr) > 1 for attr in model_attrs])).all()
    return dups


def logout_all(send_email=False):
    open_djsets = DJSet.query.filter(DJSet.dtend == None).order_by(
        DJSet.dtstart.desc()).all()
    for djset in open_djsets:
        djset.dtend = datetime.utcnow()

        if send_email and djset.dj_id > 1:
            dj = DJ.query.get(djset.dj_id)
            mail.send_logout_reminder(dj)

    db.session.commit()

    redis_conn.publish('trackman_dj_live', json.dumps({
        'event': "session_end",
    }))
    redis_conn.delete('dj_timeout')


def logout_all_except(dj_id):
    current_djset = None
    open_djsets = DJSet.query.filter(DJSet.dtend == None).order_by(
        DJSet.dtstart.desc()).all()
    for djset in open_djsets:
        if current_djset is None and djset.dj_id == dj_id:
            current_djset = djset
        else:
            djset.dtend = datetime.utcnow()

    db.session.commit()

    return current_djset


def perdelta(start, end, td):
    current = start
    while current <= end:
        yield current
        current += td


def disable_automation():
    automation_enabled = redis_conn.get("automation_enabled")
    # Make sure automation is actually enabled before changing the end time
    if automation_enabled is not None and automation_enabled == 'true':
        redis_conn.set("automation_enabled", "false")
        automation_set_id = redis_conn.get("automation_set")
        current_app.logger.info("Trackman: Automation disabled with DJSet.id "
                                "= {}".format(automation_set_id))
        if automation_set_id is not None:
            automation_set = DJSet.query.get(int(automation_set_id))
            if automation_set is not None:
                automation_set.dtend = datetime.utcnow()
                db.session.commit()
            else:
                current_app.logger.warning(
                    "Trackman: The provided automation set ({0}) was not "
                    "found in the database.".format(automation_set_id))


def enable_automation():
    redis_conn.set('automation_enabled', "true")

    # try to reuse existing DJSet if possible
    automation_set = logout_all_except(1)
    if automation_set is None:
        automation_set = DJSet(1)
        db.session.add(automation_set)
        db.session.commit()

    current_app.logger.info("Trackman: Automation enabled with DJSet.id "
                            "= {}".format(automation_set.id))
    redis_conn.set('automation_set', str(automation_set.id))


def stream_listeners(url, mounts=None, timeout=5):
    if len(url) <= 0:
        return None

    try:
        # this requires icecast 2.4
        r = requests.get(urlparse.urljoin(url, 'status-json.xsl'),
                         timeout=timeout)
        data = r.json()
        listeners = 0
        for source in data['icestats']['source']:
            if mounts is not None and len(mounts) > 0:
                parsed_url = urlparse.urlparse(source['listenurl'])
                if parsed_url.path not in mounts:
                    continue
            listeners += int(source['listeners'])

        return listeners
    except Exception as e:
        current_app.logger.error("Trackman: Error fetching stream listeners: "
                                 "{}".format(e))
        return None


def log_track(track_id, djset_id, request=False, vinyl=False, new=False,
              rotation=None):
    tracklog = TrackLog(
        track_id,
        djset_id,
        request=request,
        vinyl=vinyl,
        new=new,
        rotation=rotation,
        listeners=stream_listeners(current_app.config['ICECAST_URL'],
                                   current_app.config['ICECAST_MOUNTS']))
    db.session.add(tracklog)
    db.session.commit()

    cache.set('trackman_now_playing', serialize_trackinfo(tracklog))
    redis_conn.publish('trackman_live', json.dumps({
        'event': "track_change",
        'tracklog': tracklog.full_serialize(),
    }))

    return tracklog


def serialize_trackinfo(tracklog):
    if tracklog is not None:
        data = tracklog.track.serialize()
        data['listeners'] = tracklog.listeners
        data['played'] = str(tracklog.played)

        if tracklog.djset == None:
            dj = DJ.query.filter_by(name="Automation").first()
            data['dj'] = dj.airname
            data['dj_id'] = 0
        else:
            data['dj'] = tracklog.djset.dj.airname
            if tracklog.djset.dj.visible:
                data['dj_id'] = tracklog.djset.dj_id
            else:
                data['dj_id'] = 0
    else:
        data = {
            'artist': "",
            'title': "",
            'album': "",
            'label': "",
            'dj': "",
            'dj_id': 0,
        }

    data['description'] = current_app.config['STATION_NAME']
    data['contact'] = current_app.config['STATION_URL']
    return data


def get_current_tracklog():
    return TrackLog.query.order_by(db.desc(TrackLog.id)).first()


def fixup_current_track(event="track_edit"):
    tracklog = get_current_tracklog()

    cache.set('trackman_now_playing', serialize_trackinfo(tracklog))
    redis_conn.publish('trackman_live', json.dumps({
        'event': event,
        'tracklog': tracklog.full_serialize(),
    }))


def merge_duplicate_tracks(*args, **kwargs):
    track_query = Track.query.filter(*args, **kwargs).order_by(Track.id)

    count = track_query.count()
    tracks = track_query.all()
    track_id = int(tracks[0].id)

    if len(tracks) > 1:
        # update TrackLogs
        TrackLog.query.filter(TrackLog.track_id.in_(
            [track.id for track in tracks[1:]])).update(
            {TrackLog.track_id: track_id}, synchronize_session=False)

        # delete existing Track entries
        map(db.session.delete, tracks[1:])

        db.session.commit()

    return count, track_id


def deduplicate_track_by_id(dedup_id, ignore_case=False):
    source_track = Track.query.get(dedup_id)
    if source_track is None:
        current_app.logger.info(
            "Trackman: Track ID {0:d} not found.".format(dedup_id))
        return

    fields = ['artist', 'title', 'album', 'label']
    if ignore_case:
        count, track_id = merge_duplicate_tracks(db.and_(*[
            db.func.lower(getattr(Track, field)) ==
            db.func.lower(getattr(source_track, field))
            for field in fields
        ]))
    else:
        count, track_id = merge_duplicate_tracks(db.and_(*[
            getattr(Track, field) == getattr(source_track, field)
            for field in fields
        ]))

    current_app.logger.info(
        "Trackman: Merged {0:d} duplicates of track ID {1:d} into track "
        "ID {2:d}".format(
            count - 1,
            dedup_id,
            track_id))


def deduplicate_all_tracks(ignore_case=False):
    dups = get_duplicates(Track, ['artist', 'title', 'album', 'label'],
                          ignore_case=ignore_case)
    for artist, title, album, label in dups:
        if ignore_case:
            count, track_id = merge_duplicate_tracks(db.and_(
                db.func.lower(Track.artist) == db.func.lower(artist),
                db.func.lower(Track.title) == db.func.lower(title),
                db.func.lower(Track.album) == db.func.lower(album),
                db.func.lower(Track.label) == db.func.lower(label)))
        else:
            count, track_id = merge_duplicate_tracks(db.and_(
                Track.artist == artist,
                Track.title == title,
                Track.album == album,
                Track.label == label))

        current_app.logger.info(
            "Trackman: Merged {0:d} duplicates into track ID {1:d}".format(
                count - 1,
                track_id))


def autofill_na_labels():
    na_label_tracks = Track.query.filter(Track.label == u"Not Available").all()
    for na_track in na_label_tracks:
        other_track = Track.query.filter(db.and_(
            Track.artist == na_track.artist,
            Track.title == na_track.title,
            Track.album == na_track.album,
            Track.label != u"Not Available")).first()
        if other_track is not None:
            # update TrackLogs to point to other Track
            TrackLog.query.filter(TrackLog.track_id == na_track.id).update(
                {TrackLog.track_id: other_track.id}, synchronize_session=False)

            db.session.delete(na_track)
            db.session.commit()

            current_app.logger.info(
                "Trackman: Found a track with a label for track ID {0:d}, "
                "merged into {1:d}".format(na_track.id, other_track.id))


def email_weekly_charts():
    if current_app.config['CHART_MAIL']:
        chart = db.session.query(
            Track.artist, Track.album,
            db.func.count(Track.album)).filter(
                TrackLog.played > datetime.utcnow() - timedelta(days=7),
                TrackLog.new == True).join(TrackLog).group_by(
                    Track.album, Track.artist).order_by(
                        db.desc(db.func.count(Track.album))).all()
        mail.send_chart(chart)


def prune_empty_djsets():
    prune_before = datetime.utcnow() - timedelta(days=1)
    empty = DJSet.query.outerjoin(TrackLog).outerjoin(AirLog).group_by(
        DJSet.id).filter(db.and_(
            DJSet.dtend != None,
            DJSet.dtstart < prune_before
        )).having(db.and_(
            db.func.count(TrackLog.id) < 1,
            db.func.count(AirLog.id) < 1
        ))
    for djset in empty.all():
        db.session.delete(djset)
    db.session.commit()

    current_app.logger.debug("Trackman: Removed {} empty DJSets.".format(
        empty.count()))
