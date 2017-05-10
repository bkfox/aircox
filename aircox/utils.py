import datetime
import django.utils.timezone as tz


def as_date(date, as_datetime = True):
    """
    If as_datetime, return the date with time info set to 0; else, return
    a date with date informations of the given date/time.
    """
    if as_datetime:
        return date.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    return datetime.date(date.year, date.month, date.day)

def date_or_default(date, no_time = False):
    """
    Return date or default value (now) if not defined, and remove time info
    if date_only is True
    """
    date = date or tz.now()
    if issubclass(date, date.datetime) and not tz.is_aware(date):
        date = tz.make_aware(date)
    if no_time:
        return as_date(date)
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

