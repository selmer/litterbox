"""
Tests for the /visits API endpoints.

Functions/scenarios needing owner input:
  - What is a realistic weight range for visits? (Currently no server-side
    validation — any float is accepted including negative values.)
  - Should weight_history respect cat inactivity, or always include all cats
    that have historical visits regardless of active status?
  - What should list_visits return when limit=0? (Currently returns 0 rows —
    confirm this is the desired behaviour.)
"""
from datetime import datetime, timezone


def _make_cat(client, name="TestCat", weight=4.0):
    r = client.post("/cats", json={"name": name, "reference_weight_kg": weight})
    assert r.status_code == 200
    return r.json()["id"]


def _make_visit(client, cat_id, weight_kg=4.0, duration_seconds=120):
    payload = {
        "cat_id": cat_id,
        "started_at": "2024-01-15T10:00:00Z",
        "duration_seconds": duration_seconds,
        "weight_kg": weight_kg,
    }
    r = client.post("/visits", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


# --- create ---

def test_create_visit(client):
    cat_id = _make_cat(client)
    payload = {
        "cat_id": cat_id,
        "started_at": "2024-01-15T10:00:00Z",
        "duration_seconds": 90,
        "weight_kg": 4.1,
    }
    response = client.post("/visits", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["cat_id"] == cat_id
    assert data["weight_kg"] == 4.1
    assert data["duration_seconds"] == 90
    assert data["identified_by"] == "manual"


# --- list ---

def test_list_visits_empty(client):
    response = client.get("/visits")
    assert response.status_code == 200
    assert response.json() == []


def test_list_visits(client):
    cat_id = _make_cat(client)
    _make_visit(client, cat_id)
    _make_visit(client, cat_id)

    response = client.get("/visits")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_visits_filter_by_cat(client):
    cat_a = _make_cat(client, name="CatA")
    cat_b = _make_cat(client, name="CatB")
    _make_visit(client, cat_a)
    _make_visit(client, cat_b)

    response = client.get("/visits", params={"cat_id": cat_a})
    assert response.status_code == 200
    visits = response.json()
    assert len(visits) == 1
    assert visits[0]["cat_id"] == cat_a


def test_list_visits_respects_limit(client):
    cat_id = _make_cat(client)
    for _ in range(5):
        _make_visit(client, cat_id)

    response = client.get("/visits", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) == 3


# --- get single ---

def test_get_visit(client):
    cat_id = _make_cat(client)
    visit_id = _make_visit(client, cat_id)

    response = client.get(f"/visits/{visit_id}")
    assert response.status_code == 200
    assert response.json()["id"] == visit_id


def test_get_visit_not_found(client):
    response = client.get("/visits/9999")
    assert response.status_code == 404


# --- update ---

def test_update_visit_reassigns_cat(client):
    cat_a = _make_cat(client, name="CatA")
    cat_b = _make_cat(client, name="CatB")
    visit_id = _make_visit(client, cat_a)

    response = client.patch(f"/visits/{visit_id}", json={"cat_id": cat_b})
    assert response.status_code == 200
    data = response.json()
    assert data["cat_id"] == cat_b
    assert data["identified_by"] == "manual"


def test_update_visit_not_found(client):
    response = client.patch("/visits/9999", json={"cat_id": 1})
    assert response.status_code == 404


# --- delete ---

def test_delete_visit(client):
    cat_id = _make_cat(client)
    visit_id = _make_visit(client, cat_id)

    response = client.delete(f"/visits/{visit_id}")
    assert response.status_code == 204

    response = client.get(f"/visits/{visit_id}")
    assert response.status_code == 404


def test_delete_visit_not_found(client):
    response = client.delete("/visits/9999")
    assert response.status_code == 404


# --- weight history ---

def test_weight_history_returns_data_for_active_cats(client):
    cat_id = _make_cat(client, name="Luna", weight=4.0)
    _make_visit(client, cat_id, weight_kg=4.1)

    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cat_name"] == "Luna"
    assert len(data[0]["data"]) == 1
    assert data[0]["data"][0]["weight_kg"] == 4.1


def test_weight_history_filter_by_cat(client):
    cat_a = _make_cat(client, name="CatA")
    cat_b = _make_cat(client, name="CatB")
    _make_visit(client, cat_a)
    _make_visit(client, cat_b)

    response = client.get("/visits/weight-history", params={"cat_id": cat_a})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["cat_name"] == "CatA"


def test_weight_history_empty_for_no_visits(client):
    _make_cat(client, name="Luna")
    response = client.get("/visits/weight-history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["data"] == []
