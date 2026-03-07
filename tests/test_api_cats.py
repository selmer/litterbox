"""Tests for the /cats API endpoints."""
import pytest


def test_create_cat(client):
    resp = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Luna"
    assert data["reference_weight_kg"] == 4.0
    assert data["active"] is True
    assert "id" in data


def test_create_cat_without_reference_weight(client):
    resp = client.post("/cats", json={"name": "Ghost"})
    assert resp.status_code == 200
    assert resp.json()["reference_weight_kg"] is None


def test_list_cats_returns_active_only_by_default(client):
    client.post("/cats", json={"name": "Luna"})
    luna_id = client.post("/cats", json={"name": "Mochi"}).json()["id"]
    client.patch(f"/cats/{luna_id}", json={"active": False})

    resp = client.get("/cats")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Luna" in names
    assert "Mochi" not in names


def test_list_cats_include_inactive(client):
    luna_id = client.post("/cats", json={"name": "Luna"}).json()["id"]
    client.patch(f"/cats/{luna_id}", json={"active": False})

    resp = client.get("/cats", params={"include_inactive": True})
    assert resp.status_code == 200
    assert any(c["name"] == "Luna" for c in resp.json())


def test_get_cat(client):
    cat_id = client.post("/cats", json={"name": "Luna"}).json()["id"]
    resp = client.get(f"/cats/{cat_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Luna"


def test_get_cat_not_found(client):
    resp = client.get("/cats/999")
    assert resp.status_code == 404


def test_update_cat_name(client):
    cat_id = client.post("/cats", json={"name": "Luna"}).json()["id"]
    resp = client.patch(f"/cats/{cat_id}", json={"name": "Luna Updated"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Luna Updated"


def test_update_cat_reference_weight(client):
    cat_id = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0}).json()["id"]
    resp = client.patch(f"/cats/{cat_id}", json={"reference_weight_kg": 4.2})
    assert resp.status_code == 200
    assert resp.json()["reference_weight_kg"] == pytest.approx(4.2)


def test_deactivate_cat(client):
    cat_id = client.post("/cats", json={"name": "Luna"}).json()["id"]
    resp = client.patch(f"/cats/{cat_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


def test_update_cat_not_found(client):
    resp = client.patch("/cats/999", json={"name": "Nobody"})
    assert resp.status_code == 404
