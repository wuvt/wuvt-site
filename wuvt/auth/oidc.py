from authlib.client import OAuthClient
from authlib.jose import jwt, jwk
from authlib.oidc.core import CodeIDToken, ImplicitIDToken, UserInfo
from flask import abort, current_app, json
from wuvt.auth.user import _find_or_create_user
from wuvt.auth.utils import login_user, get_user_roles
from wuvt.auth.view_utils import log_auth_success, log_auth_failure, \
        redirect_back


def create_oidc_backend(name, client_secrets_file=None, scopes=None):
    client_secrets = {}
    with open(client_secrets_file) as f:
        client_secrets = json.load(f)

    if scopes is None:
        scopes = ['openid', 'profile', 'email']

    config = {
        'client_id': client_secrets['web']['client_id'],
        'client_secret': client_secrets['web']['client_secret'],
        'access_token_url': client_secrets['web']['token_uri'],
        'authorize_url': client_secrets['web']['auth_uri'],
        'client_kwargs': {'scope': ' '.join(scopes)},
    }
    issuer_url = client_secrets['web']['issuer']

    class OpenIDConnectBackend(OAuthClient):
        OAUTH_TYPE = '2.0,oidc'
        OAUTH_NAME = name
        OAUTH_CONFIG = config

        def fetch_jwk_set(self, force=False):
            jwk_set = getattr(self, '_jwk_set', None)
            if jwk_set and not force:
                return jwk_set

            r = self.get(
                '{0}/.well-known/openid-configuration'.format(issuer_url),
                withhold_token=True)
            r.raise_for_status()
            openid_config = r.json()

            jr = self.get(openid_config['jwks_uri'], withhold_token=True)
            self._jwk_set = jr.json()
            return self._jwk_set

        def parse_openid(self, token, nonce=None):
            def load_key(header, payload):
                jwk_set = self.fetch_jwk_set()
                try:
                    return jwk.loads(jwk_set, header.get('kid'))
                except ValueError:
                    jwk_set = self.fetch_jwk_set(force=True)
                    return jwk.loads(jwk_set, header.get('kid'))

            claims_options = {
                'iss': {
                    'values': [issuer_url],
                },
            }
            claims_params = {
                'nonce': nonce,
                'client_id': self.client_id,
            }

            access_token = token.get('access_token')
            if access_token is not None:
                claims_params['access_token'] = access_token
                claims_cls = CodeIDToken
            else:
                claims_cls = ImplicitIDToken

            claims = jwt.decode(token['id_token'],
                                key=load_key,
                                claims_cls=claims_cls,
                                claims_options=claims_options,
                                claims_params=claims_params)
            claims.validate(leeway=120)
            return UserInfo(claims)

    return OpenIDConnectBackend


def handle_authorize(remote, token, user_info):
    if user_info is None:
        log_auth_failure("oidc", None)
        abort(401)

    user = _find_or_create_user(
        user_info['sub'], user_info['name'], user_info['email'])
    user_groups = user_info.get(
        current_app.config.get('OIDC_GROUPS_CLAIM', 'groups'))
    login_user(user, get_user_roles(user, user_groups))

    log_auth_success("oidc", user_info['sub'])

    return redirect_back('admin.index')
