"""Tests for the /cleaning-cycles API endpoints."""
from datetime import datetime, timezone, timedelta

from app.models import CleaningCycle


def _add_cycle(db, minutes_ago=10, ended=True):
    now = datetime.now(timezone.utc)
    started = now - timedelta(minutes=minutes_ago)
    cycle = CleaningCycle(
        started_at=started,
        ended_at=now if ended else None,
    )
    db.add(cycle)
    db.commit()
    return cycle


def test_list_cleaning_cycles_empty(client):
    resp = client.get("/cleaning-cycles")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_cleaning_cycles(client, db):
    _add_cycle(db, minutes_ago=20)
    _add_cycle(db, minutes_ago=10)
    resp = client.get("/cleaning-cycles")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_cleaning_cycles_ordered_newest_first(client, db):
    _add_cycle(db, minutes_ago=30)
    _add_cycle(db, minutes_ago=5)
    cycles = client.get("/cleaning-cycles").json()
    # Most recent first — started_at of first item should be later
    t0 = cycles[0]["started_at"]
    t1 = cycles[1]["started_at"]
    assert t0 > t1


def test_list_cleaning_cycles_limit(client, db):
    for i in range(5):
        _add_cycle(db, minutes_ago=i + 1)
    resp = client.get("/cleaning-cycles", params={"limit": 3})
    assert len(resp.json()) == 3


def test_in_progress_cycle_has_no_ended_at(client, db):
    _add_cycle(db, ended=False)
    cycles = client.get("/cleaning-cycles").json()
    assert len(cycles) == 1
    assert cycles[0]["ended_at"] is None
