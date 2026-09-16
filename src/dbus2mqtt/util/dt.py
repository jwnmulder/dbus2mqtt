from datetime import datetime, timezone, tzinfo
from zoneinfo import ZoneInfo

from tzlocal import get_localzone


def now(tz: tzinfo | str | None = None) -> datetime:
    """Return the current date and time in the specified timezone.

    Args:
        tz: A timezone object or IANA timezone name. If omitted, the
            system's local timezone is used.

    Returns:
        The current timezone-aware datetime.
    """
    if isinstance(tz, str):
        tz = ZoneInfo(key=tz)

    return datetime.now(tz or get_localzone())


def utcnow() -> datetime:
    """Return the current date and time in UTC.

    Returns:
        The current timezone-aware datetime in UTC.
    """
    return datetime.now(tz=timezone.utc)


def as_local(value: datetime) -> datetime:
    """Convert a datetime to the system's local timezone.

    Naive datetimes are assumed to already represent local time.

    Args:
        value: The datetime to convert.

    Returns:
        A datetime localized to the system's local timezone.
    """
    localzone = get_localzone()

    if value.tzinfo == localzone:
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=localzone)

    return value.astimezone(localzone)


def as_utc(value: datetime) -> datetime:
    """Convert a datetime to UTC.

    Naive datetimes are assumed to already represent local time.

    Args:
        value: The datetime to convert.

    Returns:
        A datetime converted to UTC.
    """
    localzone = get_localzone()

    if value.tzinfo == timezone.utc:
        return value
    if value.tzinfo is None:
        dattim = value.replace(tzinfo=localzone)

    return dattim.astimezone(timezone.utc)
