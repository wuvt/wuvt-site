import json
import lxml.etree
import requests
import urllib
import urlparse
import smtplib
from datetime import timedelta
from datetime import datetime
from dateutil import tz
from flask.json import JSONEncoder
from flask import render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils

from wuvt import app
from wuvt import db
from wuvt import sse
from wuvt import redis_conn
from wuvt import format_datetime, localize_datetime
from wuvt.trackman.models import TrackLog, DJSet

def logout_recent():
    last_djset = DJSet.query.order_by(DJSet.dtstart.desc()).first()
    if last_djset.dtend is None:
        last_djset.dtend = datetime.utcnow()
        db.session.commit()
        redis_conn.delete('dj_timeout')

def perdelta(start, end, td):
    current = start
    while current <= end:
        yield current
        current += td

def list_archives(djset):
    start = djset.dtstart.replace(minute=0, second=0, microsecond=0)

    if djset.dtend is None:
        end = start
    else:
        end = djset.dtend.replace(minute=0, second=0, microsecond=0)

    for loghour in perdelta(start, end, timedelta(hours=1)):
        yield (app.config['ARCHIVE_BASE_URL'] + format_datetime(loghour, "%Y%m%d%H"),
               "-".join([format_datetime(loghour, "%Y-%m-%d %H:00"),
                        format_datetime(loghour + timedelta(hours=1), "%Y-%m-%d %H:00")]),)

def disable_automation():
    redis_conn.set("automation_enabled", "false")
    automation_set_id = redis_conn.get("automation_set")
    if automation_set_id is not None:
        automation_set = DJSet.query.get(int(automation_set_id))
        automation_set.dtend = datetime.utcnow()
        db.session.commit()

def enable_automation():
    redis_conn.set('automation_enabled', "true")

    # Create automation set for automation to log to
    automation_set = DJSet(1)
    db.session.add(automation_set)
    db.session.commit()
    redis_conn.set('automation_set', str(automation_set.id))

def email_playlist(djset):
    msg = MIMEMultipart('alternative')
    msg['Date'] = email.utils.formatdate()
    msg['From'] = app.config['MAIL_FROM']
    msg['To'] = djset.dj.email
    msg['Message-Id'] = email.utils.make_msgid()
    msg['X-Mailer'] = "Trackman"
    msg['Subject'] = "[{name}] {djname} - Playlist from {dtend}".format(
        name=app.config['TRACKMAN_NAME'],
        djname=djset.dj.airname,
        dtend=format_datetime(djset.dtend, "%Y-%m-%d"))

    tracks = djset.tracks

    msg.attach(MIMEText(
        render_template('email/playlist.txt',
                        djset=djset, tracks=tracks).encode('utf-8'),
        'text'))
    msg.attach(MIMEText(
        render_template('email/playlist.html',
                        djset=djset, tracks=tracks).encode('utf-8'),
        'html'))

    s = smtplib.SMTP(app.config['SMTP_SERVER'])
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
    s.quit()


def stream_listeners(url):
    url += 'stats.xml'
    parsed = urlparse.urlparse(url)
    r = requests.get(url, auth=(parsed.username, parsed.password))
    doc = lxml.etree.fromstring(r.text)
    listeners = doc.xpath('//icestats/listeners/text()')[0]
    return int(listeners)


def log_track(track_id, djset_id, request=False, vinyl=False, new=False, rotation=None):
    track = TrackLog(track_id, djset_id, request=request, vinyl=vinyl, new=new, rotation=rotation,
                  listeners=stream_listeners(app.config['ICECAST_ADMIN']))
    db.session.add(track)
    db.session.commit()

    artist = track.track.artist
    title = track.track.title
    album = track.track.album
    played = localize_datetime(track.played)
    # update stream metadata
    for mount in app.config['ICECAST_MOUNTS']:
        song = u'{artist} - {title}'.format(artist=artist, title=title)
        requests.get(app.config['ICECAST_ADMIN'] +
                     u'metadata?mount={mount}&mode=updinfo&song={song}'
                     .format(mount=urllib.quote(mount),
                             song=urllib.quote(song.encode('utf-8'))))

    # update tunein
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

    # update last.fm (yay!)
    if len(app.config['LASTFM_APIKEY']) > 0:
        import pylast
        import hashlib
        import time

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
                timestamp=int(time.mktime(played.timetuple())),
                album=album)
        except Exception as e:
            print(e)

    # send server-sent event
    sse.send(json.dumps({'event': "track_change",
                         'tracklog': track.full_serialize()}, cls=JSONEncoder))

    return track
