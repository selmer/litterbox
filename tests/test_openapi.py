"""Smoke tests for FastAPI OpenAPI/Swagger support."""


def test_openapi_json_is_available(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert data["openapi"].startswith("3.")
    assert data["info"]["title"] == "Litterbox API"


def test_openapi_json_includes_core_routes(client):
    response = client.get("/openapi.json")

    paths = response.json()["paths"]
    assert "/cats" in paths
    assert "/visits" in paths
    assert "/dashboard" in paths
    assert "/display/summary" in paths
