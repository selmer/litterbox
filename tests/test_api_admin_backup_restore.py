import base64
import io
import zipfile
from datetime import date, datetime, timezone

from app.models import AppSetting, Cat, CatEvent, DeviceSnapshot, SettingsHistory, Visit, VisitDiagnostic


def _backup_to_base64(response):
    return base64.b64encode(response.content).decode("ascii")


def test_backup_contains_database_and_uploads(client, db_session, tmp_path, monkeypatch):
    uploads_root = tmp_path / "uploads"
    cat_photo_dir = uploads_root / "cat_photos"
    cat_photo_dir.mkdir(parents=True)
    photo = cat_photo_dir / "1.png"
    photo.write_bytes(b"\x89PNG\r\n\x1a\nphoto")

    monkeypatch.setattr("app.routers.admin.UPLOADS_ROOT", uploads_root)

    cat = Cat(name="Plurk", reference_weight_kg=3.8, photo_path="cat_photos/1.png")
    db_session.add(cat)
    db_session.commit()

    response = client.get("/admin/backup")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert {"metadata.json", "database.json", "uploads/cat_photos/1.png"} <= names
        database = archive.read("database.json").decode("utf-8")
        assert "Plurk" in database
        assert archive.read("uploads/cat_photos/1.png") == b"\x89PNG\r\n\x1a\nphoto"


def test_restore_recreates_database_and_uploads(client, db_session, tmp_path, monkeypatch):
    uploads_root = tmp_path / "uploads"
    uploads_root.mkdir()
    monkeypatch.setattr("app.routers.admin.UPLOADS_ROOT", uploads_root)

    cat = Cat(name="Plurk", reference_weight_kg=3.8, photo_path="cat_photos/1.png")
    db_session.add(cat)
    db_session.commit()
    visit = Visit(
        cat_id=cat.id,
        identified_by="auto",
        started_at=datetime(2026, 5, 18, 8, 0, tzinfo=timezone.utc),
        ended_at=datetime(2026, 5, 18, 8, 2, tzinfo=timezone.utc),
        duration_seconds=120,
        weight_kg=3.81,
    )
    db_session.add(visit)
    db_session.commit()
    db_session.add_all([
        CatEvent(cat_id=cat.id, event_type="vet", occurred_at=date(2026, 5, 1), title="Checkup"),
        VisitDiagnostic(visit_id=visit.id, event_type="matched", payload={"ok": True}),
        DeviceSnapshot(raw_dps={"1": "ready"}),
        SettingsHistory(dp="cleaning_interval", value="4"),
    ])
    (uploads_root / "cat_photos").mkdir()
    (uploads_root / "cat_photos" / "1.png").write_bytes(b"photo")
    db_session.commit()

    backup = _backup_to_base64(client.get("/admin/backup"))

    db_session.query(VisitDiagnostic).delete()
    db_session.query(Visit).delete()
    db_session.query(CatEvent).delete()
    db_session.query(Cat).delete()
    db_session.query(DeviceSnapshot).delete()
    db_session.query(SettingsHistory).delete()
    db_session.commit()
    (uploads_root / "cat_photos" / "1.png").unlink()

    validate_response = client.post("/admin/restore/validate", json={"archive_data": backup})
    assert validate_response.status_code == 200
    assert validate_response.json()["tables"]["cats"] == 1
    assert validate_response.json()["uploads"] == 1

    restore_response = client.post("/admin/restore", json={"archive_data": backup, "confirm": True})
    assert restore_response.status_code == 200
    assert restore_response.json()["restored"] is True
    assert db_session.query(Cat).filter_by(name="Plurk").count() == 1
    assert db_session.query(Visit).count() == 1
    assert db_session.query(CatEvent).count() == 1
    assert db_session.query(VisitDiagnostic).count() == 1
    assert db_session.query(DeviceSnapshot).count() == 1
    assert db_session.query(SettingsHistory).count() == 1
    assert (uploads_root / "cat_photos" / "1.png").read_bytes() == b"photo"


def test_backup_excludes_secret_app_settings(client, db_session):
    db_session.add_all([
        AppSetting(key="tuya.device_id", value="device-1", is_secret=False),
        AppSetting(key="tuya.api_key", value="secret-key", is_secret=True),
    ])
    db_session.commit()

    response = client.get("/admin/backup")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        metadata = archive.read("metadata.json").decode("utf-8")
        database = archive.read("database.json").decode("utf-8")
        assert "app_settings" in database
        assert "device-1" in database
        assert "secret-key" not in database
        assert "secrets_excluded" in metadata


def test_restore_imports_only_non_secret_app_settings_from_backup(client, db_session):
    db_session.add(AppSetting(key="tuya.api_key", value="current-secret", is_secret=True))
    db_session.commit()

    backup = _backup_to_base64(client.get("/admin/backup"))

    restore_response = client.post("/admin/restore", json={"archive_data": backup, "confirm": True})

    assert restore_response.status_code == 200
    assert db_session.get(AppSetting, "tuya.api_key") is None


def test_restore_requires_confirmation(client):
    backup = _backup_to_base64(client.get("/admin/backup"))

    response = client.post("/admin/restore", json={"archive_data": backup, "confirm": False})

    assert response.status_code == 400
    assert response.json()["detail"] == "Restore confirmation is required"


def test_restore_rejects_path_traversal_archive(client):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("metadata.json", '{"format_version": 1, "app": "litterbox"}')
        archive.writestr("database.json", "{}")
        archive.writestr("../escape.txt", "nope")
    archive_data = base64.b64encode(buffer.getvalue()).decode("ascii")

    response = client.post("/admin/restore/validate", json={"archive_data": archive_data})

    assert response.status_code == 400
    assert "Unsafe archive path" in response.json()["detail"]
