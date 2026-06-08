from datetime import datetime, timezone

import pytest

from app.timezones import local_day_start_utc


def test_local_day_start_utc_uses_amsterdam_summer_time(monkeypatch):
    monkeypatch.setenv("APP_TIMEZONE", "Europe/Amsterdam")

    today_start = local_day_start_utc(datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc))

    assert today_start == datetime(2026, 6, 7, 22, 0, tzinfo=timezone.utc)


def test_local_day_start_utc_uses_amsterdam_winter_time(monkeypatch):
    monkeypatch.setenv("APP_TIMEZONE", "Europe/Amsterdam")

    today_start = local_day_start_utc(datetime(2026, 1, 8, 12, 0, tzinfo=timezone.utc))

    assert today_start == datetime(2026, 1, 7, 23, 0, tzinfo=timezone.utc)


def test_local_day_start_utc_rejects_invalid_timezone(monkeypatch):
    monkeypatch.setenv("APP_TIMEZONE", "Mars/Olympus_Mons")

    with pytest.raises(RuntimeError, match="Invalid APP_TIMEZONE"):
        local_day_start_utc(datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc))
