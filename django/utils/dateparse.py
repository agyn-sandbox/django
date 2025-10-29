"""Functions to parse datetime objects."""

# We're using regular expressions rather than time.strptime because:
# - They provide both validation and parsing.
# - They're more flexible for datetimes.
# - The date/datetime/time constructors produce friendlier error messages.

import datetime
import re

from django.utils.timezone import get_fixed_timezone, utc

date_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
)

time_re = re.compile(
    r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
)

datetime_re = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
    r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
    r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    r'(?P<tzinfo>Z|[+-]\d{2}(?::?\d{2})?)?$'
)

standard_duration_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days?, )?)?'
    r'((?:(?P<hours>-?\d+):)(?=\d+:\d+))?'
    r'(?:(?P<minutes>-?\d+):)?'
    r'(?P<seconds>-?\d+)'
    r'(?:\.(?P<microseconds>\d{1,6})\d{0,6})?'
    r'$'
)

# Support the sections of ISO 8601 date representation that are accepted by
# timedelta
iso8601_duration_re = re.compile(
    r'^(?P<sign>[-+]?)'
    r'P'
    r'(?:(?P<days>\d+(.\d+)?)D)?'
    r'(?:T'
    r'(?:(?P<hours>\d+(.\d+)?)H)?'
    r'(?:(?P<minutes>\d+(.\d+)?)M)?'
    r'(?:(?P<seconds>\d+(.\d+)?)S)?'
    r')?'
    r'$'
)

# Support PostgreSQL's day-time interval format, e.g. "3 days 04:05:06". The
# year-month and mixed intervals cannot be converted to a timedelta and thus
# aren't accepted.
postgres_interval_re = re.compile(
    r'^'
    r'(?:(?P<days>-?\d+) (days? ?))?'
    r'(?:(?P<sign>[-+])?'
    r'(?P<hours>\d+):'
    r'(?P<minutes>\d\d):'
    r'(?P<seconds>\d\d)'
    r'(?:\.(?P<microseconds>\d{1,6}))?'
    r')?$'
)


def parse_date(value):
    """Parse a string and return a datetime.date.

    Raise ValueError if the input is well formatted but not a valid date.
    Return None if the input isn't well formatted.
    """
    match = date_re.match(value)
    if match:
        kw = {k: int(v) for k, v in match.groupdict().items()}
        return datetime.date(**kw)


def parse_time(value):
    """Parse a string and return a datetime.time.

    This function doesn't support time zone offsets.

    Raise ValueError if the input is well formatted but not a valid time.
    Return None if the input isn't well formatted, in particular if it
    contains an offset.
    """
    match = time_re.match(value)
    if match:
        kw = match.groupdict()
        kw['microsecond'] = kw['microsecond'] and kw['microsecond'].ljust(6, '0')
        kw = {k: int(v) for k, v in kw.items() if v is not None}
        return datetime.time(**kw)


def parse_datetime(value):
    """Parse a string and return a datetime.datetime.

    This function supports time zone offsets. When the input contains one,
    the output uses a timezone with a fixed offset from UTC.

    Raise ValueError if the input is well formatted but not a valid datetime.
    Return None if the input isn't well formatted.
    """
    match = datetime_re.match(value)
    if match:
        kw = match.groupdict()
        kw['microsecond'] = kw['microsecond'] and kw['microsecond'].ljust(6, '0')
        tzinfo = kw.pop('tzinfo')
        if tzinfo == 'Z':
            tzinfo = utc
        elif tzinfo is not None:
            offset_mins = int(tzinfo[-2:]) if len(tzinfo) > 3 else 0
            offset = 60 * int(tzinfo[1:3]) + offset_mins
            if tzinfo[0] == '-':
                offset = -offset
            tzinfo = get_fixed_timezone(offset)
        kw = {k: int(v) for k, v in kw.items() if v is not None}
        kw['tzinfo'] = tzinfo
        return datetime.datetime(**kw)


def parse_duration(value):
    """Parse a duration string and return a datetime.timedelta.

    The preferred format for durations in Django is '%d %H:%M:%S.%f'.

    Also supports ISO 8601 representation and PostgreSQL's day-time interval
    format.
    """
    # Prefer standard duration handling first to implement stricter minus rules.
    std_match = standard_duration_re.match(value)
    if std_match:
        # Reject any minus sign appearing after a colon.
        if ':-' in value:
            return None
        # Reject double leading minus.
        if value.startswith('--'):
            return None

        kw = std_match.groupdict()
        days_str = kw.get('days')

        # Reject mixed-sign forms like "1 days, -2:03:04" (positive days, negative time).
        if days_str is not None and not days_str.startswith('-'):
            hours_s = kw.get('hours') or ''
            minutes_s = kw.get('minutes') or ''
            seconds_s = kw.get('seconds') or ''
            if hours_s.startswith('-') or minutes_s.startswith('-') or seconds_s.startswith('-'):
                return None

        # Apply a single leading minus to negate entire time-only duration.
        apply_global_sign = False
        if days_str is None and value.startswith('-'):
            colon_count = value.count(':')
            # For SS or MM:SS always apply global sign; for HH:MM:SS apply it
            # only when hours are zero-padded (e.g., "-00:01:01").
            if colon_count <= 1 or (colon_count == 2 and value.startswith('-0')):
                apply_global_sign = True

        if apply_global_sign:
            unsigned = value[1:]
            unsigned_match = standard_duration_re.match(unsigned)
            if not unsigned_match:
                return None
            ukw = unsigned_match.groupdict()
            days = datetime.timedelta(float(ukw.pop('days', 0) or 0))
            if ukw.get('microseconds'):
                ukw['microseconds'] = ukw['microseconds'].ljust(6, '0')
            if ukw.get('seconds') and ukw.get('microseconds') and ukw['seconds'].startswith('-'):
                ukw['microseconds'] = '-' + ukw['microseconds']
            ukw = {k: float(v) for k, v in ukw.items() if v is not None}
            return -(days + datetime.timedelta(**ukw))

        # Default behavior preserves existing per-component signs.
        days = datetime.timedelta(float(kw.pop('days', 0) or 0))
        # 'sign' only applies to ISO 8601/postgres formats.
        kw.pop('sign', None)
        if kw.get('microseconds'):
            kw['microseconds'] = kw['microseconds'].ljust(6, '0')
        if kw.get('seconds') and kw.get('microseconds') and kw['seconds'].startswith('-'):
            kw['microseconds'] = '-' + kw['microseconds']
        kw = {k: float(v) for k, v in kw.items() if v is not None}
        return days + datetime.timedelta(**kw)

    # ISO 8601: apply leading sign uniformly to all components including days.
    iso_match = iso8601_duration_re.match(value)
    if iso_match:
        kw = iso_match.groupdict()
        sign = -1 if kw.pop('sign', '+') == '-' else 1
        days = float(kw.pop('days', 0) or 0)
        if kw.get('microseconds'):
            kw['microseconds'] = kw['microseconds'].ljust(6, '0')
        if kw.get('seconds') and kw.get('microseconds') and kw['seconds'].startswith('-'):
            kw['microseconds'] = '-' + kw['microseconds']
        kw = {k: float(v) for k, v in kw.items() if v is not None}
        total = datetime.timedelta(days=days, **kw)
        return sign * total

    # PostgreSQL interval format.
    pg_match = postgres_interval_re.match(value)
    if pg_match:
        kw = pg_match.groupdict()
        days = datetime.timedelta(float(kw.pop('days', 0) or 0))
        sign = -1 if kw.pop('sign', '+') == '-' else 1
        if kw.get('microseconds'):
            kw['microseconds'] = kw['microseconds'].ljust(6, '0')
        if kw.get('seconds') and kw.get('microseconds') and kw['seconds'].startswith('-'):
            kw['microseconds'] = '-' + kw['microseconds']
        kw = {k: float(v) for k, v in kw.items() if v is not None}
        return days + sign * datetime.timedelta(**kw)

    return None
