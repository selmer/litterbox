"""Tests for the /visits API endpoints."""
from datetime import datetime, timezone, timedelta

from app.models import Visit, VisitDiagnostic


def _make_cat(client, name="Luna", weight=4.0):
    resp = client.post("/cats", json={"name": name, "reference_weight_kg": weight})
    assert resp.status_code == 200
    return resp.json()["id"]


def _make_visit(client, cat_id, started_at=None, duration_seconds=60, weight_kg=4.1):
    if started_at is None:
        started_at = datetime.now(timezone.utc).isoformat()
    resp = client.post(
        "/visits",
        json={
            "cat_id": cat_id,
            "started_at": started_at,
            "duration_seconds": duration_seconds,
            "weight_kg": weight_kg,
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_create_visit(client):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)

    assert visit["cat_id"] == cat_id
    assert visit["weight_kg"] == 4.1
    assert visit["duration_seconds"] == 60
    assert visit["identified_by"] == "manual"
    assert visit["duration_source"] == "manual"
    assert visit["duration_is_estimated"] is False
    assert visit["ended_at"] is not None


def test_create_visit_rejects_unknown_cat(client):
    response = client.post(
        "/visits",
        json={
            "cat_id": 9999,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 60,
            "weight_kg": 4.1,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cat not found"


def test_create_visit_rejects_invalid_values(client):
    cat_id = _make_cat(client)
    response = client.post(
        "/visits",
        json={
            "cat_id": cat_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": -1,
            "weight_kg": -4.1,
        },
    )
    assert response.status_code == 422


def test_list_visits(client):
    cat_id = _make_cat(client)
    _make_visit(client, cat_id)
    _make_visit(client, cat_id)

    response = client.get("/visits")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_visits_filter_by_cat(client):
    cat1 = _make_cat(client, name="Luna")
    cat2 = _make_cat(client, name="Mochi", weight=6.0)
    _make_visit(client, cat1)
    _make_visit(client, cat2)

    response = client.get(f"/visits?cat_id={cat1}")
    assert response.status_code == 200
    visits = response.json()
    assert len(visits) == 1
    assert visits[0]["cat_id"] == cat1


def test_list_visits_empty(client):
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == []


def test_list_visits_limit(client):
    cat_id = _make_cat(client)
    for _ in range(5):
        _make_visit(client, cat_id)

    response = client.get("/visits?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_visits_offset(client):
    cat_id = _make_cat(client)
    # Create 5 visits with distinct timestamps so ordering is deterministic
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        _make_visit(client, cat_id, started_at=(base + timedelta(minutes=i)).isoformat())

    # First page
    page1 = client.get("/visits?limit=3&offset=0").json()
    assert len(page1) == 3

    # Second page
    page2 = client.get("/visits?limit=3&offset=3").json()
    assert len(page2) == 2

    # No overlap
    ids1 = {v["id"] for v in page1}
    ids2 = {v["id"] for v in page2}
    assert ids1.isdisjoint(ids2)


def test_list_visits_offset_beyond_end(client):
    cat_id = _make_cat(client)
    _make_visit(client, cat_id)

    response = client.get("/visits?limit=10&offset=100")
    assert response.status_code == 200
    assert response.json() == []


def test_list_visits_rejects_negative_offset(client):
    response = client.get("/visits?offset=-1")
    assert response.status_code == 422


def test_list_visits_unidentified(client):
    cat_id = _make_cat(client)
    _make_visit(client, cat_id)
    # Create a second visit and clear its cat_id to simulate unidentified
    temp_cat = _make_cat(client, name="Temp")
    visit = _make_visit(client, temp_cat)
    client.patch(f"/visits/{visit['id']}", json={"cat_id": None})

    response = client.get("/visits?unidentified=true")
    assert response.status_code == 200
    visits = response.json()
    assert len(visits) == 1
    assert visits[0]["cat_id"] is None


def test_list_visits_unidentified_false_returns_all(client):
    cat_id = _make_cat(client)
    _make_visit(client, cat_id)
    _make_visit(client, cat_id)

    response = client.get("/visits?unidentified=false")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_visit(client):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)
    visit_id = visit["id"]

    response = client.get(f"/visits/{visit_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == visit_id
    assert data["duration_source"] == "manual"
    assert data["duration_is_estimated"] is False


def test_get_visit_diagnostics(client, db_session):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)
    first = VisitDiagnostic(
        visit_id=visit["id"],
        event_type="reconciliation_attempt",
        payload={"step": 1},
        recorded_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    second = VisitDiagnostic(
        visit_id=visit["id"],
        event_type="pending_retry",
        payload={"reason": "no_completion_match"},
        recorded_at=datetime(2024, 1, 1, 12, 1, tzinfo=timezone.utc),
    )
    db_session.add_all([second, first])
    db_session.commit()

    response = client.get(f"/visits/{visit['id']}/diagnostics")

    assert response.status_code == 200
    data = response.json()
    assert [item["event_type"] for item in data] == ["reconciliation_attempt", "pending_retry"]
    assert data[0]["payload"] == {"step": 1}


def test_get_visit_diagnostics_not_found(client):
    response = client.get("/visits/9999/diagnostics")

    assert response.status_code == 404
    assert response.json()["detail"] == "Visit not found"


def test_get_visit_not_found(client):
    response = client.get("/visits/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Visit not found"


def test_legacy_unknown_timeout_visit_returns_unknown_duration(client, db_session):
    cat_id = _make_cat(client)
    started_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    visit = Visit(
        cat_id=cat_id,
        identified_by="auto",
        started_at=started_at,
        ended_at=started_at + timedelta(minutes=30),
        duration_seconds=1800,
        duration_source="unknown",
        duration_is_estimated=False,
        weight_kg=4.1,
    )
    db_session.add(visit)
    db_session.commit()

    response = client.get(f"/visits/{visit.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["duration_seconds"] is None
    assert data["duration_source"] == "unknown"
    assert data["duration_is_estimated"] is False


def test_hard_timeout_visit_returns_unknown_duration(client, db_session):
    cat_id = _make_cat(client)
    started_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    visit = Visit(
        cat_id=cat_id,
        identified_by="auto",
        started_at=started_at,
        ended_at=started_at + timedelta(minutes=30),
        duration_seconds=1800,
        duration_source="hard_timeout",
        duration_is_estimated=True,
        weight_kg=4.1,
    )
    db_session.add(visit)
    db_session.commit()

    response = client.get(f"/visits/{visit.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["duration_seconds"] is None
    assert data["duration_source"] == "hard_timeout"
    assert data["duration_is_estimated"] is True


def test_update_visit_reassigns_cat(client):
    cat1 = _make_cat(client, name="Luna")
    cat2 = _make_cat(client, name="Mochi", weight=6.0)
    visit = _make_visit(client, cat1)
    visit_id = visit["id"]

    response = client.patch(f"/visits/{visit_id}", json={"cat_id": cat2})
    assert response.status_code == 200
    data = response.json()
    assert data["cat_id"] == cat2
    assert data["identified_by"] == "manual"


def test_update_visit_rejects_unknown_cat(client):
    cat1 = _make_cat(client, name="Luna")
    visit = _make_visit(client, cat1)

    response = client.patch(f"/visits/{visit['id']}", json={"cat_id": 9999})
    assert response.status_code == 400
    assert response.json()["detail"] == "Cat not found"


def test_update_visit_can_mark_unidentified(client):
    cat1 = _make_cat(client, name="Luna")
    visit = _make_visit(client, cat1)

    response = client.patch(f"/visits/{visit['id']}", json={"cat_id": None})
    assert response.status_code == 200
    data = response.json()
    assert data["cat_id"] is None
    assert data["identified_by"] is None


def test_update_visit_not_found(client):
    response = client.patch("/visits/9999", json={"cat_id": 1})
    assert response.status_code == 404


def test_delete_visit(client):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)
    visit_id = visit["id"]

    response = client.delete(f"/visits/{visit_id}")
    assert response.status_code == 204

    response = client.get(f"/visits/{visit_id}")
    assert response.status_code == 404


def test_delete_visit_not_found(client):
    response = client.delete("/visits/9999")
    assert response.status_code == 404


def test_deleted_visit_is_removed_from_weight_history(client):
    cat_id = _make_cat(client, name="Luna")
    visit = _make_visit(client, cat_id, weight_kg=4.25)
    visit_id = visit["id"]

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    assert response.json()[0]["data"][0]["visit_id"] == visit_id

    response = client.delete(f"/visits/{visit_id}")
    assert response.status_code == 204

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    assert response.json()[0]["data"] == []


def test_unidentified_visit_is_removed_from_weight_history(client):
    cat_id = _make_cat(client, name="Luna")
    visit = _make_visit(client, cat_id, weight_kg=4.25)
    visit_id = visit["id"]

    response = client.patch(f"/visits/{visit_id}", json={"cat_id": None})
    assert response.status_code == 200

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    assert response.json()[0]["data"] == []


def test_reassigned_visit_moves_between_weight_history_series(client):
    cat1 = _make_cat(client, name="Luna")
    cat2 = _make_cat(client, name="Mochi", weight=6.0)
    visit = _make_visit(client, cat1, weight_kg=4.25)
    visit_id = visit["id"]

    response = client.patch(f"/visits/{visit_id}", json={"cat_id": cat2})
    assert response.status_code == 200

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    by_cat = {series["cat_id"]: series["data"] for series in response.json()}
    assert by_cat[cat1] == []
    assert by_cat[cat2][0]["visit_id"] == visit_id
    assert by_cat[cat2][0]["weight_kg"] == 4.25


def test_weight_history_returns_data_for_active_cats(client):
    cat_id = _make_cat(client, name="Luna")
    now = datetime.now(timezone.utc)
    _make_visit(client, cat_id, started_at=now.isoformat(), weight_kg=4.1)

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["cat_name"] == "Luna"
    assert len(result[0]["data"]) == 1
    assert result[0]["data"][0]["weight_kg"] == 4.1


def test_weight_history_excludes_inactive_cats(client):
    cat_id = _make_cat(client, name="Luna")
    _make_visit(client, cat_id)
    # Deactivate the cat
    client.patch(f"/cats/{cat_id}", json={"active": False})

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_weight_history_respects_date_range(client):
    cat_id = _make_cat(client, name="Luna")
    old_date = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    recent_date = datetime.now(timezone.utc).isoformat()

    _make_visit(client, cat_id, started_at=old_date)
    _make_visit(client, cat_id, started_at=recent_date)

    from_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    response = client.get(
        "/visits/weight-history",
        params={"from_date": from_date},  # ✅ properly encoded
    )

    assert response.status_code == 200
    result = response.json()
    # Only the recent visit should be included
    assert len(result[0]["data"]) == 1


def test_weight_history_rejects_inverted_date_range(client):
    response = client.get(
        "/visits/weight-history",
        params={
            "from_date": datetime(2024, 2, 1, tzinfo=timezone.utc).isoformat(),
            "to_date": datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 400


def test_update_visit_edits_time_duration_weight_and_confidence(client, db_session):
    cat_id = _make_cat(client, name="Luna")
    visit = _make_visit(client, cat_id, duration_seconds=60, weight_kg=4.1)
    new_started = datetime(2024, 1, 2, 13, 30, tzinfo=timezone.utc)

    response = client.patch(
        f"/visits/{visit['id']}",
        json={
            "started_at": new_started.isoformat(),
            "duration_seconds": 125,
            "weight_kg": 4.25,
            "weight_confidence": "ignored",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["started_at"] == new_started.isoformat().replace("+00:00", "Z")
    assert data["ended_at"] == (new_started + timedelta(seconds=125)).isoformat().replace("+00:00", "Z")
    assert data["duration_seconds"] == 125
    assert data["duration_source"] == "manual"
    assert data["duration_is_estimated"] is False
    assert data["weight_kg"] == 4.25
    assert data["weight_confidence"] == "ignored"
    assert data["weight_confidence_reason"] == "operator_ignored"

    diagnostics = client.get(f"/visits/{visit['id']}/diagnostics").json()
    assert diagnostics[-1]["event_type"] == "manual_edit"
    assert diagnostics[-1]["payload"]["changes"]["weight_kg"]["to"] == 4.25


def test_update_visit_rejects_invalid_edit_values(client):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)

    response = client.patch(
        f"/visits/{visit['id']}",
        json={"duration_seconds": 0, "weight_kg": -1, "weight_confidence": "wild"},
    )

    assert response.status_code == 422


def test_weight_history_excludes_ignored_weights_by_default(client, db_session):
    cat_id = _make_cat(client, name="Luna")
    normal = _make_visit(client, cat_id, weight_kg=4.1)
    ignored = _make_visit(client, cat_id, weight_kg=9.9)
    client.patch(f"/visits/{ignored['id']}", json={"weight_confidence": "ignored"})

    response = client.get("/visits/weight-history")

    assert response.status_code == 200
    points = response.json()[0]["data"]
    assert [point["visit_id"] for point in points] == [normal["id"]]
    assert points[0]["weight_confidence"] == "normal"

    response = client.get("/visits/weight-history?include_ignored=true")
    assert response.status_code == 200
    assert [point["visit_id"] for point in response.json()[0]["data"]] == [normal["id"], ignored["id"]]


def test_create_visit_accepts_confidence_state(client):
    cat_id = _make_cat(client)
    response = client.post(
        "/visits",
        json={
            "cat_id": cat_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 60,
            "weight_kg": 4.1,
            "weight_confidence": "suspect",
        },
    )

    assert response.status_code == 201
    assert response.json()["weight_confidence"] == "suspect"
    assert response.json()["weight_confidence_reason"] == "manual"
