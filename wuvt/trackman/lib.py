import requests
import urlparse
from datetime import datetime, timedelta
from flask import current_app, json

from .. import db, redis_conn
from . import mail
from .models import AirLog, Track, TrackLog, DJ, DJSet


def get_duplicates(model, attrs):
    dups = model.query.with_entities(
        *[getattr(model, attr) for attr in attrs]).group_by(
        *[getattr(model, attr) for attr in attrs]).having(db.and_(
            *[db.func.count(getattr(model, attr)) > 1 for attr in attrs])).all()
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
    track = TrackLog(
        track_id,
        djset_id,
        request=request,
        vinyl=vinyl,
        new=new,
        rotation=rotation,
        listeners=stream_listeners(current_app.config['ICECAST_URL'],
                                   current_app.config['ICECAST_MOUNTS']))
    db.session.add(track)
    db.session.commit()

    redis_conn.publish('trackman_live', json.dumps({
        'event': "track_change",
        'tracklog': track.full_serialize(),
    }))

    return track


def get_current_tracklog():
    return TrackLog.query.order_by(db.desc(TrackLog.id)).first()


def fixup_current_track(event="track_edit"):
    tracklog = get_current_tracklog()

    redis_conn.publish('trackman_live', json.dumps({
        'event': event,
        'tracklog': tracklog.full_serialize(),
    }))


def deduplicate_track_by_id(dedup_id):
    source_track = Track.query.get(dedup_id)
    if source_track is None:
        current_app.logger.info(
            "Trackman: Track ID {0:d} not found.".format(dedup_id))
        return

    track_query = Track.query.filter(db.and_(
        Track.artist == source_track.artist,
        Track.title == source_track.title,
        Track.album == source_track.album,
        Track.label == source_track.label)).order_by(Track.id)

    count = track_query.count()
    tracks = track_query.all()
    track_id = int(tracks[0].id)

    # update TrackLogs
    TrackLog.query.filter(TrackLog.track_id.in_(
        [track.id for track in tracks[1:]])).update(
        {TrackLog.track_id: track_id}, synchronize_session=False)

    # delete existing Track entries
    map(db.session.delete, tracks[1:])

    db.session.commit()

    current_app.logger.info(
        "Trackman: Merged {0:d} duplicates of track ID {1:d} into track "
        "ID {2:d}".format(
            count - 1,
            dedup_id,
            track_id))


def deduplicate_all_tracks():
    dups = get_duplicates(Track, ['artist', 'title', 'album', 'label'])
    for artist, title, album, label in dups:
        track_query = Track.query.filter(db.and_(
            Track.artist == artist,
            Track.title == title,
            Track.album == album,
            Track.label == label)).order_by(Track.id)

        count = track_query.count()
        tracks = track_query.all()
        track_id = int(tracks[0].id)

        # update TrackLogs
        TrackLog.query.filter(TrackLog.track_id.in_(
            [track.id for track in tracks[1:]])).update(
            {TrackLog.track_id: track_id}, synchronize_session=False)

        # delete existing Track entries
        map(db.session.delete, tracks[1:])

        db.session.commit()

        current_app.logger.info(
            "Trackman: Merged {0:d} duplicates into track ID {1:d}".format(
                count - 1,
                track_id))


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
