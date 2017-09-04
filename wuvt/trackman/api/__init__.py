from flask import Blueprint, json, make_response
from flask_restful import Api

from .v1.airlog import AirLog, AirLogList
from .v1.autologout import AutologoutControl
from .v1.automation import AutomationLog
from .v1.dj import DJ
from .v1.djset import DJSet, DJSetEnd, DJSetList
from .v1.rotation import RotationList
from .v1.track import Track, TrackReport, TrackSearch, TrackAutoComplete, \
    TrackList
from .v1.tracklog import TrackLog, TrackLogList
from .v1.charts import Charts, AlbumCharts, DJAlbumCharts, ArtistCharts, \
    DJArtistCharts, TrackCharts, DJTrackCharts, DJSpinCharts, DJVinylSpinCharts
from .v1.playlists import NowPlaying, Last15Tracks, LatestTrack, \
    PlaylistsByDay, PlaylistDJs, PlaylistAllDJs, PlaylistsByDJ, Playlist, \
    PlaylistTrack


api_bp = Blueprint('trackman_api', __name__)
api = Api(api_bp)
api.add_resource(AutomationLog, '/automation/log')
api.add_resource(DJ, '/dj/<int:djset_id>')
api.add_resource(DJSet, '/djset/<int:djset_id>')
api.add_resource(DJSetEnd, '/djset/<int:djset_id>/end')
api.add_resource(DJSetList, '/djset')
api.add_resource(Track, '/track/<int:track_id>')
api.add_resource(TrackReport, '/track/<int:track_id>/report')
api.add_resource(TrackSearch, '/search')
api.add_resource(TrackAutoComplete, '/autocomplete')
api.add_resource(TrackList, '/track')
api.add_resource(TrackLog, '/tracklog/edit/<int:tracklog_id>')
api.add_resource(TrackLogList, '/tracklog')
api.add_resource(AutologoutControl, '/autologout')
api.add_resource(AirLog, '/airlog/edit/<int:airlog_id>')
api.add_resource(AirLogList, '/airlog')
api.add_resource(RotationList, '/rotations')
api.add_resource(Charts, '/charts')
api.add_resource(AlbumCharts,
                 '/charts/albums',
                 '/charts/albums/<string:period>',
                 '/charts/albums/<string:period>/<int:year>',
                 '/charts/albums/<string:period>/<int:year>/<int:month>')
api.add_resource(DJAlbumCharts, '/charts/dj/<int:dj_id>/albums')
api.add_resource(ArtistCharts,
                 '/charts/artists',
                 '/charts/artists/<string:period>',
                 '/charts/artists/<string:period>/<int:year>',
                 '/charts/artists/<string:period>/<int:year>/<int:month>')
api.add_resource(DJArtistCharts, '/charts/dj/<int:dj_id>/artists')
api.add_resource(TrackCharts,
                 '/charts/tracks',
                 '/charts/tracks/<string:period>',
                 '/charts/tracks/<string:period>/<int:year>',
                 '/charts/tracks/<string:period>/<int:year>/<int:month>')
api.add_resource(DJTrackCharts, '/charts/dj/<int:dj_id>/tracks')
api.add_resource(DJSpinCharts, '/charts/dj/spins')
api.add_resource(DJVinylSpinCharts, '/charts/dj/vinyl_spins')
api.add_resource(NowPlaying, '/now_playing')
api.add_resource(Last15Tracks, '/playlists/last15')
api.add_resource(LatestTrack, '/playlists/latest_track')
api.add_resource(PlaylistsByDay,
                 '/playlists/date/<int:year>/<int:month>/<int:day>')
api.add_resource(PlaylistDJs, '/playlists/dj')
api.add_resource(PlaylistAllDJs, '/playlists/dj/all')
api.add_resource(PlaylistsByDJ, '/playlists/dj/<int:dj_id>')
api.add_resource(Playlist, '/playlists/set/<int:set_id>')
api.add_resource(PlaylistTrack, '/playlists/track/<int:track_id>')


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp
