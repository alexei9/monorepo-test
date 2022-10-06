from datetime import timedelta


def format_timedelta(td: timedelta) -> str:
    """
    Format a time duration as {:02}h {:02} min {:02} sec, omitting the hour and minute portions if the time duration
    is less than one hour or one minute.

    Parameters
    ----------
    td : timedelta
        The time duration to format.

    Returns
    -------
    str
        The specified time duration as a string.
    """
    s = td.total_seconds()
    hours, remainder = divmod(s, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return '{:02} hr {:02} min {:02} sec'.format(int(hours), int(minutes), int(seconds))
    elif minutes > 0:
        return '{:02} min {:02} sec'.format(int(minutes), int(seconds))
    else:
        return '{:02} sec'.format(int(seconds))
