"""Tests for the /display/summary API endpoint."""
from datetime import datetime, timezone, timedelta

import pytest

from app.models import Cat, CleaningCycle, Visit
import app.routers.dashboard as dashboard_state
import app.routers.display as display_router


@pytest.fixture(autouse=True)
def reset_dashboard_state():
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = None
        dashboard_state.last_poll_attempted_at = None
        dashboard_state.last_poll_error = None
        dashboard_state.update_mode = "polling"
    yield
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = None
        dashboard_state.last_poll_attempted_at = None
        dashboard_state.last_poll_error = None
        dashboard_state.update_mode = "polling"


def _mark_poller_healthy():
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
        dashboard_state.last_poll_error = None


def test_display_summary_empty(client):
    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["refresh_after_seconds"] == 3600
    assert data["status"]["label"] == "Polling"
    assert data["status"]["healthy"] is False
    assert data["latest_visit"] is None
    assert data["today"] == {
        "visits": 0,
        "time_in_box_seconds": 0,
        "cleaning_cycles": 0,
        "unidentified_visits": 0,
    }
    assert data["chart"] is None
    assert data["cats"] == []
    assert data["alert"] == "Poller has not reported successfully yet."


def test_display_summary_returns_latest_visit_today_counts_and_chart(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=20), duration_seconds=280, duration_source="manual", duration_is_estimated=False, weight_kg=3.72),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=10), duration_seconds=290, duration_source="manual", duration_is_estimated=False, weight_kg=3.78),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(minutes=30), duration_seconds=300, duration_source="manual", duration_is_estimated=False, weight_kg=3.76),
        CleaningCycle(started_at=now - timedelta(minutes=5)),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["status"]["healthy"] is True
    assert data["status"]["message"] is None
    assert data["latest_visit"]["cat_name"] == "Plurk"
    assert data["latest_visit"]["identified"] is True
    assert data["latest_visit"]["identified_by"] == "auto"
    assert data["latest_visit"]["duration_seconds"] == 300
    assert data["latest_visit"]["weight_kg"] == 3.76
    assert data["today"]["visits"] == 1
    assert data["today"]["time_in_box_seconds"] == 300
    assert data["today"]["cleaning_cycles"] == 1
    assert data["today"]["unidentified_visits"] == 0
    assert len(data["cats"]) == 1
    cat_summary = data["cats"][0]
    assert cat_summary["name"] == "Plurk"
    assert cat_summary["visits_today"] == 1
    assert cat_summary["last_weight_kg"] == 3.76
    assert cat_summary["latest_weight_kg"] == 3.76
    assert cat_summary["latest_weight_at"] is not None
    assert cat_summary["one_month_ago"]["weight_kg"] == 3.72
    assert cat_summary["one_month_ago"]["delta_kg"] == 0.04
    assert cat_summary["three_months_ago"] is None
    assert cat_summary["sparkline"] == [3.72, 3.78, 3.76]
    assert data["alert"] is None

    chart = data["chart"]
    assert chart["label"] == "30d weight"
    assert chart["unit"] == "kg"
    assert chart["min_kg"] == 3.72
    assert chart["max_kg"] == 3.78
    assert [point["weight_kg"] for point in chart["points"]] == [3.72, 3.78, 3.76]
    assert [point["date"] for point in chart["points"]] == sorted(point["date"] for point in chart["points"])


def test_display_summary_unidentified_latest_visit_uses_unknown_cat_and_alert(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=8), duration_seconds=280, weight_kg=3.72),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=3), duration_seconds=290, weight_kg=3.78),
        Visit(
            cat_id=None,
            identified_by=None,
            started_at=now - timedelta(minutes=15),
            ended_at=now - timedelta(minutes=10),
            duration_seconds=120,
            weight_kg=3.5,
        ),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["latest_visit"]["cat_name"] == "Unknown cat"
    assert data["latest_visit"]["identified"] is False
    assert data["latest_visit"]["identified_by"] is None
    assert data["today"]["unidentified_visits"] == 1
    assert data["alert"] == "Latest visit is unidentified."
    assert [point["weight_kg"] for point in data["chart"]["points"]] == [3.72, 3.78]


def test_display_summary_ignores_hard_timeout_duration(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add(
        Visit(
            cat_id=cat.id,
            identified_by="auto",
            started_at=now - timedelta(minutes=35),
            ended_at=now - timedelta(minutes=5),
            duration_seconds=1800,
            duration_source="hard_timeout",
            duration_is_estimated=True,
            weight_kg=3.76,
        )
    )
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["latest_visit"]["duration_seconds"] is None
    assert data["today"]["time_in_box_seconds"] == 0


def test_display_summary_ignores_legacy_unknown_timeout_duration(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add(
        Visit(
            cat_id=cat.id,
            identified_by="auto",
            started_at=now - timedelta(minutes=35),
            ended_at=now - timedelta(minutes=5),
            duration_seconds=1800,
            duration_source="unknown",
            duration_is_estimated=False,
            weight_kg=3.76,
        )
    )
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["latest_visit"]["duration_seconds"] is None
    assert data["today"]["time_in_box_seconds"] == 0


def test_display_summary_unhealthy_poller_uses_error_alert(client, db_session):
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()
    db_session.add(
        Visit(
            cat_id=cat.id,
            identified_by="manual",
            started_at=datetime.now(timezone.utc),
            duration_seconds=60,
            weight_kg=3.8,
        )
    )
    db_session.commit()
    with dashboard_state._poll_lock:
        dashboard_state.last_poll_error = "permission denied"

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["status"]["healthy"] is False
    assert data["status"]["message"] == "permission denied"
    assert data["alert"] == "permission denied"


def test_display_summary_returns_null_chart_when_latest_cat_has_too_little_data(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()
    db_session.add(
        Visit(
            cat_id=cat.id,
            identified_by="auto",
            started_at=datetime.now(timezone.utc),
            duration_seconds=60,
            weight_kg=3.8,
        )
    )
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    assert response.json()["chart"] is None


def test_display_summary_excludes_chart_points_older_than_30_days(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=45), duration_seconds=60, weight_kg=3.6),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=2), duration_seconds=60, weight_kg=3.7),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=1), duration_seconds=60, weight_kg=3.8),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    weights = [point["weight_kg"] for point in response.json()["chart"]["points"]]
    assert weights == [3.7, 3.8]


def test_display_summary_returns_weight_comparisons_for_multiple_cats(client, db_session, monkeypatch):
    _mark_poller_healthy()
    now = datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(display_router, "_utc_now", lambda: now)

    plurk = Cat(name="Plurk", reference_weight_kg=3.8)
    griezeltje = Cat(name="Griezeltje", reference_weight_kg=4.4)
    db_session.add_all([plurk, griezeltje])
    db_session.commit()

    db_session.add_all([
        Visit(cat_id=plurk.id, identified_by="auto", started_at=now - timedelta(days=92), duration_seconds=60, weight_kg=3.91),
        Visit(cat_id=plurk.id, identified_by="auto", started_at=now - timedelta(days=29), duration_seconds=60, weight_kg=3.77),
        Visit(cat_id=plurk.id, identified_by="auto", started_at=now - timedelta(hours=2), duration_seconds=60, weight_kg=3.76),
        Visit(cat_id=griezeltje.id, identified_by="auto", started_at=now - timedelta(days=87), duration_seconds=60, weight_kg=4.39),
        Visit(cat_id=griezeltje.id, identified_by="auto", started_at=now - timedelta(days=31), duration_seconds=60, weight_kg=4.40),
        Visit(cat_id=griezeltje.id, identified_by="auto", started_at=now - timedelta(hours=1), duration_seconds=60, weight_kg=4.42),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    cats = {cat["name"]: cat for cat in response.json()["cats"]}
    assert cats["Plurk"]["visits_today"] == 1
    assert cats["Plurk"]["latest_weight_kg"] == 3.76
    assert cats["Plurk"]["one_month_ago"]["weight_kg"] == 3.77
    assert cats["Plurk"]["one_month_ago"]["delta_kg"] == -0.01
    assert cats["Plurk"]["three_months_ago"]["weight_kg"] == 3.91
    assert cats["Plurk"]["three_months_ago"]["delta_kg"] == -0.15
    assert cats["Griezeltje"]["visits_today"] == 1
    assert cats["Griezeltje"]["latest_weight_kg"] == 4.42
    assert cats["Griezeltje"]["one_month_ago"]["delta_kg"] == 0.02
    assert cats["Griezeltje"]["three_months_ago"]["delta_kg"] == 0.03


def test_display_summary_returns_null_comparisons_outside_tolerance(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=55), duration_seconds=60, weight_kg=3.7),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(hours=1), duration_seconds=60, weight_kg=3.8),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    cat_summary = response.json()["cats"][0]
    assert cat_summary["latest_weight_kg"] == 3.8
    assert cat_summary["one_month_ago"] is None
    assert cat_summary["three_months_ago"] is None


def test_display_summary_excludes_ignored_weights_from_cat_summaries_and_chart(client, db_session):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    now = datetime.now(timezone.utc)
    db_session.add_all([
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=20), duration_seconds=280, duration_source="manual", duration_is_estimated=False, weight_kg=3.72),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(days=2), duration_seconds=290, duration_source="manual", duration_is_estimated=False, weight_kg=3.80),
        Visit(cat_id=cat.id, identified_by="auto", started_at=now - timedelta(minutes=30), duration_seconds=300, duration_source="manual", duration_is_estimated=False, weight_kg=9.99, weight_confidence="ignored"),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["cats"][0]["latest_weight_kg"] == 3.8
    assert [point["weight_kg"] for point in data["chart"]["points"]] == [3.72, 3.8]


def test_display_summary_today_uses_local_day_boundary(client, db_session, monkeypatch):
    _mark_poller_healthy()
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()

    monkeypatch.setattr(
        display_router,
        "_utc_now",
        lambda: datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add_all([
        Visit(
            cat_id=cat.id,
            identified_by="auto",
            started_at=datetime(2026, 6, 7, 21, 30, tzinfo=timezone.utc),
            duration_seconds=60,
            duration_source="manual",
            duration_is_estimated=False,
            weight_kg=3.7,
        ),
        Visit(
            cat_id=cat.id,
            identified_by="auto",
            started_at=datetime(2026, 6, 7, 22, 30, tzinfo=timezone.utc),
            duration_seconds=120,
            duration_source="manual",
            duration_is_estimated=False,
            weight_kg=3.8,
        ),
        Visit(
            cat_id=None,
            started_at=datetime(2026, 6, 7, 22, 45, tzinfo=timezone.utc),
            ended_at=datetime(2026, 6, 7, 22, 50, tzinfo=timezone.utc),
        ),
        CleaningCycle(started_at=datetime(2026, 6, 7, 22, 40, tzinfo=timezone.utc)),
        CleaningCycle(started_at=datetime(2026, 6, 7, 21, 40, tzinfo=timezone.utc)),
    ])
    db_session.commit()

    response = client.get("/display/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["today"]["visits"] == 2
    assert data["today"]["time_in_box_seconds"] == 120
    assert data["today"]["cleaning_cycles"] == 1
    assert data["today"]["unidentified_visits"] == 1
    assert data["cats"][0]["visits_today"] == 1

