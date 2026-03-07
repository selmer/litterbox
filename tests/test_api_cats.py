"""Tests for the /cats API endpoints."""


def test_create_cat(client):
    response = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Luna"
    assert data["reference_weight_kg"] == 4.0
    assert data["active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_cat_without_reference_weight(client):
    response = client.post("/cats", json={"name": "Ghost"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ghost"
    assert data["reference_weight_kg"] is None


def test_list_cats_returns_active_only_by_default(client):
    client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0})
    cat_resp = client.post("/cats", json={"name": "Mochi", "reference_weight_kg": 6.0})
    cat_id = cat_resp.json()["id"]
    # Deactivate Mochi
    client.patch(f"/cats/{cat_id}", json={"active": False})

    response = client.get("/cats")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Luna" in names
    assert "Mochi" not in names


def test_list_cats_include_inactive(client):
    client.post("/cats", json={"name": "Luna"})
    cat_resp = client.post("/cats", json={"name": "Mochi"})
    client.patch(f"/cats/{cat_resp.json()['id']}", json={"active": False})

    response = client.get("/cats?include_inactive=true")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Luna" in names
    assert "Mochi" in names


def test_list_cats_empty(client):
    response = client.get("/cats")
    assert response.status_code == 200
    assert response.json() == []


def test_get_cat(client):
    create_resp = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0})
    cat_id = create_resp.json()["id"]

    response = client.get(f"/cats/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Luna"


def test_get_cat_not_found(client):
    response = client.get("/cats/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Cat not found"


def test_update_cat_name(client):
    create_resp = client.post("/cats", json={"name": "Luna"})
    cat_id = create_resp.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"name": "Luna II"})
    assert response.status_code == 200
    assert response.json()["name"] == "Luna II"


def test_update_cat_reference_weight(client):
    create_resp = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 4.0})
    cat_id = create_resp.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"reference_weight_kg": 4.2})
    assert response.status_code == 200
    assert response.json()["reference_weight_kg"] == 4.2


def test_deactivate_cat(client):
    create_resp = client.post("/cats", json={"name": "Luna"})
    cat_id = create_resp.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"active": False})
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_update_cat_not_found(client):
    response = client.patch("/cats/9999", json={"name": "Ghost"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Cat not found"
