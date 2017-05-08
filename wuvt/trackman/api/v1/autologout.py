from flask import current_app, request
from flask_restful import abort
from wuvt import redis_conn
from .base import TrackmanOnAirResource


class AutologoutControl(TrackmanOnAirResource):
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
