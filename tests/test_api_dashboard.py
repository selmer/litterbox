"""
Tests for the /dashboard endpoint.

Functions/scenarios needing owner input:
  - POLLER_HEALTHY_THRESHOLD_SECONDS is 30 seconds. Is this threshold appropriate
    for the polling interval configured in production? If POLL_INTERVAL_SECONDS
    is 300, the dashboard will almost always show the poller as unhealthy in
    tests (and in practice, between polls). Confirm whether this is intentional
    or if the threshold should be adjusted.
  - Should the dashboard count visits that are still in progress (ended_at=None)
    toward visits_today and time_in_box_today_seconds?
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.models import Cat, Visit, CleaningCycle


def _add_cat(db, name="TestCat", weight=4.0):
    cat = Cat(name=name, reference_weight_kg=weight)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _add_visit(db, cat, started_at, duration_seconds=120, weight_kg=4.0, ended_at=None):
    v = Visit(
        cat_id=cat.id,
        started_at=started_at,
        ended_at=ended_at or started_at + timedelta(seconds=duration_seconds),
        duration_seconds=duration_seconds,
        weight_kg=weight_kg,
        identified_by="auto",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def test_dashboard_no_cats(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["cats"] == []
    assert data["unidentified_visits_today"] == 0
    assert data["cleaning_cycles_today"] == 0
    assert data["poller_healthy"] is False  # no poll has happened in tests
    assert "generated_at" in data


def test_dashboard_shows_active_cats_only(client, db):
    _add_cat(db, name="Active")
    inactive = _add_cat(db, name="Inactive")
    inactive.active = False
    db.commit()

    response = client.get("/dashboard")
    data = response.json()
    names = [c["cat_name"] for c in data["cats"]]
    assert "Active" in names
    assert "Inactive" not in names


def test_dashboard_visits_today(client, db):
    cat = _add_cat(db)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    _add_visit(db, cat, started_at=today_start + timedelta(hours=1))
    _add_visit(db, cat, started_at=today_start + timedelta(hours=3))

    response = client.get("/dashboard")
    data = response.json()
    cat_data = data["cats"][0]
    assert cat_data["visits_today"] == 2


def test_dashboard_time_in_box_today(client, db):
    cat = _add_cat(db)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    _add_visit(db, cat, started_at=today_start + timedelta(hours=1), duration_seconds=60)
    _add_visit(db, cat, started_at=today_start + timedelta(hours=2), duration_seconds=90)

    response = client.get("/dashboard")
    data = response.json()
    cat_data = data["cats"][0]
    assert cat_data["time_in_box_today_seconds"] == 150


def test_dashboard_excludes_yesterday_visits(client, db):
    cat = _add_cat(db)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    _add_visit(db, cat, started_at=yesterday)

    response = client.get("/dashboard")
    data = response.json()
    cat_data = data["cats"][0]
    assert cat_data["visits_today"] == 0
    assert cat_data["time_in_box_today_seconds"] == 0


def test_dashboard_last_visit(client, db):
    cat = _add_cat(db)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    _add_visit(db, cat, started_at=today_start + timedelta(hours=1), weight_kg=4.2, duration_seconds=75)

    response = client.get("/dashboard")
    data = response.json()
    cat_data = data["cats"][0]
    assert cat_data["last_visit_weight_kg"] == 4.2
    assert cat_data["last_visit_duration_seconds"] == 75
    assert cat_data["last_visit_at"] is not None


def test_dashboard_unidentified_visits_today(client, db):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    v = Visit(
        cat_id=None,
        started_at=today_start + timedelta(hours=1),
        ended_at=today_start + timedelta(hours=1, minutes=2),
        duration_seconds=120,
        weight_kg=3.5,
    )
    db.add(v)
    db.commit()

    response = client.get("/dashboard")
    data = response.json()
    assert data["unidentified_visits_today"] == 1


def test_dashboard_cleaning_cycles_today(client, db):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    db.add(CleaningCycle(started_at=today_start + timedelta(hours=2)))
    db.add(CleaningCycle(started_at=today_start + timedelta(hours=4)))
    db.commit()

    response = client.get("/dashboard")
    data = response.json()
    assert data["cleaning_cycles_today"] == 2


def test_dashboard_poller_healthy(client):
    import app.routers.dashboard as dashboard_state
    dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)

    response = client.get("/dashboard")
    data = response.json()
    assert data["poller_healthy"] is True

    # Clean up
    dashboard_state.last_successful_poll_at = None
