import datetime

from wuvt import db


class DJ(db.Model):
    __tablename__ = "dj"
    id = db.Column(db.Integer, primary_key=True)
    airname = db.Column(db.Unicode)
    name = db.Column(db.Unicode)
    phone = db.Column(db.String(10))
    email = db.Column(db.String)
    genres = db.Column(db.String)
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    visible = db.Column(db.Boolean, default=True)

    def __init__(self, airname, name):
        self.airname = airname
        self.name = name


class Track(db.Model):
    __tablename__ = "track"
    # FIXME: sqlite uses 64-bit integers and does not support autoincrement on
    # BigInteger, but postgres uses only 32-bit integers and needs this to be
    # a bigint
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('dj', lazy='dynamic'))
    # TODO: enBin?
    title = db.Column(db.String)
    artist = db.Column(db.String)
    album = db.Column(db.String)
    label = db.Column(db.String)
    request = db.Column(db.Boolean, default=False)
    vinyl = db.Column(db.Boolean, default=False)
    listeners = db.Column(db.Integer)

    def __init__(self, dj_id, title, artist, album, label, request=False,
            vinyl=False, listeners=None):
        self.dj_id = dj_id
        self.title = title
        self.artist = artist
        self.album = album
        self.label = label
        self.request = request
        self.vinyl = vinyl
        self.listeners = listeners

    def serialize(self):
        return {
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'label': self.label,
            'request': self.request,
            'vinyl': self.vinyl,
            'datetime': str(self.datetime),
            'dj': self.dj.airname,
        }
