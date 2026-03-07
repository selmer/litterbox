"""Tests for the /visits API endpoints."""
from datetime import datetime, timezone, timedelta


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


def test_get_visit(client):
    cat_id = _make_cat(client)
    visit = _make_visit(client, cat_id)
    visit_id = visit["id"]

    response = client.get(f"/visits/{visit_id}")
    assert response.status_code == 200
    assert response.json()["id"] == visit_id


def test_get_visit_not_found(client):
    response = client.get("/visits/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Visit not found"


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
