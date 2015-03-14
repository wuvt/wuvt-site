import hashlib
import requests
import time
import urllib
from datetime import timedelta

from celery.decorators import periodic_task, task

from wuvt import app
from wuvt import redis_conn
from wuvt.celeryconfig import make_celery
from wuvt.trackman.lib import logout_recent, enable_automation

celery = make_celery(app)


@periodic_task(run_every=timedelta(minutes=1))
def autologout_check():
    active = redis_conn.get('dj_active')
    automation = redis_conn.get('automation_enabled')
    # active is None if dj_active has expired (no activity)
    if active is None:
        if automation is None:
            # This should never happen
            pass
        elif automation == "true":
            # automation is running, carry on
            # if automation is enabled then logout_recent was already called
            pass
        else:
            # Automation is not running, end djset if exists and start
            # automation
            logout_recent()
            enable_automation()


@task
def update_stream(artist, title):
    for mount in app.config['ICECAST_MOUNTS']:
        song = u'{artist} - {title}'.format(artist=artist, title=title)
        requests.get(app.config['ICECAST_ADMIN'] +
                     u'metadata?mount={mount}&mode=updinfo&song={song}'
                     .format(mount=urllib.quote(mount),
                             song=urllib.quote(song.encode('utf-8'))))


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
def update_lastfm(artist, title, album, played):
    if len(app.config['LASTFM_APIKEY']) > 0:
        import pylast

        h = hashlib.md5()
        h.update(app.config['LASTFM_PASSWORD'])
        password_hash = h.hexdigest()

        network = pylast.LastFMNetwork(
            api_key=app.config['LASTFM_APIKEY'],
            api_secret=app.config['LASTFM_SECRET'],
            username=app.config['LASTFM_USERNAME'],
            password_hash=password_hash)
        network.scrobble(
            artist=artist,
            title=title,
            timestamp=int(time.mktime(played.timetuple())),
            album=album)
