from flask_restful import Resource
from wuvt import csrf
from wuvt.view_utils import ajax_only, local_only
from wuvt.trackman.view_utils import dj_interact, require_dj_session, \
    require_onair


class TrackmanResource(Resource):
    decorators = [csrf.exempt]
    method_decorators = [local_only, ajax_only, dj_interact,
                         require_dj_session]


class TrackmanOnAirResource(TrackmanResource):
    method_decorators = [local_only, ajax_only, dj_interact,
                         require_dj_session, require_onair]


class TrackmanStudioResource(TrackmanResource):
    method_decorators = [local_only, ajax_only, dj_interact]
