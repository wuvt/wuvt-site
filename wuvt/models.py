from wuvt import app
from wuvt import db
from flask_login import UserMixin
from passlib.hash import django_pbkdf2_sha256
from markdown import markdown

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


class Page(db.Model):
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False)
    menu = db.Column(db.Unicode(255))
    content = db.Column(db.UnicodeText(length=2**31), nullable=False)
    html = db.Column(db.UnicodeText(length=2**31))
    published = db.Column(db.Boolean, default=True, nullable=False)


    def __init__(self, name, slug, content, published, menu=None):
        self.name = name
        self.slug = slug
        self.content = content
        self.published = published
        self.menu = menu
        self.html = markdown(content)

    def update_content(self, content):
        self.content = content
        self.html = markdown(content)
