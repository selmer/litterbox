"""Tests for the /cleaning-cycles API endpoint."""
from datetime import datetime, timezone

from app.models import CleaningCycle


def test_list_cleaning_cycles_empty(client):
    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    assert response.json() == []


def test_list_cleaning_cycles(client, db):
    now = datetime.now(timezone.utc)
    db.add(CleaningCycle(started_at=now))
    db.commit()

    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ended_at"] is None


def test_list_cleaning_cycles_completed(client, db):
    from datetime import timedelta
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(minutes=5)
    db.add(CleaningCycle(started_at=start, ended_at=end))
    db.commit()

    response = client.get("/cleaning-cycles")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["ended_at"] is not None


def test_list_cleaning_cycles_respects_limit(client, db):
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    for i in range(5):
        db.add(CleaningCycle(started_at=now + timedelta(minutes=i)))
    db.commit()

    response = client.get("/cleaning-cycles", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_cleaning_cycles_ordered_newest_first(client, db):
    from datetime import timedelta
    base = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    db.add(CleaningCycle(started_at=base))
    db.add(CleaningCycle(started_at=base + timedelta(hours=1)))
    db.commit()

    response = client.get("/cleaning-cycles")
    data = response.json()
    # Most recent should be first
    assert data[0]["started_at"] > data[1]["started_at"]
