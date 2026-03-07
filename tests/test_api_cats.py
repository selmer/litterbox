"""
Tests for the /cats API endpoints.

Functions/scenarios needing owner input:
  - What should happen when a cat's reference_weight_kg is updated to a value
    outside any reasonable range? (Currently no server-side validation.)
  - Should deactivating a cat also affect its historical visits? (Currently it
    does not — visits remain linked.)
"""


def test_create_cat(client):
    response = client.post("/cats", json={"name": "Luna"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Luna"
    assert data["active"] is True
    assert data["reference_weight_kg"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_cat_with_reference_weight(client):
    response = client.post("/cats", json={"name": "Mochi", "reference_weight_kg": 5.5})
    assert response.status_code == 200
    assert response.json()["reference_weight_kg"] == 5.5


def test_list_cats_returns_only_active_by_default(client):
    client.post("/cats", json={"name": "Active"})
    # Create and deactivate a second cat
    r = client.post("/cats", json={"name": "Inactive"})
    cat_id = r.json()["id"]
    client.patch(f"/cats/{cat_id}", json={"active": False})

    response = client.get("/cats")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Active" in names
    assert "Inactive" not in names


def test_list_cats_include_inactive(client):
    client.post("/cats", json={"name": "Active"})
    r = client.post("/cats", json={"name": "Inactive"})
    cat_id = r.json()["id"]
    client.patch(f"/cats/{cat_id}", json={"active": False})

    response = client.get("/cats", params={"include_inactive": True})
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Active" in names
    assert "Inactive" in names


def test_get_cat(client):
    r = client.post("/cats", json={"name": "Luna"})
    cat_id = r.json()["id"]

    response = client.get(f"/cats/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Luna"


def test_get_cat_not_found(client):
    response = client.get("/cats/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_cat_name(client):
    r = client.post("/cats", json={"name": "Luna"})
    cat_id = r.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"name": "Luna Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Luna Updated"


def test_update_cat_reference_weight(client):
    r = client.post("/cats", json={"name": "Luna"})
    cat_id = r.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"reference_weight_kg": 4.2})
    assert response.status_code == 200
    assert response.json()["reference_weight_kg"] == 4.2


def test_update_cat_deactivate(client):
    r = client.post("/cats", json={"name": "Luna"})
    cat_id = r.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"active": False})
    assert response.status_code == 200
    assert response.json()["active"] is False


def test_update_cat_not_found(client):
    response = client.patch("/cats/9999", json={"name": "Ghost"})
    assert response.status_code == 404


def test_create_multiple_cats_appear_in_list(client):
    client.post("/cats", json={"name": "Luna"})
    client.post("/cats", json={"name": "Mochi"})

    response = client.get("/cats")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Luna" in names
    assert "Mochi" in names
