"""Tests for the /visits API endpoints."""
from datetime import datetime, timezone, timedelta


def _now():
    return datetime.now(timezone.utc).isoformat()


def _make_cat(client, name="Luna", weight=4.0):
    return client.post("/cats", json={"name": name, "reference_weight_kg": weight}).json()


def _make_visit(client, cat_id, started_at=None, duration=120, weight=4.0):
    return client.post("/visits", json={
        "cat_id": cat_id,
        "started_at": started_at or _now(),
        "duration_seconds": duration,
        "weight_kg": weight,
    })


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_visit(client):
    cat = _make_cat(client)
    resp = _make_visit(client, cat["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert data["cat_id"] == cat["id"]
    assert data["identified_by"] == "manual"
    assert data["duration_seconds"] == 120
    assert data["weight_kg"] == 4.0


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_list_visits(client):
    cat = _make_cat(client)
    _make_visit(client, cat["id"])
    _make_visit(client, cat["id"])
    resp = client.get("/visits")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_visits_filter_by_cat(client):
    cat1 = _make_cat(client, "Luna")
    cat2 = _make_cat(client, "Mochi", 6.0)
    _make_visit(client, cat1["id"])
    _make_visit(client, cat2["id"])

    resp = client.get("/visits", params={"cat_id": cat1["id"]})
    assert resp.status_code == 200
    visits = resp.json()
    assert len(visits) == 1
    assert visits[0]["cat_id"] == cat1["id"]


def test_list_visits_limit(client):
    cat = _make_cat(client)
    for _ in range(5):
        _make_visit(client, cat["id"])
    resp = client.get("/visits", params={"limit": 3})
    assert len(resp.json()) == 3


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------

def test_get_visit(client):
    cat = _make_cat(client)
    visit_id = _make_visit(client, cat["id"]).json()["id"]
    resp = client.get(f"/visits/{visit_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == visit_id


def test_get_visit_not_found(client):
    resp = client.get("/visits/999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def test_update_visit_cat_assignment(client):
    cat1 = _make_cat(client, "Luna")
    cat2 = _make_cat(client, "Mochi", 6.0)
    visit_id = _make_visit(client, cat1["id"]).json()["id"]

    resp = client.patch(f"/visits/{visit_id}", json={"cat_id": cat2["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["cat_id"] == cat2["id"]
    assert data["identified_by"] == "manual"


def test_update_visit_not_found(client):
    resp = client.patch("/visits/999", json={"cat_id": 1})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_visit(client):
    cat = _make_cat(client)
    visit_id = _make_visit(client, cat["id"]).json()["id"]
    resp = client.delete(f"/visits/{visit_id}")
    assert resp.status_code == 204
    assert client.get(f"/visits/{visit_id}").status_code == 404


def test_delete_visit_not_found(client):
    resp = client.delete("/visits/999")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Weight history
# ---------------------------------------------------------------------------

def test_weight_history_returns_data(client):
    cat = _make_cat(client, "Luna", 4.0)
    _make_visit(client, cat["id"], weight=4.1)
    _make_visit(client, cat["id"], weight=4.2)

    resp = client.get("/visits/weight-history")
    assert resp.status_code == 200
    histories = resp.json()
    assert len(histories) == 1
    assert histories[0]["cat_name"] == "Luna"
    assert len(histories[0]["data"]) == 2


def test_weight_history_filter_by_cat(client):
    cat1 = _make_cat(client, "Luna", 4.0)
    cat2 = _make_cat(client, "Mochi", 6.0)
    _make_visit(client, cat1["id"], weight=4.0)
    _make_visit(client, cat2["id"], weight=6.0)

    resp = client.get("/visits/weight-history", params={"cat_id": cat1["id"]})
    assert resp.status_code == 200
    histories = resp.json()
    assert len(histories) == 1
    assert histories[0]["cat_name"] == "Luna"
