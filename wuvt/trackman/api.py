import dateutil.parser
from flask import current_app, json, make_response, request, session
from flask_restful import abort, Api, Resource
from .. import csrf, db, redis_conn
from ..view_utils import ajax_only, local_only
from . import api_bp, models
from .lib import disable_automation, fixup_current_track, log_track, \
    logout_all_except
from .view_utils import dj_interact


class TrackmanResource(Resource):
    decorators = [csrf.exempt]
    method_decorators = [local_only, ajax_only, dj_interact]


class AutomationLog(TrackmanResource):
    method_decorators = [local_only]

    def post(self):
        """
        Log a track played by automation
        ---
        operationId: logAutomationTrack
        tags:
        - trackman
        - tracklog
        - automation
        parameters:
        - in: form
          name: artist
          type: string
          required: true
          description: Artist name
        - in: form
          name: title
          type: string
          required: true
          description: Track title
        - in: form
          name: album
          type: string
          description: Album title
        - in: form
          name: label
          type: string
          description: Record label
        responses:
          200:
            description: Track accepted, but not necessarily logged
            schema:
              type: object
              properties:
                success:
                  type: boolean
          201:
            description: Track logged
            schema:
              type: object
              properties:
                success:
                  type: boolean
          400:
            description: Bad request
          401:
            description: Invalid automation password
        """

        if 'password' not in request.form or \
                request.form['password'] != \
                current_app.config['AUTOMATION_PASSWORD']:
            abort(401, message="Invalid automation password")

        automation = redis_conn.get('automation_enabled') == "true"
        if not automation:
            return {
                'success': False,
                'error': "Automation not enabled",
            }

        if 'title' in request.form and len(request.form['title']) > 0:
            title = request.form['title'].strip()
        else:
            abort(400, message="Title must be provided")

        if 'artist' in request.form and len(request.form['artist']) > 0:
            artist = request.form['artist'].strip()
        else:
            abort(400, message="Artist must be provided")

        if 'album' in request.form and len(request.form['album']) > 0:
            album = request.form['album'].strip()
        else:
            album = u"Not Available"

        if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr", "ua"):
            # TODO: implement airlog logging
            return {
                'success': False,
                'message': "AirLog logging not yet implemented",
            }

        if 'label' in request.form and len(request.form['label']) > 0:
            label = request.form['label'].strip()
            tracks = models.Track.query.filter(
                models.Track.title == title,
                models.Track.artist == artist,
                models.Track.album == album,
                models.Track.label == label)
            if len(tracks.all()) == 0:
                track = models.Track(title, artist, album, label)
                db.session.add(track)
                db.session.commit()
            else:
                track = tracks.first()

        else:
            # Handle automation not providing a label
            label = u"Not Available"
            tracks = models.Track.query.filter(
                models.Track.title == title,
                models.Track.artist == artist,
                models.Track.album == album)
            if len(tracks.all()) == 0:
                track = models.Track(title, artist, album, label)
                db.session.add(track)
                db.session.commit()
            else:
                notauto = tracks.filter(models.Track.label != u"Not Available")
                if len(notauto.all()) == 0:
                    # The only option is "not available label"
                    track = tracks.first()
                else:
                    track = notauto.first()

        djset_id = redis_conn.get('automation_set')
        if djset_id != None:
            djset_id = int(djset_id)
            log_track(track.id, djset_id)
            return {'success': True}, 201
        else:
            return {'success': False}


class DJSet(TrackmanResource):
    def get(self, djset_id):
        """
        Get information about a DJSet
        ---
        operationId: getDjsetById
        tags:
        - trackman
        - djset
        parameters:
        - in: path
          name: djset_id
          type: integer
          required: true
          description: The ID of an existing DJSet
        responses:
          401:
            description: Session expired
          404:
            description: DJSet not found
        """

        djset = models.DJSet.query.get(djset_id)
        if not djset:
            abort(404, message="DJSet not found")

        if djset.dtend is not None:
            abort(401, message="Session expired, please login again")

        if request.args.get('merged', False):
            logs = [i.full_serialize() for i in djset.tracks]
            logs.extend([i.serialize() for i in djset.airlog])
            logs = sorted(logs, key=lambda log: log.get('airtime', False) if log.get('airtime', False) else log.get('played', False), reverse=False)

            return {
                'success': True,
                'logs': logs,
            }
        else:
            return {
                'success': True,
                'tracklog': [i.serialize() for i in djset.tracks],
                'airlog': [i.serialize() for i in djset.airlog],
            }


class DJSetList(TrackmanResource):
    def post(self):
        """
        Create a new DJSet
        ---
        operation: createDjset
        tags:
        - trackman
        - djset
        parameters:
        - in: form
          name: dj
          type: integer
          required: true
          description: The ID of an existing DJ
        responses:
          201:
            description: DJSet created
            schema:
              type: object
              properties:
                success:
                  type: boolean
                djset_id:
                  type: integer
                  description: The ID of the new DJSet
        """
        disable_automation()

        dj = models.DJ.query.get(request.form['dj'])

        current_app.logger.warning(
            "Trackman: {airname} logged in from {ip} using {ua}".format(
                airname=dj.airname,
                ip=request.remote_addr,
                ua=request.user_agent))

        # close open DJSets, and see if we have one we can use
        djset = logout_all_except(dj.id)
        if djset is None:
            djset = DJSet(dj.id)
            db.session.add(djset)
            db.session.commit()

        session['djset_id'] = djset.id

        return {
            'success': True,
            'djset_id': djset.id,
        }, 201


class TrackSearch(TrackmanResource):
    def get(self):
        """
        Search the track database for a particular track
        ---
        operationId: searchTracks
        tags:
        - trackman
        - track
        definitions:
        - schema:
            id: Track
            properties:
              id:
                type: integer
                description: The ID of the track
              title:
                type: string
                description: Track title
              artist:
                type: string
                description: Artist name
              album:
                type: string
                description: Album name
              label:
                type: string
                description: Record label
              added:
                type: string
                description: Date added
        parameters:
        - in: query
          name: artist
          type: string
          description: Partial artist name
        - in: query
          name: title
          type: string
          description: Partial track title
        - in: query
          name: album
          type: string
          description: Partial album title
        - in: query
          name: label
          type: string
          description: Partial record label
        responses:
          200:
            description: Search results
            schema:
              type: object
              properties:
                success:
                  type: boolean
                results:
                  type: array
                  $ref: '#/definitions/Track'
          400:
            description: Bad request
        """

        base_query = models.Track.query.outerjoin(models.TrackLog).\
            order_by(models.Track.plays)

        # To verify some data was searched for
        somesearch = False

        tracks = base_query

        # Do case-insensitive exact matching first

        artist = request.args.get('artist', '').strip()
        if len(artist) > 0:
            somesearch = True
            tracks = tracks.filter(
                db.func.lower(models.Track.artist) == db.func.lower(artist))

        title = request.args.get('title', '').strip()
        if len(title) > 0:
            somesearch = True
            tracks = tracks.filter(
                db.func.lower(models.Track.title) == db.func.lower(title))

        album = request.args.get('album', '').strip()
        if len(album) > 0:
            somesearch = True
            tracks = tracks.filter(
                db.func.lower(models.Track.album) == db.func.lower(album))

        label = request.args.get('label', '').strip()
        if len(label) > 0:
            somesearch = True
            tracks = tracks.filter(
                db.func.lower(models.Track.label) == db.func.lower(label))

        # This means there was a bad search, stop searching
        if somesearch is False:
            abort(400, message="No search entires")

        # Check if results

        tracks = tracks.limit(8).all()
        if len(tracks) == 0:
            tracks = base_query

            # if there are too few results, append some similar results
            artist = request.args.get('artist', '').strip()
            if len(artist) > 0:
                somesearch = True
                tracks = tracks.filter(
                    models.Track.artist.ilike(''.join(['%', artist, '%'])))

            title = request.args.get('title', '').strip()
            if len(title) > 0:
                somesearch = True
                tracks = tracks.filter(
                    models.Track.title.ilike(''.join(['%', title, '%'])))

            album = request.args.get('album', '').strip()
            if len(album) > 0:
                somesearch = True
                tracks = tracks.filter(
                    models.Track.album.ilike(''.join(['%', album, '%'])))

            label = request.args.get('label', '').strip()
            if len(label) > 0:
                somesearch = True
                tracks = tracks.filter(
                    models.Track.label.ilike(''.join(['%', label, '%'])))

            tracks = tracks.limit(8).all()

        if len(tracks) > 0:
            results = [t.serialize() for t in tracks]
        else:
            results = []

        return {
            'success': True,
            'results': results,
        }


class TrackList(TrackmanResource):
    def post(self):
        """
        Create a new track in the database
        ---
        operationId: createTrack
        tags:
        - trackman
        - track
        parameters:
        - in: form
          name: artist
          type: string
          required: true
          description: Artist name
        - in: form
          name: title
          type: string
          required: true
          description: Track title
        - in: form
          name: album
          type: string
          required: true
          description: Album title
        - in: form
          name: label
          type: string
          required: true
          description: Record label
        responses:
          201:
            description: Track created
            schema:
              type: object
              properties:
                success:
                  type: boolean
                track_id:
                  type: integer
                  description: The ID of the track
          400:
            description: Bad request
        """

        title = request.form['title'].strip()
        album = request.form['album'].strip()
        artist = request.form['artist'].strip()
        label = request.form['label'].strip()

        track = models.Track(title, artist, album, label)
        if not track.validate():
            abort(400, message="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")

        db.session.add(track)
        db.session.commit()

        return {
            'success': True,
            'track_id': track.id,
        }, 201


class TrackLog(TrackmanResource):
    def _load(self, tracklog_id):
        tracklog = models.TrackLog.query.get(tracklog_id)
        if not tracklog:
            abort(404, message="TrackLog not found")
        if tracklog.djset.dtend is not None:
            abort(401, message="Session expired, please login again")

        return tracklog

    def _get_current_id(self):
        current_tracklog = models.TrackLog.query.with_entities(
            models.TrackLog.id).order_by(db.desc(models.TrackLog.id)).first()
        if current_tracklog is not None:
            return current_tracklog[0]
        else:
            return None

    def delete(self, tracklog_id):
        """
        Delete an existing logged track entry
        ---
        operationId: deleteTrackLog
        tags:
        - trackman
        - tracklog
        parameters:
        - in: path
          name: tracklog_id
          type: integer
          required: true
          description: Logged track ID
        responses:
          200:
            description: Logged track entry deleted
            schema:
              type: object
              properties:
                success:
                  type: boolean
          400:
            description: Bad request
          401:
            description: Session expired
          404:
            description: TrackLog not found
        """

        tracklog = self._load(tracklog_id)
        current_tracklog_id = self._get_current_id()
        db.session.delete(tracklog)
        db.session.commit()

        if tracklog_id == current_tracklog_id:
            fixup_current_track("track_delete")

        return {'success': True}

    def post(self, tracklog_id):
        """
        Modify an existing logged track entry
        ---
        operationId: modifyTrackLog
        tags:
        - trackman
        - tracklog
        parameters:
        - in: path
          name: tracklog_id
          type: integer
          required: true
          description: Logged track ID
        - in: form
          name: artist
          type: string
          required: true
          description: Artist name
        - in: form
          name: title
          type: string
          required: true
          description: Track title
        - in: form
          name: album
          type: string
          required: true
          description: Album title
        - in: form
          name: label
          type: string
          required: true
          description: Record label
        responses:
          200:
            description: Logged track entry modified
          400:
            description: Bad request
          401:
            description: Session expired
          404:
            description: TrackLog not found
        """

        tracklog = self._load(tracklog_id)
        current_tracklog_id = self._get_current_id()

        # Do data sanitation!
        artist = request.form.get("artist", "").strip()
        title = request.form.get("title", "").strip()
        album = request.form.get("album", "").strip()
        label = request.form.get("label", "").strip()
        is_request = request.form.get('request', 'false') != 'false'
        vinyl = request.form.get('vinyl', 'false') != 'false'
        new = request.form.get('new', 'false') != 'false'
        rotation = request.form.get("rotation", 1)

        # Validate
        if len(artist) <= 0 or len(title) <= 0 or len(album) <= 0 or \
                len(label) <= 0:
            abort(400, message="Must fill out artist, title, album, and label field")

        # First check if the artist et. al. are the same
        if artist != tracklog.track.artist or title != tracklog.track.title or \
                album != tracklog.track.album or label != tracklog.track.label:
            # This means we try to create a new track
            track = models.Track(title, artist, album, label)
            if not track.validate():
                abort(400, message="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")

            db.session.add(track)
            db.session.commit()
            tracklog.track_id = track.id

        # Update played time
        played = request.form.get('played', None)
        if played is not None:
            tracklog.played = dateutil.parser.parse(played)
        # Update boolean information
        tracklog.request = is_request
        tracklog.new = new
        tracklog.vinyl = vinyl

        # Update rotation
        rotation = models.Rotation.query.get(rotation)
        if not rotation:
            abort(400, "Rotation specified by rotation_id does not exist")
        tracklog.rotation_id = rotation.id

        db.session.commit()

        if tracklog_id == current_tracklog_id:
            fixup_current_track()

        return {'success': True}


class TrackLogList(TrackmanResource):
    def post(self):
        """
        Log a track that already exists in the database
        ---
        operationId: createTrackLog
        tags:
        - trackman
        - tracklog
        - track
        parameters:
        - in: form
          name: track_id
          type: integer
          required: true
          description: The ID of an existing track
        - in: form
          name: djset_id
          type: integer
          required: true
          description: The ID of an existing DJSet
        responses:
          201:
            description: Track logged
            schema:
              type: object
              properties:
                success:
                  type: boolean
                tracklog_id:
                  type: integer
                  description: The ID of the logged track
          400:
            description: Bad request
          401:
            description: Session expired
        """

        track_id = int(request.form['track_id'])
        djset_id = int(request.form['djset_id'])

        is_request = request.form.get('request', 'false') != 'false'
        vinyl = request.form.get('vinyl', 'false') != 'false'
        new = request.form.get('new', 'false') != 'false'

        rotation = request.form.get('rotation', None)
        if rotation is not None:
            rotation = models.Rotation.query.get(int(rotation))

        # check to be sure the track and DJSet exist
        track = models.Track.query.get(track_id)
        djset = models.DJSet.query.get(djset_id)
        if not track or not djset:
            abort(400, message="Track and/or DJSet does not exist")

        if djset.dtend is not None:
            abort(401, message="Session expired, please login again")

        tracklog = log_track(track_id, djset_id, request=is_request,
                             vinyl=vinyl, new=new, rotation=rotation)

        return {
            'success': True,
            'tracklog_id': tracklog.id,
        }, 201


class AutologoutControl(TrackmanResource):
    def get(self):
        """
        Get the current autologout status
        ---
        operationId: getAutologout
        tags:
        - trackman
        - autologout
        responses:
          200:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                autologout:
                  type: boolean
        """

        dj_timeout = redis_conn.get('dj_timeout')
        return {
            'success': True,
            'autologout': dj_timeout is None,
        }

    def post(self):
        """
        Enable/disable the autologout functionality
        ---
        operationId: setAutologout
        tags:
        - trackman
        - autologout
        parameters:
        - in: form
          name: autologout
          schema:
            parameters:
              autologout:
                type: string
                description: Use a value of "enable" to enable, otherwise disable
        responses:
          200:
            description: Autologout preferences updated
            schema:
              type: object
              properties:
                success:
                  type: boolean
                autologout:
                  type: boolean
          400:
            description: Bad request
        """

        if 'autologout' not in request.form:
            abort(400, message="No autologout field given in POST")

        if request.form['autologout'] == 'enable':
            redis_conn.delete('dj_timeout')

            return {
                'success': True,
                'autologout': True,
            }
        else:
            redis_conn.set('dj_timeout',
                           current_app.config['EXTENDED_DJ_TIMEOUT'])

            return {
                'success': True,
                'autologout': False,
            }


class AirLog(TrackmanResource):
    def delete(self, airlog_id):
        """
        Delete an existing AirLog entry
        ---
        operationId: deleteAirLog
        tags:
        - trackman
        - airlog
        parameters:
        - in: path
          name: airlog_id
          type: integer
          required: true
          description: AirLog ID
        responses:
          200:
            description: AirLog entry deleted
            schema:
              type: object
              properties:
                success:
                  type: boolean
          404:
            description: AirLog entry not found
        """

        airlog = models.AirLog.query.get(airlog_id)
        if not airlog:
            abort(404, message="AirLog entry not found")

        db.session.delete(airlog)
        db.session.commit()

        return {'success': True}

    def post(self, airlog_id):
        """
        Modify an existing logged AirLog entry
        ---
        operationId: modifyAirLog
        tags:
        - trackman
        - airlog
        parameters:
        - in: path
          name: airlog_id
          type: integer
          required: true
          description: AirLog ID
        - in: form
          name: airtime
          type: string
          description: Air time
        - in: form
          name: logtype
          type: integer
          description: Log type
        - in: form
          name: logid
          type: integer
          description: Log ID
        responses:
          200:
            description: AirLog entry modified
            schema:
              type: object
              properties:
                success:
                  type: boolean
          400:
            description: Bad request
          404:
            description: AirLog entry not found
        """

        airlog = models.AirLog.query.get(airlog_id)
        if not airlog:
            abort(404, message="AirLog entry not found")

        # Update aired time
        airtime = request.form.get('airtime', None)
        if airtime is not None:
            airlog.airtime = dateutil.parser.parse(airtime)

        # Update integers
        logtype = request.form.get('logtype', None)
        if logtype is not None:
            airlog.request = bool(logtype)

        logid = request.form.get('logid', None)
        if logid is not None:
            airlog.request = bool(logid)

        db.session.commit()

        return {'success': True}


class AirLogList(TrackmanResource):
    def post(self):
        """
        Create a new AirLog entry
        ---
        operationId: createAirLog
        tags:
        - trackman
        - airlog
        parameters:
        - in: form
          name: djset_id
          type: integer
          required: true
          description: The ID of an existing DJSet
        - in: form
          name: logtype
          type: integer
          required: true
          description: Log type
        - in: form
          name: logid
          type: integer
          description: Log ID
        responses:
          201:
            description: AirLog entry created
            schema:
              type: object
              properties:
                success:
                  type: boolean
                airlog_id:
                  type: integer
                  description: The ID of the new AirLog entry
          400:
            description: Bad request
        """

        djset_id = int(request.form['djset_id'])
        logtype = int(request.form['logtype'])
        logid = int(request.form.get('logid', 0))

        airlog = models.AirLog(djset_id, logtype, logid=logid)
        db.session.add(airlog)
        db.session.commit()

        return {
            'success': True,
            'airlog_id': airlog.id,
        }, 201


api = Api(api_bp)
api.add_resource(AutomationLog, '/automation/log')
api.add_resource(DJSet, '/djset/<int:djset_id>')
api.add_resource(DJSetList, '/djset')
api.add_resource(TrackSearch, '/search')
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
