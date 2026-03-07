"""Tests for the /cleaning-cycles API endpoint."""
from datetime import datetime, timezone

from app.models import CleaningCycle


def test_list_cleaning_cycles_empty(client):
    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    assert response.json() == []


def test_list_cleaning_cycles(client, db_session):
    now = datetime.now(timezone.utc)
    db_session.add(CleaningCycle(started_at=now))
    db_session.commit()

    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    cycles = response.json()
    assert len(cycles) == 1
    assert cycles[0]["ended_at"] is None


def test_list_cleaning_cycles_limit(client, db_session):
    now = datetime.now(timezone.utc)
    for _ in range(5):
        db_session.add(CleaningCycle(started_at=now))
    db_session.commit()

    response = client.get("/cleaning-cycles?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_cleaning_cycles_returns_most_recent_first(client, db_session):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    db_session.add(CleaningCycle(started_at=now - timedelta(hours=2)))
    db_session.add(CleaningCycle(started_at=now))
    db_session.commit()

    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    cycles = response.json()
    # Most recent should be first
    first_time = datetime.fromisoformat(cycles[0]["started_at"])
    second_time = datetime.fromisoformat(cycles[1]["started_at"])
    assert first_time > second_time
