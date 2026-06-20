from sqlalchemy import inspect

from app.models import AppSetting
from app.settings import (
    TUYA_API_KEY_KEY,
    TUYA_API_SECRET_KEY,
    TUYA_DEVICE_ID_KEY,
    resolve_tuya_config,
    seed_env_tuya_settings,
)


def test_app_settings_table_exists_in_schema(db_engine):
    inspector = inspect(db_engine)

    assert "app_settings" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("app_settings")}
    assert {"key", "value", "is_secret", "updated_at"} <= columns


def test_startup_seeding_copies_env_tuya_config_only_when_missing(db_session, monkeypatch):
    monkeypatch.setenv("TUYA_DEVICE_ID", "env-device")
    monkeypatch.setenv("TUYA_API_KEY", "env-key")
    monkeypatch.setenv("TUYA_API_SECRET", "env-secret")

    seed_env_tuya_settings(db_session)

    assert db_session.get(AppSetting, TUYA_DEVICE_ID_KEY).value == "env-device"
    assert db_session.get(AppSetting, TUYA_API_KEY_KEY).value == "env-key"
    assert db_session.get(AppSetting, TUYA_API_KEY_KEY).is_secret is True
    assert db_session.get(AppSetting, TUYA_API_SECRET_KEY).is_secret is True

    db_session.get(AppSetting, TUYA_API_KEY_KEY).value = "db-key"
    db_session.commit()
    monkeypatch.setenv("TUYA_API_KEY", "new-env-key")

    seed_env_tuya_settings(db_session)

    assert db_session.get(AppSetting, TUYA_API_KEY_KEY).value == "db-key"


def test_settings_resolver_prefers_db_over_env(db_session, monkeypatch):
    monkeypatch.setenv("TUYA_DEVICE_ID", "env-device")
    monkeypatch.setenv("TUYA_API_KEY", "env-key")
    monkeypatch.setenv("TUYA_API_SECRET", "env-secret")
    db_session.add(AppSetting(key=TUYA_API_KEY_KEY, value="db-key", is_secret=True))
    db_session.commit()

    config = resolve_tuya_config(db_session)

    assert config.device_id == "env-device"
    assert config.api_key == "db-key"
    assert config.api_secret == "env-secret"
