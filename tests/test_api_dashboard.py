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
    assert data["poller_last_successful_at"] is None
    assert data["poller_last_attempted_at"] is None
    assert data["poller_last_error"] is None
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


def test_dashboard_ignores_hard_timeout_duration(client, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    db_session.add_all([
        Visit(
            cat_id=cat.id,
            started_at=today_start + timedelta(hours=1),
            duration_seconds=60,
            duration_source="status_dp",
            duration_is_estimated=False,
        ),
        Visit(
            cat_id=cat.id,
            started_at=today_start + timedelta(hours=2),
            ended_at=today_start + timedelta(hours=2, minutes=30),
            duration_seconds=1800,
            duration_source="hard_timeout",
            duration_is_estimated=True,
            weight_kg=4.2,
        ),
    ])
    db_session.commit()

    response = client.get("/dashboard")

    assert response.status_code == 200
    cat_data = response.json()["cats"][0]
    assert cat_data["time_in_box_today_seconds"] == 60
    assert cat_data["last_visit_duration_seconds"] is None


def test_dashboard_latest_visit_is_deterministic_on_timestamp_tie(client, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0)
    db_session.add(cat)
    db_session.commit()

    started_at = datetime.now(timezone.utc)
    first = Visit(cat_id=cat.id, started_at=started_at, weight_kg=4.0, duration_seconds=30)
    second = Visit(cat_id=cat.id, started_at=started_at, weight_kg=4.2, duration_seconds=40)
    db_session.add_all([first, second])
    db_session.commit()

    response = client.get("/dashboard")
    assert response.status_code == 200
    cats = response.json()["cats"]
    assert len(cats) == 1
    assert cats[0]["last_visit_weight_kg"] == 4.2
    assert cats[0]["last_visit_duration_seconds"] == 40
