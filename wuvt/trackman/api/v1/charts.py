from flask_restful import abort, Resource
from wuvt import db
from wuvt.trackman import charts
from wuvt.trackman.models import DJ, Track, TrackLog
from .base import ChartResource


class Charts(Resource):
    def get(self):
        return {
            'albums': "Top albums",
            'artists': "Top artists",
            'tracks': "Top tracks",
        }


class AlbumCharts(ChartResource):
    def get(self, period=None, year=None, month=None):
        try:
            start, end = charts.get_range(period, year, month)
        except ValueError:
            abort(404)

        results = charts.get(
            'albums_{0}_{1}'.format(start, end),
            Track.query.with_entities(
                Track.artist, Track.album, db.func.count(TrackLog.id)).
            join(TrackLog).filter(db.and_(
                TrackLog.dj_id > 1,
                TrackLog.played >= start,
                TrackLog.played <= end)).
            group_by(Track.artist, Track.album).
            order_by(db.func.count(TrackLog.id).desc()))

        return {
            'start': start,
            'end': end,
            'results': [(x[0], x[1], x[2], x[3]) for x in results],
        }


class DJAlbumCharts(ChartResource):
    def get(self, dj_id):
        dj = DJ.query.get_or_404(dj_id)
        results = charts.get(
            'albums_dj_{}'.format(dj_id),
            Track.query.with_entities(
                Track.artist, Track.album, db.func.count(TrackLog.id)).
            join(TrackLog).filter(TrackLog.dj_id == dj.id).
            group_by(Track.artist, Track.album).
            order_by(db.func.count(TrackLog.id).desc()))

        return {
            'dj': dj.serialize(),
            'results': [(x[0], x[1], x[2], x[3]) for x in results],
        }


class ArtistCharts(ChartResource):
    def get(self, period=None, year=None, month=None):
        try:
            start, end = charts.get_range(period, year, month)
        except ValueError:
            abort(404)

        results = charts.get(
            'artists_{0}_{1}'.format(start, end),
            Track.query.with_entities(Track.artist, db.func.count(TrackLog.id)).
            join(TrackLog).filter(db.and_(
                TrackLog.dj_id > 1,
                TrackLog.played >= start,
                TrackLog.played <= end)).
            group_by(Track.artist).
            order_by(db.func.count(TrackLog.id).desc()))

        return {
            'start': start,
            'end': end,
            'results': [(x[0], x[1], x[2]) for x in results],
        }


class DJArtistCharts(ChartResource):
    def get(self, dj_id):
        dj = DJ.query.get_or_404(dj_id)
        results = charts.get(
            'artists_dj_{}'.format(dj_id),
            Track.query.with_entities(Track.artist, db.func.count(TrackLog.id)).
            join(TrackLog).filter(TrackLog.dj_id == dj.id).
            group_by(Track.artist).
            order_by(db.func.count(TrackLog.id).desc()))

        return {
            'dj': dj.serialize(),
            'results': [(x[0], x[1], x[2]) for x in results],
        }


class TrackCharts(ChartResource):
    def get(self, period=None, year=None, month=None):
        try:
            start, end = charts.get_range(period, year, month)
        except ValueError:
            abort(404)

        subquery = TrackLog.query.\
            with_entities(TrackLog.track_id,
                          db.func.count(TrackLog.id).label('count')).\
            filter(TrackLog.dj_id > 1,
                   TrackLog.played >= start,
                   TrackLog.played <= end).\
            group_by(TrackLog.track_id).subquery()
        results = charts.get(
            'tracks_{start}_{end}'.format(start=start, end=end),
            Track.query.with_entities(Track, subquery.c.count).
            join(subquery).order_by(db.desc(subquery.c.count)))

        return {
            'start': start,
            'end': end,
            'results': [(x[0].serialize(), x[1], x[2]) for x in results],
        }


class DJTrackCharts(ChartResource):
    def get(self, dj_id):
        dj = DJ.query.get_or_404(dj_id)

        subquery = TrackLog.query.\
            with_entities(TrackLog.track_id,
                          db.func.count(TrackLog.id).label('count')).\
            filter(TrackLog.dj_id == dj.id).\
            group_by(TrackLog.track_id).subquery()
        results = charts.get(
            'tracks_dj_{}'.format(dj_id),
            Track.query.with_entities(Track, subquery.c.count).
            join(subquery).order_by(db.desc(subquery.c.count)))

        return {
            'dj': dj.serialize(),
            'results': [(x[0].serialize(), x[1], x[2]) for x in results],
        }


class DJSpinCharts(ChartResource):
    def get(self):
        subquery = TrackLog.query.\
            with_entities(TrackLog.dj_id,
                          db.func.count(TrackLog.id).label('count')).\
            group_by(TrackLog.dj_id).subquery()

        results = charts.get(
            'dj_spins',
            DJ.query.with_entities(DJ, subquery.c.count).
            join(subquery).filter(DJ.visible == True).
            order_by(db.desc(subquery.c.count)))

        return {
            'results': [(x[0].serialize(), x[1], x[2]) for x in results],
        }


class DJVinylSpinCharts(ChartResource):
    def get(self):
        subquery = TrackLog.query.\
            with_entities(TrackLog.dj_id,
                          db.func.count(TrackLog.id).label('count')).\
            filter(TrackLog.vinyl == True).\
            group_by(TrackLog.dj_id).subquery()

        results = charts.get(
            'dj_vinyl_spins',
            DJ.query.with_entities(DJ, subquery.c.count).
            join(subquery).filter(DJ.visible == True).
            order_by(db.desc(subquery.c.count)))

        return {
            'results': [(x[0].serialize(), x[1], x[2]) for x in results],
        }
