"""Tests for the /diagnostics/summary API endpoint."""
from datetime import datetime, timezone, timedelta

import pytest

from app.models import Cat, Visit, VisitDiagnostic
import app.routers.dashboard as dashboard_state


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


def test_diagnostics_summary_empty_state(client):
    response = client.get("/diagnostics/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["poller"]["mode"] == "polling"
    assert data["poller"]["healthy"] is False
    assert data["poller"]["interval_seconds"] == 300
    assert data["open_visits"] == {
        "count": 0,
        "oldest_started_at": None,
        "oldest_age_seconds": None,
        "visits": [],
    }
    assert data["recent_diagnostics"] == []
    assert data["reconciliation"]["reconciliation_attempts"] == 0
    assert data["display"]["refresh_after_seconds"] == 3600
    assert {endpoint["path"] for endpoint in data["endpoints"]} >= {
        "/diagnostics/summary",
        "/display/summary",
        "/visits/{visit_id}/diagnostics",
    }


def test_diagnostics_summary_reports_poller_open_visit_and_reconciliation(client, db_session):
    now = datetime.now(timezone.utc)
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = now - timedelta(minutes=1)
        dashboard_state.last_poll_attempted_at = now
        dashboard_state.last_poll_error = None

    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()
    visit = Visit(
        cat_id=cat.id,
        identified_by="auto",
        started_at=now - timedelta(minutes=7),
        ended_at=None,
        weight_kg=3.83,
        last_weight_at=now - timedelta(minutes=7),
    )
    db_session.add(visit)
    db_session.commit()
    db_session.add_all([
        VisitDiagnostic(
            visit_id=visit.id,
            event_type="reconciliation_attempt",
            payload={"checked_at": now.isoformat()},
            recorded_at=now - timedelta(minutes=2),
        ),
        VisitDiagnostic(
            visit_id=visit.id,
            event_type="report_logs_fetched",
            payload={"log_count": 0},
            recorded_at=now - timedelta(minutes=1),
        ),
    ])
    db_session.commit()

    response = client.get("/diagnostics/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["poller"]["healthy"] is True
    assert data["open_visits"]["count"] == 1
    assert data["open_visits"]["visits"][0]["id"] == visit.id
    assert data["open_visits"]["visits"][0]["weight_kg"] == 3.83
    assert data["open_visits"]["oldest_age_seconds"] >= 0
    assert [item["event_type"] for item in data["recent_diagnostics"]] == [
        "report_logs_fetched",
        "reconciliation_attempt",
    ]
    assert data["reconciliation"]["reconciliation_attempts"] == 1
    assert data["reconciliation"]["report_logs_fetched"] == 1
    assert data["display"]["cats"][0]["name"] == "Plurk"


def test_diagnostics_summary_redacts_sensitive_payload_keys(client, db_session):
    cat = Cat(name="Plurk", reference_weight_kg=3.8)
    db_session.add(cat)
    db_session.commit()
    visit = Visit(
        cat_id=cat.id,
        identified_by="auto",
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        weight_kg=3.8,
    )
    db_session.add(visit)
    db_session.commit()
    db_session.add(
        VisitDiagnostic(
            visit_id=visit.id,
            event_type="cloud_response_error",
            payload={
                "api_key": "test_api_key",
                "nested": {"access_token": "secret-token", "safe": "kept"},
            },
            recorded_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    response = client.get("/diagnostics/summary")

    assert response.status_code == 200
    payload = response.json()["recent_diagnostics"][0]["payload"]
    assert payload["api_key"] == "[redacted]"
    assert payload["nested"]["access_token"] == "[redacted]"
    assert payload["nested"]["safe"] == "kept"
    assert "test_api_key" not in response.text
    assert "secret-token" not in response.text
