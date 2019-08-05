import datetime
import django.utils.timezone as tz


__all__ = ['Redirect', 'redirect', 'date_range', 'cast_date',
           'date_or_default', 'to_timedelta', 'seconds_to_time']


class Redirect(Exception):
    """ Redirect exception -- see `redirect()`. """
    def __init__(self, url):
        self.url = url


def redirect(url):
    """
    Raise a Redirect exception in order to response a redirection to client.
    AircoxMiddleware must be enabled. """
    raise Redirect(url)


def date_range(date, delta=None, **delta_kwargs):
    """
    Return a range of provided date such as `[date-delta, date+delta]`.
    :param date: the reference date
    :param delta: timedelta
    :param \**delta_kwargs: timedelta init arguments

    Return a datetime range for a given day, as:
    ```(date, 0:0:0:0; date, 23:59:59:999)```.
    """
    delta = tz.timedelta(**delta_kwargs) if delta is None else delta
    return [date - delta, date + delta]


def cast_date(date, into=datetime.date):
    """
    Cast a given date into the provided class' instance. Make datetime
    aware of timezone.
    """
    date = into(date.year, date.month, date.day)
    return tz.make_aware(date) if issubclass(into, tz.datetime) else date


def date_or_default(date, into=None):
    """
    Return date if not None, otherwise return now. Cast result into provided
    type if any.
    """
    date = date if date is not None else datetime.date.today() \
        if into is not None and issubclass(into, datetime.date) else tz.now()

    if into is not None:
        date = cast_date(date, into)

    if isinstance(date, tz.datetime) and not tz.is_aware(date):
        date = tz.make_aware(date)
    return date


def to_timedelta(time):
    """
    Transform a datetime or a time instance to a timedelta,
    only using time info
    """
    return datetime.timedelta(
        hours=time.hour,
        minutes=time.minute,
        seconds=time.second
    )


def to_seconds(time):
    """ Return total seconds for provided time """
    return 3600 * time.hour + 60 * time.minute + time.second


def seconds_to_time(seconds):
    """
    Seconds to datetime.time
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return datetime.time(hour=hours, minute=minutes, second=seconds)

