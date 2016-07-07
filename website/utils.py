
def duration_to_str(duration):
    return duration.strftime(
        '%H:%M:%S' if duration.hour else '%M:%S'
    )

