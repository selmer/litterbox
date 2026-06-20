import os
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import AppSetting

TUYA_DEVICE_ID_KEY = "tuya.device_id"
TUYA_DEVICE_IP_KEY = "tuya.device_ip"
TUYA_API_KEY_KEY = "tuya.api_key"
TUYA_API_SECRET_KEY = "tuya.api_secret"
TUYA_API_REGION_KEY = "tuya.api_region"

TUYA_SETTING_KEYS = {
    TUYA_DEVICE_ID_KEY,
    TUYA_DEVICE_IP_KEY,
    TUYA_API_KEY_KEY,
    TUYA_API_SECRET_KEY,
    TUYA_API_REGION_KEY,
}
TUYA_SECRET_KEYS = {TUYA_API_KEY_KEY, TUYA_API_SECRET_KEY}
ENV_BY_KEY = {
    TUYA_DEVICE_ID_KEY: "TUYA_DEVICE_ID",
    TUYA_DEVICE_IP_KEY: "TUYA_DEVICE_IP",
    TUYA_API_KEY_KEY: "TUYA_API_KEY",
    TUYA_API_SECRET_KEY: "TUYA_API_SECRET",
    TUYA_API_REGION_KEY: "TUYA_API_REGION",
}
DEFAULT_TUYA_API_REGION = "eu"


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


@dataclass(frozen=True)
class TuyaConfig:
    device_id: str | None = None
    device_ip: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    api_region: str = DEFAULT_TUYA_API_REGION

    @property
    def cloud_configured(self) -> bool:
        return bool(self.device_id and self.api_key and self.api_secret)


def _env_value(key: str) -> str | None:
    return _clean(os.getenv(ENV_BY_KEY[key]))


def _settings_map(db: Session) -> dict[str, AppSetting]:
    rows = db.query(AppSetting).filter(AppSetting.key.in_(TUYA_SETTING_KEYS)).all()
    return {row.key: row for row in rows}


def seed_env_tuya_settings(db: Session) -> None:
    existing = _settings_map(db)
    changed = False
    for key in TUYA_SETTING_KEYS:
        if key in existing:
            continue
        value = _env_value(key)
        if value is None:
            continue
        db.add(AppSetting(key=key, value=value, is_secret=key in TUYA_SECRET_KEYS))
        changed = True
    if changed:
        db.commit()


def resolve_tuya_config(db: Session | None = None, overrides: dict[str, str | None] | None = None) -> TuyaConfig:
    values = {key: _env_value(key) for key in TUYA_SETTING_KEYS}
    if db is not None:
        for key, row in _settings_map(db).items():
            if _clean(row.value) is not None:
                values[key] = _clean(row.value)
    if overrides:
        for key, value in overrides.items():
            if key in values:
                values[key] = _clean(value)

    return TuyaConfig(
        device_id=values.get(TUYA_DEVICE_ID_KEY),
        device_ip=values.get(TUYA_DEVICE_IP_KEY),
        api_key=values.get(TUYA_API_KEY_KEY),
        api_secret=values.get(TUYA_API_SECRET_KEY),
        api_region=values.get(TUYA_API_REGION_KEY) or DEFAULT_TUYA_API_REGION,
    )


def get_tuya_config_status(db: Session) -> dict:
    config = resolve_tuya_config(db)
    return {
        "device_id": config.device_id,
        "device_ip": config.device_ip,
        "api_region": config.api_region,
        "api_key_configured": bool(config.api_key),
        "api_secret_configured": bool(config.api_secret),
        "cloud_configured": config.cloud_configured,
    }


def upsert_tuya_config(
    db: Session,
    *,
    device_id: str | None,
    device_ip: str | None,
    api_key: str | None,
    api_secret: str | None,
    api_region: str | None,
) -> TuyaConfig:
    existing = _settings_map(db)
    updates = {
        TUYA_DEVICE_ID_KEY: _clean(device_id),
        TUYA_DEVICE_IP_KEY: _clean(device_ip),
        TUYA_API_REGION_KEY: _clean(api_region) or DEFAULT_TUYA_API_REGION,
    }
    if _clean(api_key) is not None:
        updates[TUYA_API_KEY_KEY] = _clean(api_key)
    if _clean(api_secret) is not None:
        updates[TUYA_API_SECRET_KEY] = _clean(api_secret)

    now = datetime.now(timezone.utc)
    for key, value in updates.items():
        row = existing.get(key)
        if row is None:
            db.add(AppSetting(key=key, value=value, is_secret=key in TUYA_SECRET_KEYS, updated_at=now))
        else:
            row.value = value
            row.is_secret = key in TUYA_SECRET_KEYS
            row.updated_at = now
    db.commit()
    return resolve_tuya_config(db)
