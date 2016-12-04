from datetime import timedelta
import email.utils
from flask import current_app, request
from functools import wraps
from urlparse import urljoin
from .. import db, format_datetime
from .lib import perdelta, renew_dj_lease
from .models import TrackLog


def dj_interact(f):
    @wraps(f)
    def dj_wrapper(*args, **kwargs):
        # Call in the function first in case it changes the timeout
        ret = f(*args, **kwargs)
        renew_dj_lease()
        return ret
    return dj_wrapper


def make_external(url):
    return urljoin(request.url_root, url)


def list_archives(djset):
    if len(current_app.config['ARCHIVE_URL_FORMAT']) <= 0:
        return

    start = djset.dtstart.replace(minute=0, second=0, microsecond=0)

    if djset.dtend is None:
        end = start
    else:
        end = djset.dtend.replace(minute=0, second=0, microsecond=0)

    for loghour in perdelta(start, end, timedelta(hours=1)):
        yield ( format_datetime(loghour, current_app.config['ARCHIVE_URL_FORMAT']),
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
            filename = format_datetime(loghour, "%Y%m%d%H0001{}".format(ext))
            cuesheet += generate_cuesheet(filename, loghour, tracks, offset)
            offset += len(tracks)

    return cuesheet
