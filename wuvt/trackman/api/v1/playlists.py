import datetime
from flask import request
from flask_restful import abort, Resource
from wuvt import db
from wuvt.trackman.lib import get_current_tracklog, serialize_trackinfo
from wuvt.trackman.models import DJ, DJSet, Track, TrackLog
from wuvt.trackman.view_utils import list_archives
from .base import PlaylistResource


class NowPlaying(PlaylistResource):
    def get(self):
        """
        Retrieve information about what is currently playing.
        ---
        operationId: getNowPlaying
        tags:
        - trackman
        - playlists
        - tracklog
        - track
        """
        tracklog = TrackLog.query.order_by(db.desc(TrackLog.id)).first()
        return tracklog.api_serialize()


class Last15Tracks(PlaylistResource):
    def get(self):
        """
        Retrieve information about the last 15 tracks that were played.
        ---
        operationId: getLast15
        tags:
        - trackman
        - playlists
        - tracklog
        - track
        """
        tracks = TrackLog.query.order_by(db.desc(TrackLog.id)).limit(15).all()
        return {
            'tracks': [t.api_serialize() for t in tracks],
        }


class LatestTrack(PlaylistResource):
    def get(self):
        """
        Retrieve information about what is currently playing in the old format.
        ---
        operationId: getLatestTrack
        tags:
        - trackman
        - playlists
        - tracklog
        - track
        """
        return serialize_trackinfo(get_current_tracklog())


class PlaylistsByDay(PlaylistResource):
    def get(self, year, month, day):
        """
        Get a list of playlists played on a particular day.
        ---
        operationId: getPlaylistsByDay
        tags:
        - trackman
        - track
        parameters:
        - in: path
          name: year
          type: integer
          required: true
          description: Year
        - in: path
          name: month
          type: integer
          required: true
          description: Month
        - in: path
          name: day
          type: integer
          required: true
          description: Day of month
        responses:
          404:
            description: No playlists found
        """
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


class PlaylistsByDateRange(Resource):
    def get(self):
        try:
            start = datetime.datetime.strptime(request.args['start'],
                                               "%Y-%m-%dT%H:%M:%S.%fZ")
            end = datetime.datetime.strptime(request.args['end'],
                                             "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            abort(400)

        sets = DJSet.query.\
            filter(DJSet.dtstart >= start, DJSet.dtstart <= end).\
            order_by(db.desc(DJSet.dtstart)).\
            limit(300).all()

        return {
            'sets': [s.serialize() for s in sets],
        }


class PlaylistDJs(PlaylistResource):
    def get(self):
        """
        List DJs who have played something recently.
        ---
        operationId: getPlaylistDJs
        tags:
        - trackman
        - playlists
        - dj
        """
        djs = DJ.query.order_by(DJ.airname).filter(DJ.visible == True)
        return {
            'djs': [dj.serialize() for dj in djs],
        }


class PlaylistAllDJs(PlaylistResource):
    def get(self):
        """
        List all DJs, even those that haven't played anything in a while.
        ---
        operationId: getPlaylistAllDJs
        tags:
        - trackman
        - playlists
        - dj
        """
        djs = DJ.query.order_by(DJ.airname).all()
        return {
            'djs': [dj.serialize() for dj in djs],
        }


class PlaylistsByDJ(PlaylistResource):
    def get(self, dj_id):
        """
        Get a list of playlists played by a particular DJ.
        ---
        operationId: getPlaylistsByDJ
        tags:
        - trackman
        - track
        parameters:
        - in: path
          name: dj_id
          type: integer
          required: true
          description: The ID of a DJ
        responses:
          404:
            description: DJ not found
        """
        dj = DJ.query.get_or_404(dj_id)
        sets = DJSet.query.filter(DJSet.dj_id == dj_id).order_by(
            DJSet.dtstart).all()
        return {
            'dj': dj.serialize(),
            'sets': [s.serialize() for s in sets],
        }


class Playlist(PlaylistResource):
    def get(self, set_id):
        """
        Get a list of tracks and archive links for a playlist.
        ---
        operationId: getPlaylist
        tags:
        - trackman
        - track
        parameters:
        - in: path
          name: set_id
          type: integer
          required: true
          description: The ID of an existing playlist
        responses:
          404:
            description: Playlist not found
        """
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
        """
        Get information about a Track.
        ---
        operationId: getPlaylistTrack
        tags:
        - trackman
        - track
        parameters:
        - in: path
          name: track_id
          type: integer
          required: true
          description: The ID of an existing Track
        responses:
          404:
            description: Track not found
        """
        track = Track.query.get_or_404(track_id)
        tracklogs = TrackLog.query.filter(TrackLog.track_id == track.id).\
            order_by(TrackLog.played).all()

        data = track.api_serialize()
        data['plays'] = [tl.api_serialize() for tl in tracklogs]
        return data
