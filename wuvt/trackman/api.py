import dateutil.parser
from flask import current_app, json, make_response, request, session
from flask_restful import abort, Api, Resource
from .. import csrf, db, redis_conn
from ..view_utils import ajax_only, local_only
from . import api_bp, models
from .forms import TrackAddForm, AutomationTrackLogForm, TrackLogForm, \
    TrackLogEditForm, AirLogForm, AirLogEditForm
from .lib import disable_automation, fixup_current_track, log_track, \
    logout_all_except, find_or_add_track
from .view_utils import dj_interact, require_dj_session


class TrackmanResource(Resource):
    decorators = [csrf.exempt]
    method_decorators = [local_only, ajax_only, dj_interact,
                         require_dj_session]


class TrackmanPublicResource(TrackmanResource):
    method_decorators = [local_only, ajax_only, dj_interact]


class AutomationLog(TrackmanPublicResource):
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

        form = AutomationTrackLogForm(meta={'csrf': False})

        if form.password.data != current_app.config['AUTOMATION_PASSWORD']:
            abort(401, success=False, message="Invalid automation password")

        automation = redis_conn.get('automation_enabled') == "true"
        if not automation:
            return {
                'success': False,
                'error': "Automation not enabled",
            }

        title = form.title.data
        if len(title) <= 0:
            abort(400, success=False, message="Title must be provided")

        artist = form.artist.data
        if len(artist) <= 0:
            abort(400, success=False, message="Artist must be provided")

        album = form.album.data
        if len(album) <= 0:
            album = u"Not Available"

        if artist.lower() in ("wuvt", "pro", "soo", "psa", "lnr", "ua"):
            # TODO: implement airlog logging
            return {
                'success': False,
                'message': "AirLog logging not yet implemented",
            }

        label = form.label.data
        if len(label) > 0:
            track = find_or_add_track(models.Track(
                title,
                artist,
                album,
                label))
        else:
            # Handle automation not providing a label
            label = u"Not Available"
            tracks = models.Track.query.filter(
                db.func.lower(models.Track.title) == db.func.lower(title),
                db.func.lower(models.Track.artist) == db.func.lower(artist),
                db.func.lower(models.Track.album) == db.func.lower(album))
            if tracks.count() == 0:
                track = models.Track(title, artist, album, label)
                db.session.add(track)
                db.session.commit()
            else:
                notauto = tracks.filter(models.Track.label != u"Not Available")
                if notauto.count() == 0:
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


class DJ(TrackmanResource):
    def post(self, dj_id):
        """
        Make changes to a DJ
        ---
        operationId: editDj
        tags:
        - trackman
        - dj
        parameters:
        - in: path
          name: dj_id
          type: integer
          required: true
          description: The ID of an existing DJ
        - in: form
          name: visible
          type: boolean
          description: Whether or not a DJ is visible in the list
        """

        if dj_id == 1:
            abort(403, success=False, message="This DJ cannot be modified")

        dj = models.DJ.query.get_or_404(dj_id)

        if 'visible' in request.form:
            visible = request.form['active'] == "true"
            if visible is True:
                dj.visible = True
            else:
                abort(403, success=False,
                      message="DJs cannot be hidden through this API.")

        db.session.commit()

        return {
            'success': True,
            'dj': dj.serialize(),
        }


class DJSet(TrackmanPublicResource):
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
            abort(404, success=False, message="DJSet not found")

        if djset.dtend is not None:
            abort(401, success=False, message="Session expired, please login again")

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


class DJSetList(TrackmanPublicResource):
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

        session['dj_id'] = dj.id
        session['djset_id'] = djset.id

        return {
            'success': True,
            'dj_id': dj.id,
            'djset_id': djset.id,
        }, 201


class Track(TrackmanPublicResource):
    def get(self, track_id):
        """
        Get information about a Track
        ---
        operationId: getTrackById
        tags:
        - trackman
        - djset
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
        track = models.Track.query.get(track_id)
        if not track:
            abort(404, success=False, message="Track not found")

        return {
            'success': True,
            'track': track.serialize(),
        }


class TrackReport(TrackmanResource):
    def post(self, track_id):
        """
        Report a Track
        ---
        operationId: getTrackById
        tags:
        - trackman
        - djset
        parameters:
        - in: path
          name: track_id
          type: integer
          required: true
          description: The ID of an existing Track
        - in: form
          name: reason
          type: string
          required: true
          description: The reason for reporting the track
        - in: form
          name: dj_id
          type: integer
          required: true
          description: The DJ to associate with the report
        responses:
          201:
            description: Track report created
          404:
            description: Track not found
        """
        track = models.Track.query.get(track_id)
        if not track:
            abort(404, success=False, message="Track not found")

        reason = request.form['reason'].strip()
        if len(reason) <= 0:
            abort(400, success=False, message="A reason must be provided")

        dj_id = session['dj_id']

        report = models.TrackReport(dj_id, track_id, reason)
        db.session.add(report)
        db.session.commit()

        return {
            'success': True,
        }


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
            abort(400, success=False, message="No search entires")

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


class TrackAutoComplete(TrackmanResource):
    def get(self):
        """
        Search the track database for a particular field
        ---
        operationId: autocompleteTracks
        tags:
        - trackman
        - track
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
        - in: query
          name: field
          type: string
          required: true
          description: The field to autocomplete
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
          400:
            description: Bad request
        """

        field = request.args['field']
        if field == 'artist':
            base_query = models.Track.query.\
                with_entities(models.Track.artist).\
                group_by(models.Track.artist)
        elif field == 'title':
            base_query = models.Track.query.\
                with_entities(models.Track.title).\
                group_by(models.Track.title)
        elif field == 'album':
            base_query = models.Track.query.\
                with_entities(models.Track.album).\
                group_by(models.Track.album)
        elif field == 'label':
            base_query = models.Track.query.\
                with_entities(models.Track.label).\
                group_by(models.Track.label)
        else:
            abort(400, success=False)

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
            abort(400, success=False, message="No search entires")

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
            results = [t[0] for t in tracks]
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

        form = TrackAddForm(meta={'csrf': False})
        if form.validate():
            track = find_or_add_track(models.Track(
                form.title.data,
                form.artist.data,
                form.album.data,
                form.label.data))

            return {
                'success': True,
                'track_id': track.id,
            }, 201
        else:
            abort(400, success=False, errors=form.errors,
                  message="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")


class TrackLog(TrackmanResource):
    def _load(self, tracklog_id):
        tracklog = models.TrackLog.query.get(tracklog_id)
        if not tracklog:
            abort(404, success=False, message="TrackLog not found")
        if tracklog.djset.dtend is not None:
            abort(401, success=False, message="Session expired, please login again")

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

        form = TrackLogEditForm(meta={'csrf': False})
        artist = form.artist.data
        title = form.title.data
        album = form.album.data
        label = form.label.data

        # First check if the artist et. al. are the same
        if artist != tracklog.track.artist or title != tracklog.track.title or \
                album != tracklog.track.album or label != tracklog.track.label:
            # If not, this means we try to create a new track
            if form.validate():
                track = find_or_add_track(models.Track(
                    title,
                    artist,
                    album,
                    label))
                tracklog.track_id = track.id
            else:
                abort(400, success=False, errors=form.errors,
                      message="The track information you entered did not validate. Common reasons for this include missing or improperly entered information, especially the label. Please try again. If you continue to get this message after several attempts, and you're sure the information is correct, please contact the IT staff for help.")

        # Update played time
        played = form.played.data
        if len(played) > 0:
            tracklog.played = dateutil.parser.parse(played)

        # Update boolean information
        tracklog.request = form.request.data
        tracklog.new = form.new.data
        tracklog.vinyl = form.vinyl.data

        # Update rotation
        rotation = models.Rotation.query.get(form.rotation.data)
        if not rotation:
            abort(400, success=False,
                  message="Rotation specified by rotation_id does not exist")
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

        form = TrackLogForm(meta={'csrf': False})
        track_id = form.track_id.data
        djset_id = form.djset_id.data

        if djset_id != session['djset_id']:
            abort(403, success=False)

        rotation = form.rotation.data
        if rotation is not None:
            rotation = models.Rotation.query.get(int(rotation))

        # check to be sure the track and DJSet exist
        track = models.Track.query.get(track_id)
        djset = models.DJSet.query.get(djset_id)
        if not track or not djset:
            abort(400, success=False,
                  message="Track and/or DJSet does not exist")

        if djset.dtend is not None:
            abort(401, success=False,
                  message="Session expired, please login again")

        tracklog = log_track(track_id, djset_id,
                             request=form.request.data,
                             vinyl=form.vinyl.data,
                             new=form.new.data,
                             rotation=rotation)

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
            abort(400, success=False,
                  message="No autologout field given in POST")

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
            abort(404, success=False, message="AirLog entry not found")

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
            abort(404, success=False, message="AirLog entry not found")

        form = AirLogEditForm(meta={'csrf': False})

        # Update aired time
        airtime = form.airtime.data
        if len(airtime) > 0:
            airlog.airtime = dateutil.parser.parse(airtime)

        logtype = form.logtype.data
        if logtype > 0:
            airlog.logtype = logtype

        logid = form.logid.data
        if logid > 0:
            airlog.logid = logid

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

        form = AirLogForm(meta={'csrf': False})

        djset_id = form.djset_id.data
        if djset_id != session['djset_id']:
            abort(403, success=False)

        airlog = models.AirLog(djset_id, form.logtype.data, form.logid.data)
        db.session.add(airlog)
        db.session.commit()

        return {
            'success': True,
            'airlog_id': airlog.id,
        }, 201


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
