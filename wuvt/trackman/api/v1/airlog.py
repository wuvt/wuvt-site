import dateutil.parser
from flask import session
from flask_restful import abort
from wuvt import db
from wuvt.trackman import models, playlists_cache
from wuvt.trackman.forms import AirLogForm, AirLogEditForm
from .base import TrackmanOnAirResource


class AirLog(TrackmanOnAirResource):
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
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        playlists_cache.clear()
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

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        playlists_cache.clear()
        return {'success': True}


class AirLogList(TrackmanOnAirResource):
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
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        playlists_cache.clear()
        return {
            'success': True,
            'airlog_id': airlog.id,
        }, 201
