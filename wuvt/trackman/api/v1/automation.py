from flask import current_app
from flask_restful import abort
from wuvt import db, redis_conn
from wuvt.view_utils import local_only
from wuvt.trackman import models
from wuvt.trackman.forms import AutomationTrackLogForm
from wuvt.trackman.lib import log_track, find_or_add_track
from .base import TrackmanStudioResource


class AutomationLog(TrackmanStudioResource):
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
            album = "Not Available"

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
            label = "Not Available"
            tracks = models.Track.query.filter(
                db.func.lower(models.Track.title) == db.func.lower(title),
                db.func.lower(models.Track.artist) == db.func.lower(artist),
                db.func.lower(models.Track.album) == db.func.lower(album))
            if tracks.count() == 0:
                track = models.Track(title, artist, album, label)
                db.session.add(track)
                try:
                    db.session.commit()
                except:
                    db.session.rollback()
                    raise
            else:
                notauto = tracks.filter(models.Track.label != "Not Available")
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
