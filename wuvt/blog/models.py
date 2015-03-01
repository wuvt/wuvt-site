import datetime

from wuvt import db
from markdown import markdown


class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False)

    def __init__(self, name, slug):
        self.name = name
        self.slug = slug


class Article(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(255), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=db.backref('category',
        lazy='dynamic'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('author',
        lazy='dynamic'))
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    summary = db.Column(db.UnicodeText(length=2**31))
    content = db.Column(db.UnicodeText(length=2**31))
    html_summary = db.Column(db.UnicodeText(length=2**31))
    html_content = db.Column(db.UnicodeText(length=2**31))
    published = db.Column(db.Boolean, default=False, nullable=False)
    front_page = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, title, slug, category_id, author_id, summary,
            content=None, published=False):
        self.title = title
        self.slug = slug
        self.category_id = category_id
        self.author_id = author_id
        self.summary = summary
        self.content = content
        self.published = published

    def render_html(self):
        if self.summary is not None:
            self.html_summary = markdown(self.summary)
        if self.content is not None:
            self.html_content = markdown(self.content)
