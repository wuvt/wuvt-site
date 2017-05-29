import datetime
from wuvt import db
from markdown import markdown


class Page(db.Model):
    __tablename__ = "page"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    slug = db.Column(db.Unicode(255), nullable=False)
    menu = db.Column(db.Unicode(255))
    content = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'), nullable=False)
    html = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'))
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


class PageRevision(db.Model):
    __tablename__ = "page_revision"
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
    page = db.relationship('Page', backref=db.backref('page', lazy='dynamic'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('page_revision_author',
                                                        lazy='dynamic'))
    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    name = db.Column(db.Unicode(255), nullable=False)
    content = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'), nullable=False)
    html = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'))

    def __init__(self, page_id, author_id, name, content):
        self.page_id = page_id
        self.author_id = author_id
        self.name = name
        self.content = content
        self.html = markdown(content)
