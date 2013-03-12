from wuvt import db
from flask.ext.login import UserMixin
from passlib.hash import django_pbkdf2_sha256


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(255), nullable=False)
    name = db.Column(db.Unicode(255), nullable=False)
    pw_hash = db.Column(db.String(255))
    email = db.Column(db.Unicode(255), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, username, name):
        self.username = username
        self.name = name

    def set_password(self, password):
        self.pw_hash = django_pbkdf2_sha256.encrypt(password)

    def check_password(self, password):
        return django_pbkdf2_sha256.verify(password, self.pw_hash)


class Page(db.Model):
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False)
    menu = db.Column(db.Unicode(255))
    content = db.Column(db.UnicodeText, nullable=False)

    def __init__(self, name, slug, content, menu=None):
        self.name = name
        self.slug = slug
        self.content = content
        self.menu = menu
