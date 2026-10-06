from datetime import datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from dbus2mqtt.util.dt import as_local, as_utc, now, utcnow


def test_now_without_args():
    """Test now() returns a timezone-aware datetime in local timezone."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        # Mock the local timezone to a fixed one for predictability
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        dt = now()
        assert isinstance(dt, datetime)
        assert dt.tzinfo == mock_tz


def test_now_with_string_tz():
    """Test now(tz) with a string timezone."""
    dt = now("Europe/Paris")
    assert isinstance(dt, datetime)
    assert dt.tzinfo == ZoneInfo("Europe/Paris")


def test_now_with_tzinfo_obj():
    """Test now(tz) with a tzinfo object."""
    dt = now(timezone.utc)
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc


def test_utcnow():
    """Test utcnow() returns a timezone-aware datetime in UTC."""
    dt = utcnow()
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc


def test_as_local_already_local():
    """Test as_local when datetime is already in local timezone."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=mock_tz)
        result = as_local(dt)
        assert result == dt


def test_as_local_naive():
    """Test as_local when datetime is naive (assumed local)."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # noqa: DTZ001
        result = as_local(naive_dt)
        expected = naive_dt.replace(tzinfo=mock_tz)
        assert result == expected


def test_as_local_from_other_tz():
    """Test as_local when datetime is in another timezone."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        # Create a datetime in UTC
        utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = as_local(utc_dt)
        # Check that the timezone is correct and the time is shifted appropriately.
        assert result.tzinfo == mock_tz
        # Check that the UTC time is the same
        assert result.astimezone(timezone.utc) == utc_dt


def test_as_utc_already_utc():
    """Test as_utc when datetime is already in UTC."""
    dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = as_utc(dt)
    assert result == dt


def test_as_utc_naive():
    """Test as_utc when datetime is naive (assumed local)."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        naive_dt = datetime(2025, 1, 1, 12, 0, 0)  # noqa: DTZ001
        result = as_utc(naive_dt)
        # First attach local tz, then convert to UTC
        expected = naive_dt.replace(tzinfo=mock_tz).astimezone(timezone.utc)
        assert result == expected


def test_as_utc_from_other_tz():
    """Test as_utc when datetime is in another timezone."""
    with patch("dbus2mqtt.util.dt.get_localzone") as mock_get_localzone:
        mock_tz = ZoneInfo("Europe/Amsterdam")
        mock_get_localzone.return_value = mock_tz

        # Create a datetime in Amsterdam time
        amsterdam_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=mock_tz)
        result = as_utc(amsterdam_dt)
        # Convert to UTC
        expected = amsterdam_dt.astimezone(timezone.utc)
        assert result == expected
