from flask import Blueprint
from flask.ext.login import UserMixin
import ldap

from wuvt import app
from wuvt import login_manager
from wuvt.models import User


bp = Blueprint('auth', __name__)


def build_dn(username):
    return app.config['LDAP_AUTH_DN'].format(ldap.dn.escape_dn_chars(username))


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


from wuvt.auth import views
