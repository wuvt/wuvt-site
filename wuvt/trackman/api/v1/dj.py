from flask import session
from flask_restful import abort
from wuvt import db
from wuvt.trackman import models
from wuvt.trackman.forms import DJEditForm
from .base import TrackmanResource


class DJ(TrackmanResource):
    def get(self, dj_id):
        """
        Get information about a DJ
        ---
        operationId: getDj
        tags:
        - trackman
        - dj
        parameters:
        - in: path
          name: dj_id
          type: integer
          required: true
          description: The ID of an existing DJ
        """
        dj = models.DJ.query.get_or_404(dj_id)
        return dj.serialize(include_private=True)

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
          required: false
          description: Whether or not a DJ is visible in the list
        - in: form
          name: email
          type: string
          required: false
          description: Email address of the DJ
        - in: form
          name: phone
          type: string
          required: false
          description: Phone number of the DJ
        """

        if dj_id == 1 or dj_id != session.get('dj_id', None):
            abort(403, success=False, message="This DJ cannot be modified")

        dj = models.DJ.query.get_or_404(dj_id)

        form = DJEditForm(meta={'csrf': False})
        if form.validate():
            if form.visible.data is True:
                dj.visible = True
            if dj.email is None and len(form.email.data) > 0:
                dj.email = form.email.data
            if dj.phone is None and len(form.phone.data) > 0:
                dj.phone = form.phone.data
        else:
            return {
                'success': False,
                'errors': form.errors,
            }, 403

        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise

        return {
            'success': True,
            'dj': dj.serialize(include_private=True),
        }
