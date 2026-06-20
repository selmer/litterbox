from unittest.mock import MagicMock, patch

from app.models import AppSetting
from app.settings import TUYA_API_KEY_KEY, TUYA_API_SECRET_KEY


def test_get_tuya_config_masks_secrets(client, db_session, monkeypatch):
    monkeypatch.delenv("TUYA_API_KEY", raising=False)
    monkeypatch.delenv("TUYA_API_SECRET", raising=False)
    db_session.add_all([
        AppSetting(key="tuya.device_id", value="device-1", is_secret=False),
        AppSetting(key=TUYA_API_KEY_KEY, value="plain-key", is_secret=True),
        AppSetting(key=TUYA_API_SECRET_KEY, value="plain-secret", is_secret=True),
    ])
    db_session.commit()

    response = client.get("/admin/tuya-config")

    assert response.status_code == 200
    body = response.json()
    assert body["device_id"] == "device-1"
    assert body["api_key_configured"] is True
    assert body["api_secret_configured"] is True
    assert "plain-key" not in response.text
    assert "plain-secret" not in response.text


def test_put_tuya_config_preserves_blank_secret_and_replaces_new_secret(client, db_session):
    db_session.add_all([
        AppSetting(key=TUYA_API_KEY_KEY, value="existing-key", is_secret=True),
        AppSetting(key=TUYA_API_SECRET_KEY, value="existing-secret", is_secret=True),
    ])
    db_session.commit()

    with patch("app.routers.admin.reload_active_poller", return_value=(True, "reloaded")):
        response = client.put("/admin/tuya-config", json={
            "device_id": "device-2",
            "device_ip": "192.0.2.10",
            "api_region": "eu",
            "api_key": "",
            "api_secret": "new-secret",
        })

    assert response.status_code == 200
    assert response.json()["config"]["api_key_configured"] is True
    assert response.json()["config"]["api_secret_configured"] is True
    assert db_session.get(AppSetting, TUYA_API_KEY_KEY).value == "existing-key"
    assert db_session.get(AppSetting, TUYA_API_SECRET_KEY).value == "new-secret"
    assert "new-secret" not in response.text


def test_test_tuya_config_reports_mocked_success_and_failure(client, db_session):
    db_session.add_all([
        AppSetting(key="tuya.device_id", value="device-1", is_secret=False),
        AppSetting(key=TUYA_API_KEY_KEY, value="key", is_secret=True),
        AppSetting(key=TUYA_API_SECRET_KEY, value="secret", is_secret=True),
    ])
    db_session.commit()

    cloud = MagicMock()
    cloud.getstatus.return_value = {"success": True, "result": []}
    with patch("app.routers.admin.make_cloud", return_value=cloud):
        response = client.post("/admin/tuya-config/test", json={})

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "secret" not in response.text

    with patch("app.routers.admin.make_cloud", side_effect=RuntimeError("boom secret")):
        response = client.post("/admin/tuya-config/test", json={})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "secret" not in response.text
    assert "boom" not in response.text


def test_reload_tuya_config_uses_active_poller(client):
    with patch("app.routers.admin.reload_active_poller", return_value=(False, "reload failed")) as reload_mock:
        response = client.post("/admin/tuya-config/reload")

    assert response.status_code == 200
    assert response.json()["reloaded"] is False
    assert response.json()["message"] == "reload failed"
    reload_mock.assert_called_once_with()
