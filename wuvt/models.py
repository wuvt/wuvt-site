from wuvt import db
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import UserMixin


bcrypt = Bcrypt()


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, nullable=False)
    name = db.Column(db.Unicode, nullable=False)
    pw_hash = db.Column(db.String)
    email = db.Column(db.Unicode, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    def __init__(self, username, name):
        self.username = username
        self.name = name

    def set_password(self, password):
        self.pw_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.pw_hash, password)


class Page(db.Model):
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    slug = db.Column(db.Unicode, nullable=False)
    menu = db.Column(db.Unicode)
    content = db.Column(db.UnicodeText, nullable=False)

    def __init__(self, name, slug, content, menu=None):
        self.name = name
        self.slug = slug
        self.content = content
        self.menu = menu
