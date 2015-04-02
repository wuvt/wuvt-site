import json
import lxml.etree
import requests
import urlparse
import smtplib
from datetime import timedelta
from datetime import datetime
from flask.json import JSONEncoder
from flask import render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import logging

from wuvt import app
from wuvt import db
from wuvt import sse
from wuvt import redis_conn
from wuvt import format_datetime, localize_datetime
from wuvt.trackman.models import TrackLog, DJSet, DJ


def logout_recent():
    automation_dj = DJ.query.filter(DJ.name == "Automation").first()
    last_djset = DJSet.query.filter(DJSet.dj_id == automation_dj.id).order_by(DJSet.dtstart.desc()).first()
    if last_djset is not None and last_djset.dtend is None:
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


def generate_cuesheet(filename, tracks):
    cuesheet = "FILE \"{}\"\n".format(email.utils.quote(filename))
    i = 1
    for track in tracks:
        cuesheet += """\
    TRACK {index:02d} AUDIO
        TITLE "{title}"
        PERFORMER "{artist}"
        INDEX 01 {h:02d}:{m:02d}:{s:02d}
""".format(index=i, title=email.utils.quote(track.track.title),
           artist=email.utils.quote(track.track.artist),
           h=track.played.hour, m=track.played.minute, s=track.played.second)
        i += 1

    return cuesheet


def disable_automation():
    automation_enabled = redis_conn.get("automation_enabled")
    # Make sure automation is actually enabled before changing the end time
    if automation_enabled is not None and automation_enabled == 'true':
        redis_conn.set("automation_enabled", "false")
        automation_set_id = redis_conn.get("automation_set")
        app.logger.info("Automation disabled with DJSet.id = {}".format(automation_set_id))
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
    app.logger.info("Automation enabled with DJSet.id = {}".format(automation_set.id))
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


def log_track(track_id, djset_id, request=False, vinyl=False, new=False,
              rotation=None):
    track = TrackLog(track_id, djset_id, request=request, vinyl=vinyl, new=new,
                     rotation=rotation,
                     listeners=stream_listeners(app.config['ICECAST_ADMIN']))
    db.session.add(track)
    db.session.commit()

    artist = track.track.artist
    title = track.track.title
    album = track.track.album
    played = localize_datetime(track.played)

    from wuvt.trackman import tasks
    tasks.update_stream.delay(artist, title)
    tasks.update_tunein.delay(artist, title)
    tasks.update_lastfm.delay(artist, title, album, played)

    # send server-sent event
    sse.send(json.dumps({'event': "track_change",
                         'tracklog': track.full_serialize()}, cls=JSONEncoder))

    return track
