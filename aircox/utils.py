import datetime
import django.utils.timezone as tz


def date_range(date):
    """
    Return a range of datetime for a given day, such as:
        [date, 0:0:0:0; date, 23:59:59:999]

    Ensure timezone awareness.
    """
    date = date_or_default(date)
    range = (
        date.replace(hour = 0, minute = 0, second = 0), \
        date.replace(hour = 23, minute = 59, second = 59, microsecond = 999)
    )
    return range

def cast_date(date, to_datetime = True):
    """
    Given a date reset its time information and
    return it as a date or datetime object.

    Ensure timezone awareness.
    """
    if to_datetime:
        return tz.make_aware(
            tz.datetime(date.year, date.month, date.day, 0, 0, 0, 0)
        )
    return datetime.date(date.year, date.month, date.day)

def date_or_default(date, reset_time = False, keep_type = False, to_datetime = True):
    """
    Return datetime or default value (now) if not defined, and remove time info
    if reset_time is True.

    \param reset_time   reset time info to 0
    \param keep_type    keep the same type of the given date if not None
    \param to_datetime  force conversion to datetime if not keep_type

    Ensure timezone awareness.
    """
    date = date or tz.now()
    to_datetime = isinstance(date, tz.datetime) if keep_type else to_datetime

    if reset_time or not isinstance(date, tz.datetime):
        return cast_date(date, to_datetime)

    if not tz.is_aware(date):
        date = tz.make_aware(date)
    return date

def to_timedelta (time):
    """
    Transform a datetime or a time instance to a timedelta,
    only using time info
    """
    return datetime.timedelta(
        hours = time.hour,
        minutes = time.minute,
        seconds = time.second
    )

def seconds_to_time (seconds):
    """
    Seconds to datetime.time
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return datetime.time(hour = hours, minute = minutes, second = seconds)

