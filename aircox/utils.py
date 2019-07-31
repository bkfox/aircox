import datetime
import django.utils.timezone as tz


def date_range(date):
    """
    Return a datetime range for a given day, as:
    ```(date, 0:0:0:0; date, 23:59:59:999)```.
    """
    date = date_or_default(date, tz.datetime)
    return (
        date.replace(hour=0, minute=0, second=0),
        date.replace(hour=23, minute=59, second=59, microsecond=999)
    )


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


def seconds_to_time(seconds):
    """
    Seconds to datetime.time
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return datetime.time(hour=hours, minute=minutes, second=seconds)

