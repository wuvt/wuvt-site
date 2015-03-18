from flask import Blueprint
from flask.ext.login import UserMixin
import ldap

from wuvt import app
from wuvt import login_manager
from wuvt.models import User


bp = Blueprint('auth', __name__)


def build_dn(username):
    return app.config['LDAP_AUTH_DN'].format(ldap.dn.escape_dn_chars(username))


def build_group_query(groups):
    query = '(|'
    for group in groups:
        query += '(cn={})'.format(ldap.dn.escape_dn_chars(group))
    query += ')'
    return query


def ldap_group_test(client, groups, username):
    result = client.search_s(app.config['LDAP_BASE_DN'], ldap.SCOPE_SUBTREE,
                             build_group_query(groups))
    for r in result:
        if 'memberUid' in r[1]:
            for u in r[1]['memberUid']:
                if u == username:
                    return True

    return False


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


from wuvt.auth import views
