import logging
import sys
import traceback


def start_logging(level: str):
    """
    Switch on logging using a simple tabular formatter otherwise.

    This function is intended to be used immediately when an application starts running.

    This function also calls silence_3rd_party_logs() internally.

    Parameters
    ----------
    level : str
        The minimum level of the logs to be captured, one of DEBUG, INFO, WARNING, ERROR or CRITICAL.

    Returns
    -------
    None
    """
    silence_3rd_party_logs()
    # format_template = '%(levelname)-10s %(message)s -- in %(filename)s @ line %(lineno)d'
    format_template = '%(asctime)s    %(filename)-25s @ line %(lineno)-5d  %(levelname)-10s %(message)-120s'
    logging.basicConfig(stream=sys.stdout, level=level, format=format_template)


def silence_3rd_party_logs():
    """
    Silence logging generated by the boto3 and Snowflake python packages.
    """
    # ref: https://github.com/boto/boto3/issues/521
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('nose').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    # mute Snowflake connector logging
    # https://stackoverflow.com/questions/56525319/turning-off-snowflake-db-logging-while-still-keeping-log-level-as-debug  # noqa
    for name in logging.Logger.manager.loggerDict.keys():
        if 'snowflake' in name:
            logging.getLogger(name).setLevel(logging.WARNING)
            logging.getLogger(name).propagate = False


def format_exception(exc_info):
    """
    Utility function to format an exception info object as string.

    Parameters
    ----------
    exc_info : ExceptionInfo
        The ExceptionInfo object to be formatted.

    Returns
    -------
    str
        The formatted ExceptionInfo object.
    """
    if exc_info is not None:
        exception_type = exc_info[0]
        exception_info = {
            'name': exception_type.__name__,
            'qualname': exception_type.__qualname__,
            'class': str(exception_type),
            'module': exception_type.__module__,
            'msg': str(exc_info[1]),
        }
        tb = traceback.format_exception(exception_type, exc_info[1], exc_info[2])
        exception_info['traceback'] = tb
        return exception_info
