import datetime

def to_timedelta (time):
    """
    Transform a datetime or a time instance to a timedelta,
    only using time info
    """
    return datetime.timedelta(
        hours = time.hour,
        minutes = time.minute,
        seconds = time.seconds
    )


def seconds_to_time (seconds):
    """
    Seconds to datetime.time
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return datetime.time(hour = hours, minute = minutes, second = seconds)


