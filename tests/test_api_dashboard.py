"""Tests for the /dashboard API endpoint."""
from datetime import datetime, timezone, timedelta

from app.models import Cat, Visit, CleaningCycle


def test_dashboard_empty(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["cats"] == []
    assert data["unidentified_visits_today"] == 0
    assert data["cleaning_cycles_today"] == 0
    assert data["poller_healthy"] is False
    assert "generated_at" in data


def test_dashboard_shows_active_cats(client, db_session):
    db_session.add(Cat(name="Luna", reference_weight_kg=4.0))
    db_session.add(Cat(name="Mochi", reference_weight_kg=6.0))
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()
    names = [c["cat_name"] for c in data["cats"]]
    assert "Luna" in names
    assert "Mochi" in names


def test_dashboard_excludes_inactive_cats(client, db_session):
    db_session.add(Cat(name="Luna", active=False))
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json()["cats"] == []


def test_dashboard_counts_visits_today(client, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    visit_today = Visit(cat_id=cat.id, started_at=today_start + timedelta(hours=1))
    visit_yesterday = Visit(
        cat_id=cat.id,
        started_at=today_start - timedelta(hours=1),
    )
    db_session.add_all([visit_today, visit_yesterday])
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    cat_data = response.json()["cats"][0]
    assert cat_data["visits_today"] == 1


def test_dashboard_counts_cleaning_cycles_today(client, db_session):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    db_session.add(CleaningCycle(started_at=today_start + timedelta(hours=1)))
    db_session.add(CleaningCycle(started_at=today_start - timedelta(hours=1)))
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json()["cleaning_cycles_today"] == 1


def test_dashboard_counts_unidentified_visits_today(client, db_session):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Completed visit with no cat assigned
    db_session.add(
        Visit(
            cat_id=None,
            started_at=today_start + timedelta(hours=1),
            ended_at=today_start + timedelta(hours=1, minutes=2),
        )
    )
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert response.json()["unidentified_visits_today"] == 1


def test_dashboard_time_in_box_today(client, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    db_session.add(
        Visit(
            cat_id=cat.id,
            started_at=today_start + timedelta(hours=1),
            duration_seconds=120,
        )
    )
    db_session.add(
        Visit(
            cat_id=cat.id,
            started_at=today_start + timedelta(hours=2),
            duration_seconds=60,
        )
    )
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    cat_data = response.json()["cats"][0]
    assert cat_data["time_in_box_today_seconds"] == 180
