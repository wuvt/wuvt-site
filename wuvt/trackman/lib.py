import json
import lxml.etree
import requests
import urlparse

from wuvt import app
from wuvt import db
from wuvt import sse
from wuvt.trackman.models import Track


def stream_listeners(url):
    parsed = urlparse.urlparse(url)
    r = requests.get(url, auth=(parsed.username, parsed.password))
    doc = lxml.etree.fromstring(r.text)
    listeners = doc.xpath('//icestats/listeners/text()')[0]
    return int(listeners)


def log_track(dj_id, djset_id, title, artist, album, label, request=False, vinyl=False):
    track = Track(dj_id=dj_id, djset_id=djset_id, title=title, artist=artist,
            album=album, label=label, request=request, vinyl=vinyl,
            listeners=stream_listeners(app.config['ICECAST_STATS']))
    db.session.add(track)
    db.session.commit()

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
            network.scrobble(artist=track.artist, title=track.title,
                    timestamp=int(time.mktime(track.datetime.timetuple())),
                    album=track.album)
        except Exception as e:
            print(e)

    # send server-sent event
    sse.send(json.dumps({'event': "track_change", 'track':
        track.serialize()}))

    return track
