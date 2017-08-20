import datetime
import dateutil
import pytz
from .models import TrackLog

CHART_PER_PAGE = 250


def get_range(period=None, year=None, month=None, week=None):
    first_track = TrackLog.query.order_by(TrackLog.played).first()
    if first_track is None:
        raise ValueError("Cannot determine range without any logged tracks")

    now = datetime.datetime.utcnow()

    if period == 'weekly':
        if year is not None or month is not None or week is not None:
            raise ValueError(
                "Weekly charts are available only for the current week.")

        start = now - datetime.timedelta(weeks=1)
        end = now
    elif period == 'monthly':
        if year is not None and month is not None:
            start = datetime.datetime(year=year, month=month, day=1)
            end = start + dateutil.relativedelta.relativedelta(months=1)
        else:
            start = datetime.datetime(year=now.year, month=now.month, day=1)
            end = now
    elif period == 'yearly':
        if year is not None:
            start = datetime.datetime(year=year, month=1, day=1)
            end = start + dateutil.relativedelta.relativedelta(years=1)
        else:
            start = datetime.datetime(year=now.year, month=1, day=1)
            end = now
    elif period is None:
        start = first_track.played
        end = datetime.datetime.utcnow()
    else:
        raise ValueError(
            "Period must be one of 'weekly', 'monthly', 'yearly', or None.")

    if first_track.played.tzinfo is not None:
        # add tzinfo to now to avoid attempted comparison of offset-aware and
        # offset-naive timezones
        now = now.replace(tzinfo=pytz.UTC)
        start = start.replace(tzinfo=pytz.UTC)
        end = end.replace(tzinfo=pytz.UTC)

    # reduce date resolution to 1 hour windows to make caching work
    start = start.replace(minute=0, second=0, microsecond=0)
    end = end.replace(minute=0, second=0, microsecond=0)

    # enforce datetime boundaries
    if start < first_track.played:
        start = first_track.played
    if end > now:
        end = now

    # sanity checking
    if start > now:
        raise ValueError("Start must be <= now")
    if start > end:
        raise ValueError("Start must be <= end")

    return start, end


def get(cache_key, query, limit=CHART_PER_PAGE):
    results = []
    ranking = 0
    last_value = None
    increment = 1

    for result in query.limit(limit):
        # calculate an appropriate ranking for each result
        # rankings will be tied for results that have the same value
        if result[-1] == last_value:
            increment += 1
        else:
            last_value = result[-1]
            ranking += increment
            increment = 1
        results.append(result + (ranking,))

    return results
