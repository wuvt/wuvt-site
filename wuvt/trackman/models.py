import datetime

from wuvt import db


class DJ(db.Model):
    __tablename__ = "dj"
    id = db.Column(db.Integer, primary_key=True)
    airname = db.Column(db.Unicode(255))
    name = db.Column(db.Unicode(255))
    phone = db.Column(db.Unicode(10))
    email = db.Column(db.Unicode(255))
    genres = db.Column(db.Unicode(255))
    time_added = db.Column(db.DateTime, default=datetime.datetime.now)
    visible = db.Column(db.Boolean, default=True)

    def __init__(self, airname, name, visible=True):
        self.airname = airname
        self.name = name
        self.visible = visible


class DJSet(db.Model):
    __tablename__ = "set"
    # FIXME: sqlite uses 64-bit integers and does not support autoincrement on
    # BigInteger, but postgres uses only 32-bit integers and needs this to be
    # a bigint
    id = db.Column(db.Integer, primary_key=True)
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('setdj', lazy='dynamic'))
    dtstart = db.Column(db.DateTime, default=datetime.datetime.now)
    dtend = db.Column(db.DateTime)

    def __init__(self, dj_id):
        self.dj_id = dj_id


class Track(db.Model):
    __tablename__ = "track"
    # FIXME: sqlite uses 64-bit integers and does not support autoincrement on
    # BigInteger, but postgres uses only 32-bit integers and needs this to be
    # a bigint
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('dj', lazy='dynamic'))
    djset_id = db.Column(db.Integer, db.ForeignKey('set.id'))
    # TODO: enBin?
    title = db.Column(db.Unicode(255))
    artist = db.Column(db.Unicode(255))
    album = db.Column(db.Unicode(255))
    label = db.Column(db.Unicode(255))
    request = db.Column(db.Boolean, default=False)
    vinyl = db.Column(db.Boolean, default=False)
    new = db.Column(db.Boolean, default=False)
    listeners = db.Column(db.Integer)

    def __init__(self, dj_id, djset_id, title, artist, album, label, request=False,
            vinyl=False, listeners=None):
        self.dj_id = dj_id
        self.djset_id = djset_id
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
            'djset': self.djset_id,
        }
