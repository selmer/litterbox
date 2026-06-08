import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_APP_TIMEZONE = "Europe/Amsterdam"
APP_TIMEZONE_ENV = "APP_TIMEZONE"


def app_timezone() -> ZoneInfo:
    timezone_name = os.getenv(APP_TIMEZONE_ENV, DEFAULT_APP_TIMEZONE)
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise RuntimeError(f"Invalid {APP_TIMEZONE_ENV}: {timezone_name}") from exc


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def local_day_start_utc(now: datetime) -> datetime:
    local_now = as_utc(now).astimezone(app_timezone())
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(timezone.utc)
