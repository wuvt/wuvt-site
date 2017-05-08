from flask import request
from flask_restful import abort
from wuvt import db
from wuvt.trackman import models
from .base import TrackmanResource


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

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        return {
            'success': True,
            'dj': dj.serialize(),
        }
