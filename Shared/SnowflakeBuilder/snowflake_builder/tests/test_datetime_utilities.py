import snowflake_builder.utilities.datetime_utilities as datetime_utilities
from datetime import timedelta


def test_format_timedelta():
    value = timedelta(hours=9, minutes=56, seconds=2)
    assert datetime_utilities.format_timedelta(value) == '09 hr 56 min 02 sec'
    value = timedelta(minutes=8, seconds=0)
    assert datetime_utilities.format_timedelta(value) == '08 min 00 sec'
    value = timedelta(seconds=12)
    assert datetime_utilities.format_timedelta(value) == '12 sec'
