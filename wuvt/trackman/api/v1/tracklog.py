import dateutil.parser
from flask import session
from flask_restful import abort
from wuvt import db
from wuvt.trackman import models
from wuvt.trackman.forms import TrackLogForm, TrackLogEditForm
from wuvt.trackman.lib import fixup_current_track, log_track, find_or_add_track
from .base import TrackmanOnAirResource


class TrackLog(TrackmanOnAirResource):
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
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

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

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        if tracklog_id == current_tracklog_id:
            fixup_current_track()

        return {'success': True}


class TrackLogList(TrackmanOnAirResource):
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
