from wuvt import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, nullable=False)
    name = db.Column(db.Unicode, nullable=False)

    def __init__(self, username, name):
        self.username = username
        self.name = name


class Page(db.Model):
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode, nullable=False)
    slug = db.Column(db.Unicode, nullable=False)
    content = db.Column(db.UnicodeText, nullable=False)

    def __init__(self, name, slug, content):
        self.name = name
        self.slug = slug
        self.content = content

