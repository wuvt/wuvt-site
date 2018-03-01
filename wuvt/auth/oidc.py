from flask import url_for
import flask_oidc


class OpenIDConnect(object):
    def __init__(self, app=None, db=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        flask_oidc.logger = app.logger

        with app.app_context():
            app.config.setdefault('OIDC_SCOPES',
                                  ['openid', 'profile', 'email'])
            app.config.update({
                'OIDC_RESOURCE_SERVER_ONLY': True,
                'OIDC_RESOURCE_CHECK_AUD': True,
            })

            app.before_request(self._before_request)

        self.oidc = flask_oidc.OpenIDConnect(app)

    def _before_request(self):
        if self.app.config['OVERWRITE_REDIRECT_URI'] is False:
            self.app.config['OVERWRITE_REDIRECT_URI'] = url_for(
                'auth.oidc_callback', _external=True)
