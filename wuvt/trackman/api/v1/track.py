from flask import request, session
from flask_restful import abort
from wuvt import db
from wuvt.trackman import models
from wuvt.trackman.forms import TrackAddForm
from wuvt.trackman.lib import find_or_add_track
from .base import TrackmanResource, TrackmanStudioResource


class Track(TrackmanStudioResource):
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
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

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

        artist = request.args.get('artist', '').strip()
        if len(artist) > 0:
            somesearch = True
            tracks = tracks.filter(
                models.Track.artist.ilike(u'{0}%'.format(artist)))

        title = request.args.get('title', '').strip()
        if len(title) > 0:
            somesearch = True
            tracks = tracks.filter(
                models.Track.title.ilike(u'{0}%'.format(title)))

        album = request.args.get('album', '').strip()
        if len(album) > 0:
            somesearch = True
            tracks = tracks.filter(
                models.Track.album.ilike(u'{0}%'.format(album)))

        label = request.args.get('label', '').strip()
        if len(label) > 0:
            somesearch = True
            tracks = tracks.filter(
                models.Track.label.ilike(u'{0}%'.format(label)))

        # This means there was a bad search, stop searching
        if somesearch is False:
            abort(400, success=False, message="No search entires")

        # Check if results

        tracks = tracks.limit(25).all()
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
