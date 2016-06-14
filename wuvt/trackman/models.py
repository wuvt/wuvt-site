import datetime
from flask import current_app

from .. import db


class DJ(db.Model):
    __tablename__ = "dj"
    id = db.Column(db.Integer, primary_key=True)
    airname = db.Column(db.Unicode(255))
    name = db.Column(db.Unicode(255))
    phone = db.Column(db.Unicode(12))
    email = db.Column(db.Unicode(255))
    genres = db.Column(db.Unicode(255))
    time_added = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    visible = db.Column(db.Boolean, default=True)

    def __init__(self, airname, name, visible=True):
        self.airname = airname
        self.name = name
        self.visible = visible

    def serialize(self):
        return {
            'id': self.id,
            'airname': self.airname,
            'name': self.name,
            'visible': self.visible,
        }


class DJSet(db.Model):
    __tablename__ = "set"
    # may need to make this a BigInteger
    id = db.Column(db.Integer, primary_key=True)
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('sets', lazy='dynamic'))
    dtstart = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    dtend = db.Column(db.DateTime)

    def __init__(self, dj_id):
        self.dj_id = dj_id

    def serialize(self):
        return {
            'id': self.id,
            'dj_id': self.dj_id,
            'dj': self.dj.serialize(),
            'dtstart': self.dtstart,
            'dtend': self.dtend,
        }


class Rotation(db.Model):
    __tablename__ = "rotation"
    id = db.Column(db.Integer, primary_key=True)
    rotation = db.Column(db.Unicode(255))

    def __init__(self, rotation):
        self.rotation = rotation

    def serialize(self):
        return {
            'id': self.id,
            'rotation': self.rotation,
        }


class AirLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # 0 - Station ID
    # 1 - Statement of Ownership
    # 2 - PSA
    # 3 - Underwriting
    # 4 - Weather
    # 5 - Promo
    logtype = db.Column(db.Integer)
    # This is to be filled with the PSA/Promo ID
    logid = db.Column(db.Integer, nullable=True)
    airtime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    djset_id = db.Column(db.Integer, db.ForeignKey('set.id'))
    djset = db.relationship('DJSet', backref=db.backref('airlog', lazy='dynamic'))

    def __init__(self, djset_id, logtype, logid=None):
        self.djset_id = djset_id
        self.logtype = logtype
        self.logid = logid

    def serialize(self):
        return {
            'airlog_id': self.id,
            'airtime': self.airtime,
            'djset': self.djset_id,
            'logtype': self.logtype,
            'logid': self.logid,
        }


class TrackLog(db.Model):
    __tablename__ = "tracklog"
    id = db.Column(db.Integer, primary_key=True)
    # Relationships with the Track
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    track = db.relationship('Track', backref=db.backref('plays', lazy='dynamic'))
    # When the track was entered (does not count edits)
    played = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # Relationship with the playlist
    djset_id = db.Column(db.Integer, db.ForeignKey('set.id'))
    djset = db.relationship('DJSet', backref=db.backref('tracks', lazy='dynamic'))
    # DJ information, this is not kept updated right now and is _subject to removal_
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('tracks', lazy='dynamic'))
    # Information about the track
    request = db.Column(db.Boolean, default=False)
    vinyl = db.Column(db.Boolean, default=False)
    new = db.Column(db.Boolean, default=False)
    rotation_id = db.Column(db.Integer, db.ForeignKey('rotation.id'), nullable=True)
    rotation = db.relationship('Rotation', backref=db.backref('tracks', lazy='dynamic'))
    # This should be recorded at the start of the song probably
    listeners = db.Column(db.Integer)

    def __init__(self, track_id, djset_id, request=False, vinyl=False, new=False, rotation=None, listeners=0):
        self.track_id = track_id
        self.djset_id = djset_id

        if djset_id is not None:
            self.dj_id = DJSet.query.get(djset_id).dj_id
        else:
            # default to automation
            self.dj_id = 1

        self.request = request
        self.vinyl = vinyl
        self.new = new
        self.rotation = rotation
        self.listeners = listeners

    def serialize(self):
        return {
            'tracklog_id': self.id,
            'track_id': self.track_id,
            'played': self.played,
            'djset': self.djset_id,
            'dj_id': self.dj_id,
            'request': self.request,
            'vinyl': self.vinyl,
            'new': self.new,
            'listeners': self.listeners,
        }

    def full_serialize(self):
        return {
            'tracklog_id': self.id,
            'track_id': self.track_id,
            'track': Track.query.get(self.track_id).serialize(),
            'played': self.played,
            'djset': self.djset_id,
            'dj_id': self.dj_id,
            'dj_visible': self.dj.visible,
            'dj': self.dj.airname,
            'request': self.request,
            'vinyl': self.vinyl,
            'new': self.new,
            'rotation_id': self.rotation_id,
            'listeners': self.listeners,
        }


class Track(db.Model):
    __tablename__ = "track"
    # may need to make this a BigInteger
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(255))
    artist = db.Column(db.Unicode(255), index=True)
    album = db.Column(db.Unicode(255))
    label = db.Column(db.Unicode(255))
    added = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, title, artist, album, label):
        self.title = title
        self.artist = artist
        self.album = album
        self.label = label

    def validate(self):
        if len(self.title) <= 0 or len(self.artist) <= 0 or \
                len(self.album) <= 0 or len(self.label) <= 0:
            return False

        if 'TRACKMAN_ARTIST_BLACKLIST' in current_app.config and \
                self.artist in current_app.config['TRACKMAN_ARTIST_BLACKLIST']:
            return False

        if 'TRACKMAN_LABEL_BLACKLIST' in current_app.config and \
                self.label in current_app.config['TRACKMAN_LABEL_BLACKLIST']:
            return False

        return True

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'album': self.album,
            'label': self.label,
            'added': str(self.added),
        }


class TrackReport(db.Model):
    __tablename__ = "trackreport"
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'))
    resolution = db.Column(db.UnicodeText().with_variant(db.UnicodeText(length=2**1), 'mysql'))
    open = db.Column(db.Boolean, default=True)
    # Track being reported
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    track = db.relationship('Track', backref=db.backref('reports', lazy='dynamic'))
    # DJ who reported the track
    dj_id = db.Column(db.Integer, db.ForeignKey('dj.id'))
    dj = db.relationship('DJ', backref=db.backref('reports', lazy='dynamic'))

    def __init__(self, dj_id, track_id, reason):
        self.track_id = track_id
        self.dj_id = dj_id
        self.reason = reason
