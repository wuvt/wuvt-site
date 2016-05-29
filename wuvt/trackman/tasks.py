import hashlib
import requests
import urllib
from celery.decorators import periodic_task, task
from celery.task.schedules import crontab
from datetime import datetime, timedelta

from .. import app, db, redis_conn
from ..celeryconfig import make_celery
from . import mail
from .lib import get_duplicates, logout_all, enable_automation
from .models import AirLog, DJ, DJSet, Track, TrackLog

celery = make_celery(app)


@periodic_task(run_every=crontab(hour=3, minute=0))
def deduplicate_tracks():
    with app.app_context():
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

            app.logger.info(
                "Trackman: Removed {0:d} duplicates of track ID {1:d}".format(
                    count - 1,
                    track_id))


@periodic_task(run_every=crontab(hour=6, minute=0))
def playlist_cleanup():
    with app.app_context():
        app.logger.debug("Trackman: Starting playlist cleanup...")

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

        app.logger.debug("Trackman: Removed {} empty DJSets.".format(
            empty.count()))


@periodic_task(run_every=timedelta(minutes=1))
def autologout_check():
    with app.app_context():
        active = redis_conn.get('dj_active')
        automation = redis_conn.get('automation_enabled')
        # active is None if dj_active has expired (no activity)
        if active is None:
            if automation is None:
                # This happens when the key is missing;
                # We just bail out because we don't know the current state
                pass
            elif automation == "true":
                # Automation is already enabled, carry on
                pass
            else:
                # Automation is disabled; end djset if exists and start
                # automation
                logout_all(send_email=True)
                enable_automation()


@task
def update_stream(artist, title, album):
    for mount in app.config['ICECAST_MOUNTS']:
        requests.get(app.config['ICECAST_ADMIN'] + u'metadata', params={
            u'mount': mount,
            u'mode': u'updinfo',
            u'album': album,
            u'artist': artist,
            u'title': title,
        })


@task
def update_tunein(artist, title):
    if len(app.config['TUNEIN_PARTNERID']) > 0:
        requests.get(
            u'http://air.radiotime.com/Playing.ashx?partnerId={partner_id}'
            u'&partnerKey={partner_key}&id={station_id}&title={title}'
            u'&artist={artist}'.format(
                partner_id=urllib.quote(app.config['TUNEIN_PARTNERID']),
                partner_key=urllib.quote(app.config['TUNEIN_PARTNERKEY']),
                station_id=urllib.quote(app.config['TUNEIN_STATIONID']),
                artist=urllib.quote(artist.encode('utf-8')),
                title=urllib.quote(title.encode('utf-8'))
            ))


@task
def update_lastfm(artist, title, album, timestamp):
    if len(app.config['LASTFM_APIKEY']) > 0:
        import pylast

        h = hashlib.md5()
        h.update(app.config['LASTFM_PASSWORD'])
        password_hash = h.hexdigest()

        try:
            network = pylast.LastFMNetwork(
                api_key=app.config['LASTFM_APIKEY'],
                api_secret=app.config['LASTFM_SECRET'],
                username=app.config['LASTFM_USERNAME'],
                password_hash=password_hash)
            network.scrobble(
                artist=artist,
                title=title,
                timestamp=timestamp,
                album=album)
        except Exception as exc:
            app.logger.warning("Trackman: Last.fm scrobble failed: {}".format(
                exc))


@task
def email_playlist(djset_id):
    djset = DJSet.query.get(djset_id)
    tracks = TrackLog.query.filter(TrackLog.djset_id == djset_id).order_by(
        TrackLog.played).all()

    try:
        mail.send_playlist(djset, tracks)
    except Exception as exc:
        app.logger.warning(
            "Trackman: Failed to send email for DJ set {0}: {1}".format(
                djset.id, exc))
