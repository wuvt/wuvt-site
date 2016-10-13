from celery.decorators import periodic_task
from celery.task.schedules import crontab
from datetime import datetime, timedelta
from flask import json

from .. import app, db, redis_conn
from ..celeryconfig import make_celery
from . import mail
from .lib import get_duplicates, logout_all, enable_automation
from .models import AirLog, DJSet, Track, TrackLog

celery = make_celery(app)


@periodic_task(run_every=crontab(day_of_week=1, hour=0, minute=0))
def email_weekly_charts():
    with app.app_context():
        if app.config['CHART_MAIL']:
            chart = db.session.query(
                Track.artist, Track.album,
                db.func.count(Track.album)).filter(
                    TrackLog.played > datetime.utcnow() - timedelta(days=7),
                    TrackLog.new == True).join(TrackLog).group_by(
                        Track.album, Track.artist).order_by(
                            db.desc(db.func.count(Track.album))).all()
            mail.send_chart(chart)


#@periodic_task(run_every=crontab(hour=3, minute=0))
#def deduplicate_tracks():
#    with app.app_context():
#        dups = get_duplicates(Track, ['artist', 'title', 'album', 'label'])
#        for artist, title, album, label in dups:
#            track_query = Track.query.filter(db.and_(
#                Track.artist == artist,
#                Track.title == title,
#                Track.album == album,
#                Track.label == label)).order_by(Track.id)
#            count = track_query.count()
#            tracks = track_query.all()
#            track_id = int(tracks[0].id)
#
#            # update TrackLogs
#            TrackLog.query.filter(TrackLog.track_id.in_(
#                [track.id for track in tracks[1:]])).update(
#                {TrackLog.track_id: track_id}, synchronize_session=False)
#
#            # delete existing Track entries
#            map(db.session.delete, tracks[1:])
#
#            db.session.commit()
#
#            app.logger.info(
#                "Trackman: Removed {0:d} duplicates of track ID {1:d}".format(
#                    count - 1,
#                    track_id))


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


@periodic_task(run_every=timedelta(seconds=55))
def publish_keepalive():
    with app.app_context():
        redis_conn.publish('trackman_live', json.dumps({
            'event': "keepalive",
        }))

        redis_conn.publish('trackman_dj_live', json.dumps({
            'event': "keepalive",
        }))
