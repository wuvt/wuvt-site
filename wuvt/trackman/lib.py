import dateutil
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

from .. import app
from .. import cache
from .. import db
from .. import redis_conn
from .. import format_datetime, localize_datetime
from .models import TrackLog, DJSet

CHART_PER_PAGE = 250
CHART_TTL = 14400


def get_duplicates(model, attrs):
    dups = model.query.with_entities(
        *[getattr(model, attr) for attr in attrs]).group_by(
        *[getattr(model, attr) for attr in attrs]).having(db.and_(
            *[db.func.count(getattr(model, attr)) > 1 for attr in attrs])).all()
    return dups


def logout_all():
    open_djsets = DJSet.query.filter(DJSet.dtend == None).order_by(
        DJSet.dtstart.desc()).all()
    for djset in open_djsets:
        djset.dtend = datetime.utcnow()

    db.session.commit()
    redis_conn.delete('dj_timeout')


def logout_all_but_current(dj):
    current_djset = None
    open_djsets = DJSet.query.filter(DJSet.dtend == None).order_by(
        DJSet.dtstart.desc()).all()
    for djset in open_djsets:
        if current_djset is None and djset.dj_id == dj.id:
            current_djset = djset
        else:
            djset.dtend = datetime.utcnow()

    db.session.commit()
    redis_conn.delete('dj_timeout')

    return current_djset


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


def generate_cuesheet(filename, start, tracks, offset=0):
    cuesheet = "FILE \"{}\"\n".format(email.utils.quote(filename))
    i = offset + 1
    for track in tracks:
        if track.played < start:
            offset = timedelta(seconds=0)
        else:
            offset = track.played - start

        minutes, secs = divmod(offset.seconds, 60)

        cuesheet += """\
    TRACK {index:02d} AUDIO
        TITLE "{title}"
        PERFORMER "{artist}"
        INDEX 01 {m:02d}:{s:02d}:00
""".format(index=i, title=email.utils.quote(track.track.title.encode('utf-8')),
           artist=email.utils.quote(track.track.artist.encode('utf-8')),
           m=minutes, s=secs)
        i += 1

    return cuesheet


def generate_playlist_cuesheet(djset, ext):
    cuesheet = """\
PERFORMER "{dj}"
TITLE "{date}"
""".format(
        dj=email.utils.quote(djset.dj.airname.encode('utf-8')),
        date=format_datetime(djset.dtstart, "%Y-%m-%d %H:%M"))

    delta = timedelta(hours=1)
    start = djset.dtstart.replace(minute=0, second=0, microsecond=0)
    end = djset.dtend.replace(minute=59, second=59, microsecond=0) + \
        timedelta(seconds=1)
    offset = 0

    for loghour in perdelta(start, end, delta):
        tracks = TrackLog.query.filter(db.and_(
            TrackLog.djset_id == djset.id,
            TrackLog.played >= loghour,
            TrackLog.played <= loghour + delta)).\
            order_by(TrackLog.played).all()

        if len(tracks) > 0:
            filename = datetime.strftime(localize_datetime(loghour),
                                         "%Y%m%d%H0001{}".format(ext))
            cuesheet += generate_cuesheet(filename, loghour, tracks, offset)
            offset += len(tracks)

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
    if len(url) <= 0:
        return None

    url += 'stats.xml'
    parsed = urlparse.urlparse(url)

    try:
        r = requests.get(url, auth=(parsed.username, parsed.password))
        doc = lxml.etree.fromstring(r.text)
        listeners = doc.xpath('//icestats/listeners/text()')[0]
        return int(listeners)
    except Exception as e:
        app.logger.error(e)
        return None


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

    from . import tasks
    tasks.update_stream.delay(artist, title, album)
    tasks.update_tunein.delay(artist, title)
    tasks.update_lastfm.delay(artist, title, album, played)

    # send server-sent event
    redis_conn.publish(app.config['REDIS_CHANNEL'], json.dumps({
        'event': "track_change",
        'tracklog': track.full_serialize()
    }, cls=JSONEncoder))

    return track


def get_chart_range(period, request):
    if period is not None:
        end = datetime.utcnow()

        if period == 'weekly':
            start = end - timedelta(weeks=1)
        elif period == 'monthly':
            start = end - dateutil.relativedelta.relativedelta(months=1)
        elif period == 'yearly':
            start = end - dateutil.relativedelta.relativedelta(years=1)
        else:
            raise ValueError("Period not one of weekly, monthly, or yearly")
    else:
        if 'start' in request.args:
            start = datetime.strptime(request.args['start'],
                                      "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            first_track = TrackLog.query.order_by(TrackLog.played).first()
            start = first_track.played

        if 'end' in request.args:
            end = datetime.strptime(request.args['end'],
                                    "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            end = datetime.utcnow()

    # reduce date resolution to 1 hour windows tot make caching work
    start = start.replace(minute=0, second=0, microsecond=0)
    end = end.replace(minute=0, second=0, microsecond=0)

    return start, end


def get_chart(cache_key, query, limit=CHART_PER_PAGE):
    results = cache.get('charts:' + cache_key)
    if results is None:
        results = list(query.limit(limit))
        cache.set('charts:' + cache_key, results, timeout=CHART_TTL)
    return results
