from flask import json, make_response
from flask_restful import Api

from wuvt.trackman import api_bp
from .v1.airlog import AirLog, AirLogList
from .v1.autologout import AutologoutControl
from .v1.automation import AutomationLog
from .v1.dj import DJ
from .v1.djset import DJSet, DJSetList
from .v1.track import Track, TrackReport, TrackSearch, TrackAutoComplete, \
    TrackList
from .v1.tracklog import TrackLog, TrackLogList


api = Api(api_bp)
api.add_resource(AutomationLog, '/automation/log')
api.add_resource(DJ, '/dj/<int:djset_id>')
api.add_resource(DJSet, '/djset/<int:djset_id>')
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


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp
