import datetime
from wuvt import app
from wuvt import db
from passlib.hash import django_pbkdf2_sha256
from .mixins import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(255), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    pw_hash = db.Column(db.String(255))
    email = db.Column(db.Unicode(255), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, username, name, email):
        self.username = username
        self.name = name
        self.email = email

    def set_password(self, password):
        self.pw_hash = django_pbkdf2_sha256.encrypt(password)

    def check_password(self, password):
        if len(password) >= app.config['MIN_PASSWORD_LENGTH']:
            return django_pbkdf2_sha256.verify(password, self.pw_hash)
        else:
            return False


class UserRole(db.Model):
    __tablename__ = "user_role"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    role = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, user_id, role):
        self.user_id = user_id
        self.role = role


class UserSession(db.Model):
    __tablename__ = "user_session"
    id = db.Column(db.String(255), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    login_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    expires = db.Column(db.DateTime)
    user_agent = db.Column(db.Unicode(512))
    remote_addr = db.Column(db.Unicode(100))
    roles_list = db.Column(db.Unicode(1024))

    def __init__(self, session_id, user_id, expires, user_agent, remote_addr,
                 roles):
        self.id = session_id
        self.user_id = user_id
        self.expires = expires
        self.user_agent = user_agent
        self.remote_addr = remote_addr
        self.roles_list = ','.join(roles)

    @property
    def roles(self):
        return set(self.roles_list.split(','))


class GroupRole(db.Model):
    __tablename__ = "group_role"
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Unicode(255), nullable=False)
    role = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, group, role):
        self.group = group
        self.role = role
