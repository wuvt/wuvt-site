from wuvt import db
from wuvt.trackman import models
from .base import TrackmanResource


class RotationList(TrackmanResource):
    def get(self):
        """
        Get a list of rotations
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
        rotations = {}
        for i in models.Rotation.query.order_by(models.Rotation.id).all():
            rotations[i.id] = i.rotation

        return {
            'rotations': rotations,
        }
