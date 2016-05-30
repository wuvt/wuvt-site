import datetime
import dateutil
from .. import cache
from .models import TrackLog

CHART_PER_PAGE = 250
CHART_TTL = 14400


def get_range(period, request):
    if period is not None:
        end = datetime.datetime.utcnow()

        if period == 'weekly':
            start = end - datetime.timedelta(weeks=1)
        elif period == 'monthly':
            start = end - dateutil.relativedelta.relativedelta(months=1)
        elif period == 'yearly':
            start = end - dateutil.relativedelta.relativedelta(years=1)
        else:
            raise ValueError("Period not one of weekly, monthly, or yearly")
    else:
        if 'start' in request.args:
            start = datetime.datetime.strptime(request.args['start'],
                                               "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            first_track = TrackLog.query.order_by(TrackLog.played).first()
            if first_track is not None:
                start = first_track.played
            else:
                start = datetime.datetime.utcnow()

        if 'end' in request.args:
            end = datetime.datetime.strptime(request.args['end'],
                                             "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            end = datetime.datetime.utcnow()

    # reduce date resolution to 1 hour windows to make caching work
    start = start.replace(minute=0, second=0, microsecond=0)
    end = end.replace(minute=0, second=0, microsecond=0)

    return start, end


def get(cache_key, query, limit=CHART_PER_PAGE):
    results = cache.get('charts:' + cache_key)
    if results is None:
        results = list(query.limit(limit))
        cache.set('charts:' + cache_key, results, timeout=CHART_TTL)
    return results
