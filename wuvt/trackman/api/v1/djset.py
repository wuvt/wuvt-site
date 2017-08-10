from flask import request, session
from flask_restful import abort
from wuvt import db, redis_conn
from wuvt.trackman import models
from wuvt.trackman.lib import disable_automation, logout_all_except
from .base import TrackmanResource


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


class DJSetList(TrackmanResource):
    def post(self):
        """
        Create a new DJSet
        ---
        operation: createDjset
        tags:
        - trackman
        - djset
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
        dj_id = session.get('dj_id', None)
        if dj_id is None:
            abort(403)

        dj = models.DJ.query.get(dj_id)
        if dj is None or dj.phone is None or dj.email is None:
            abort(403,
                  message="You must complete your DJ profile to continue.")

        disable_automation()

        # close open DJSets, and see if we have one we can use
        djset = logout_all_except(dj.id)
        if djset is None:
            djset = models.DJSet(dj.id)
            db.session.add(djset)
            try:
                db.session.commit()
            except:
                db.session.rollback()
                raise

        redis_conn.set('onair_djset_id', djset.id)
        session['djset_id'] = djset.id

        return {
            'success': True,
            'djset_id': djset.id,
        }, 201
