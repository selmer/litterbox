"""Tests for the /dashboard API endpoint."""
from datetime import datetime, timezone, timedelta

import app.routers.dashboard as dashboard_state
from app.models import Cat, CleaningCycle, Visit


def _today():
    now = datetime.now(timezone.utc)
    return now.replace(hour=12, minute=0, second=0, microsecond=0)


def _add_cat(db, name="Luna", weight=4.0, active=True):
    cat = Cat(name=name, reference_weight_kg=weight, active=active)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def _add_visit(db, cat=None, started_at=None, ended_at=None, duration=120, weight=4.0):
    if started_at is None:
        started_at = _today()
    visit = Visit(
        cat_id=cat.id if cat else None,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        weight_kg=weight,
        identified_by="auto" if cat else None,
    )
    db.add(visit)
    db.commit()
    return visit


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------

def test_dashboard_returns_ok(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "cats" in data
    assert "unidentified_visits_today" in data
    assert "cleaning_cycles_today" in data
    assert "poller_healthy" in data


def test_dashboard_empty(client):
    resp = client.get("/dashboard")
    data = resp.json()
    assert data["cats"] == []
    assert data["unidentified_visits_today"] == 0
    assert data["cleaning_cycles_today"] == 0
    assert data["poller_healthy"] is False


# ---------------------------------------------------------------------------
# Cat stats
# ---------------------------------------------------------------------------

def test_dashboard_visits_today(client, db):
    cat = _add_cat(db)
    _add_visit(db, cat=cat, ended_at=_today())
    _add_visit(db, cat=cat, ended_at=_today())

    resp = client.get("/dashboard").json()
    assert resp["cats"][0]["visits_today"] == 2


def test_dashboard_only_counts_todays_visits(client, db):
    cat = _add_cat(db)
    yesterday = _today() - timedelta(days=1)
    _add_visit(db, cat=cat, started_at=yesterday, ended_at=yesterday)
    _add_visit(db, cat=cat, ended_at=_today())

    resp = client.get("/dashboard").json()
    assert resp["cats"][0]["visits_today"] == 1


def test_dashboard_inactive_cat_excluded(client, db):
    _add_cat(db, name="Ghost", active=False)
    resp = client.get("/dashboard").json()
    assert resp["cats"] == []


# ---------------------------------------------------------------------------
# Unidentified visits — in-progress visits are INCLUDED (assumption 5 fix)
# ---------------------------------------------------------------------------

def test_dashboard_counts_completed_unidentified_visits(client, db):
    _add_visit(db, cat=None, ended_at=_today())
    resp = client.get("/dashboard").json()
    assert resp["unidentified_visits_today"] == 1


def test_dashboard_counts_in_progress_unidentified_visits(client, db):
    """In-progress (ended_at=NULL) unidentified visits must be counted."""
    _add_visit(db, cat=None, ended_at=None)
    resp = client.get("/dashboard").json()
    assert resp["unidentified_visits_today"] == 1


def test_dashboard_identified_visit_not_counted_as_unidentified(client, db):
    cat = _add_cat(db)
    _add_visit(db, cat=cat, ended_at=_today())
    resp = client.get("/dashboard").json()
    assert resp["unidentified_visits_today"] == 0


def test_dashboard_yesterday_unidentified_not_counted(client, db):
    yesterday = _today() - timedelta(days=1)
    _add_visit(db, cat=None, started_at=yesterday, ended_at=yesterday)
    resp = client.get("/dashboard").json()
    assert resp["unidentified_visits_today"] == 0


# ---------------------------------------------------------------------------
# Cleaning cycles
# ---------------------------------------------------------------------------

def test_dashboard_cleaning_cycles_today(client, db):
    cycle = CleaningCycle(started_at=_today())
    db.add(cycle)
    db.commit()
    resp = client.get("/dashboard").json()
    assert resp["cleaning_cycles_today"] == 1


# ---------------------------------------------------------------------------
# Poller health — threshold is now 2× POLL_INTERVAL_SECONDS (default 600 s)
# ---------------------------------------------------------------------------

def test_poller_healthy_when_recent_poll(client):
    dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
    resp = client.get("/dashboard").json()
    assert resp["poller_healthy"] is True


def test_poller_unhealthy_when_stale(client):
    dashboard_state.last_successful_poll_at = (
        datetime.now(timezone.utc) - timedelta(seconds=700)
    )
    resp = client.get("/dashboard").json()
    assert resp["poller_healthy"] is False


def test_poller_unhealthy_when_never_polled(client):
    dashboard_state.last_successful_poll_at = None
    resp = client.get("/dashboard").json()
    assert resp["poller_healthy"] is False
