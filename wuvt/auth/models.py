from wuvt import app
from wuvt import db
from flask_login import UserMixin
from passlib.hash import django_pbkdf2_sha256


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
    role = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, user_id, role):
        self.user_id = user_id
        self.role = role


class GroupRole(db.Model):
    __tablename__ = "group_role"
    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.Unicode(255), nullable=False)
    role = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, group, role):
        self.group = group
        self.role = role
