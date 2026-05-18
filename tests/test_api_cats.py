"""Tests for the /cats API endpoints."""
from datetime import date, timedelta


TINY_GIF_DATA_URL = "data:image/gif;base64,R0lGODlhAQABAAAAACw="


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


def test_create_cat_rejects_blank_name(client):
    response = client.post("/cats", json={"name": "   "})
    assert response.status_code == 422


def test_create_cat_rejects_unrealistic_reference_weight(client):
    response = client.post("/cats", json={"name": "Luna", "reference_weight_kg": 30})
    assert response.status_code == 422


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


def test_upload_cat_photo_accepts_valid_image(client):
    create_resp = client.post("/cats", json={"name": "Luna"})
    cat_id = create_resp.json()["id"]

    response = client.post(f"/cats/{cat_id}/photo", json={"photo_data": TINY_GIF_DATA_URL})
    assert response.status_code == 200
    data = response.json()
    assert data["photo_url"] == f"/uploads/cat_photos/{cat_id}.gif"


def test_upload_cat_photo_rejects_invalid_image_bytes(client):
    create_resp = client.post("/cats", json={"name": "Luna"})
    cat_id = create_resp.json()["id"]

    response = client.post(
        f"/cats/{cat_id}/photo",
        json={"photo_data": "data:image/jpeg;base64,bm90IGFuIGltYWdl"},
    )
    assert response.status_code == 400


def test_delete_cat_photo_clears_photo_url(client):
    create_resp = client.post("/cats", json={"name": "Luna"})
    cat_id = create_resp.json()["id"]
    client.post(f"/cats/{cat_id}/photo", json={"photo_data": TINY_GIF_DATA_URL})

    response = client.delete(f"/cats/{cat_id}/photo")
    assert response.status_code == 200
    assert response.json()["photo_url"] is None


def test_create_cat_with_birth_date(client):
    response = client.post("/cats", json={"name": "Plurk", "birth_date": "2020-05-18"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Plurk"
    assert data["birth_date"] == "2020-05-18"


def test_update_cat_birth_date(client):
    create_resp = client.post("/cats", json={"name": "Plurk"})
    cat_id = create_resp.json()["id"]

    response = client.patch(f"/cats/{cat_id}", json={"birth_date": "2020-05-18"})

    assert response.status_code == 200
    assert response.json()["birth_date"] == "2020-05-18"


def test_create_cat_event(client):
    cat_id = client.post("/cats", json={"name": "Plurk"}).json()["id"]
    occurred_at = '2026-05-18'

    response = client.post(
        f"/cats/{cat_id}/events",
        json={
            "event_type": "vet_visit",
            "occurred_at": occurred_at,
            "title": "Annual checkup",
            "notes": "Everything looked good.",
            "cost_amount": "45.50",
            "cost_currency": "eur",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["cat_id"] == cat_id
    assert data["event_type"] == "vet_visit"
    assert data["occurred_at"] == occurred_at
    assert data["title"] == "Annual checkup"
    assert data["notes"] == "Everything looked good."
    assert data["cost_amount"] == "45.50"
    assert data["cost_currency"] == "EUR"
    assert "created_at" in data
    assert "updated_at" in data


def test_list_cat_events_sorts_newest_first(client):
    cat_id = client.post("/cats", json={"name": "Plurk"}).json()["id"]
    older = date(2026, 5, 17)
    newer = older + timedelta(days=1)
    client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "other", "occurred_at": older.isoformat(), "title": "Older event"},
    )
    client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "milestone", "occurred_at": newer.isoformat(), "title": "Newer event"},
    )

    response = client.get(f"/cats/{cat_id}/events")

    assert response.status_code == 200
    assert [event["title"] for event in response.json()] == ["Newer event", "Older event"]


def test_update_cat_event(client):
    cat_id = client.post("/cats", json={"name": "Plurk"}).json()["id"]
    event = client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "other", "occurred_at": '2026-05-18', "title": "Initial"},
    ).json()

    response = client.patch(
        f"/cats/{cat_id}/events/{event['id']}",
        json={"title": "Updated", "cost_amount": "12.00"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["cost_amount"] == "12.00"


def test_delete_cat_event(client):
    cat_id = client.post("/cats", json={"name": "Plurk"}).json()["id"]
    event = client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "other", "occurred_at": '2026-05-18', "title": "Delete me"},
    ).json()

    response = client.delete(f"/cats/{cat_id}/events/{event['id']}")

    assert response.status_code == 204
    assert client.get(f"/cats/{cat_id}/events").json() == []


def test_cat_events_reject_missing_cat(client):
    response = client.get("/cats/9999/events")

    assert response.status_code == 404
    assert response.json()["detail"] == "Cat not found"


def test_cat_event_validation(client):
    cat_id = client.post("/cats", json={"name": "Plurk"}).json()["id"]

    blank_title = client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "other", "occurred_at": '2026-05-18', "title": "   "},
    )
    invalid_type = client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "nap", "occurred_at": '2026-05-18', "title": "Nap"},
    )
    negative_cost = client.post(
        f"/cats/{cat_id}/events",
        json={
            "event_type": "vet_visit",
            "occurred_at": '2026-05-18',
            "title": "Vet",
            "cost_amount": "-1.00",
        },
    )
    datetime_value = client.post(
        f"/cats/{cat_id}/events",
        json={"event_type": "other", "occurred_at": "2026-05-18T14:30:00Z", "title": "Timestamp"},
    )

    assert blank_title.status_code == 422
    assert invalid_type.status_code == 422
    assert negative_cost.status_code == 422
    assert datetime_value.status_code == 422
