import datetime
from wuvt import db
from wuvt.trackman.lib import get_current_tracklog, serialize_trackinfo
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog
from wuvt.trackman.view_utils import list_archives
from .base import PlaylistResource


class NowPlaying(PlaylistResource):
    def get(self):
        tracklog = TrackLog.query.order_by(db.desc(TrackLog.id)).first()
        return tracklog.api_serialize()


class Last15Tracks(PlaylistResource):
    def get(self):
        tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()
        return {
            'tracks': [t.api_serialize() for t in tracks],
        }


class LatestTrack(PlaylistResource):
    def get(self):
        return serialize_trackinfo(get_current_tracklog())


class PlaylistsByDay(PlaylistResource):
    def get(self, year, month, day):
        dtstart = datetime.datetime(year, month, day, 0, 0, 0)
        dtend = datetime.datetime(year, month, day, 23, 59, 59)
        sets = DJSet.query.\
            filter(DJSet.dtstart >= dtstart, DJSet.dtstart <= dtend).\
            all()

        status_code = 200
        if len(sets) <= 0:
            # return 404 if no playlists found
            status_code = 404

        return {
            'dtstart': dtstart,
            'sets': [s.serialize() for s in sets],
        }, status_code


class PlaylistDJs(PlaylistResource):
    def get(self):
        djs = DJ.query.order_by(DJ.airname).filter(DJ.visible == True)
        return {
            'djs': [dj.serialize() for dj in djs],
        }


class PlaylistAllDJs(PlaylistResource):
    def get(self):
        djs = DJ.query.order_by(DJ.airname).all()
        return {
            'djs': [dj.serialize() for dj in djs],
        }


class PlaylistsByDJ(PlaylistResource):
    def get(self, dj_id):
        dj = DJ.query.get_or_404(dj_id)
        sets = DJSet.query.filter(DJSet.dj_id == dj_id).order_by(
            DJSet.dtstart).all()
        return {
            'dj': dj.serialize(),
            'sets': [s.serialize() for s in sets],
        }


class Playlist(PlaylistResource):
    def get(self, set_id):
        djset = DJSet.query.get_or_404(set_id)
        tracks = TrackLog.query.filter(TrackLog.djset_id == djset.id).order_by(
            TrackLog.played).all()

        data = djset.serialize()
        data.update({
            'archives': [list(a) for a in list_archives(djset)],
            'tracks': [t.api_serialize() for t in tracks],
        })
        return data


class PlaylistTrack(PlaylistResource):
    def get(self, track_id):
        track = Track.query.get_or_404(track_id)
        tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
            order_by(TrackLog.played).all()

        data = track.serialize()
        data['plays'] = [tl.api_serialize() for tl in tracklogs]
        return data
