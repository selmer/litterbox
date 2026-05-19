import base64
import binascii
import io
import json
import os
import shutil
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import Date, DateTime, Numeric, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Base

router = APIRouter(prefix="/admin", tags=["admin"])

BACKUP_FORMAT_VERSION = 1
BACKUP_APP_NAME = "litterbox"
UPLOADS_ROOT = Path(os.getenv("UPLOADS_DIR", "uploads")).resolve()
MAX_RESTORE_ARCHIVE_BYTES = int(os.getenv("MAX_RESTORE_ARCHIVE_BYTES", str(100 * 1024 * 1024)))


class RestoreArtifactIn(BaseModel):
    archive_data: str


class RestoreRequestIn(RestoreArtifactIn):
    confirm: bool = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_schema_revision(db: Session) -> str | None:
    try:
        row = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
    except Exception:
        return None
    return str(row[0]) if row else None


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _db_export(db: Session) -> dict[str, list[dict[str, Any]]]:
    export: dict[str, list[dict[str, Any]]] = {}
    for table in Base.metadata.sorted_tables:
        rows = db.execute(table.select().order_by(*table.primary_key.columns)).mappings().all()
        export[table.name] = [
            {column.name: _json_value(row[column.name]) for column in table.columns}
            for row in rows
        ]
    return export


def _metadata(db: Session) -> dict[str, Any]:
    return {
        "format_version": BACKUP_FORMAT_VERSION,
        "app": BACKUP_APP_NAME,
        "created_at": _utc_now().isoformat(),
        "schema_revision": _get_schema_revision(db),
    }


def _assert_safe_archive_path(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise HTTPException(status_code=400, detail=f"Unsafe archive path: {name}")
    if path.parts[0] not in {"metadata.json", "database.json", "uploads"}:
        raise HTTPException(status_code=400, detail=f"Unexpected archive path: {name}")
    if path.parts[0] in {"metadata.json", "database.json"} and len(path.parts) != 1:
        raise HTTPException(status_code=400, detail=f"Unexpected archive path: {name}")
    return path


def _read_archive(archive_bytes: bytes) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[str]]:
    if len(archive_bytes) > MAX_RESTORE_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Restore archive is too large")

    try:
        with ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = [info.filename for info in archive.infolist() if not info.is_dir()]
            for name in names:
                _assert_safe_archive_path(name)
            if "metadata.json" not in names or "database.json" not in names:
                raise HTTPException(status_code=400, detail="Backup archive must contain metadata.json and database.json")
            metadata = json.loads(archive.read("metadata.json"))
            database = json.loads(archive.read("database.json"))
    except HTTPException:
        raise
    except (BadZipFile, json.JSONDecodeError, OSError, KeyError):
        raise HTTPException(status_code=400, detail="Restore archive is not a valid backup")

    if metadata.get("format_version") != BACKUP_FORMAT_VERSION:
        raise HTTPException(status_code=400, detail="Backup format version is not supported")
    if metadata.get("app") != BACKUP_APP_NAME:
        raise HTTPException(status_code=400, detail="Backup was not created by this application")
    if not isinstance(database, dict):
        raise HTTPException(status_code=400, detail="Backup database export is malformed")

    expected_tables = {table.name for table in Base.metadata.sorted_tables}
    if set(database) != expected_tables:
        raise HTTPException(status_code=400, detail="Backup database tables do not match this application")
    for table_name, rows in database.items():
        if not isinstance(rows, list):
            raise HTTPException(status_code=400, detail=f"Backup table {table_name} is malformed")

    upload_names = [name for name in names if name.startswith("uploads/")]
    return metadata, database, upload_names


def _decode_archive(archive_data: str) -> bytes:
    encoded = archive_data
    if "," in encoded and encoded.startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Restore archive must be base64 encoded")


def _coerce_value(column, value: Any) -> Any:
    if value is None:
        return None
    column_type = getattr(column.type, "impl", column.type)
    if isinstance(column_type, DateTime):
        return datetime.fromisoformat(value)
    if isinstance(column_type, Date):
        return date.fromisoformat(value)
    if isinstance(column_type, Numeric) and getattr(column_type, "asdecimal", True):
        return Decimal(str(value))
    return value


def _restore_database(db: Session, database: dict[str, list[dict[str, Any]]]) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

    for table in Base.metadata.sorted_tables:
        rows = []
        column_names = {column.name for column in table.columns}
        for row in database[table.name]:
            if set(row) != column_names:
                raise HTTPException(status_code=400, detail=f"Backup table {table.name} has incompatible columns")
            rows.append({column.name: _coerce_value(column, row[column.name]) for column in table.columns})
        if rows:
            db.execute(table.insert(), rows)
    db.commit()


def _restore_uploads(archive_bytes: bytes) -> int:
    temp_root = UPLOADS_ROOT.parent / f".{UPLOADS_ROOT.name}.restore-tmp"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True, exist_ok=True)

    restored = 0
    try:
        with ZipFile(io.BytesIO(archive_bytes)) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.startswith("uploads/"):
                    continue
                archive_path = _assert_safe_archive_path(info.filename)
                relative_parts = archive_path.parts[1:]
                if not relative_parts:
                    continue
                destination = (temp_root / Path(*relative_parts)).resolve()
                if not destination.is_relative_to(temp_root.resolve()):
                    raise HTTPException(status_code=400, detail=f"Unsafe archive path: {info.filename}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(info.filename))
                restored += 1

        if UPLOADS_ROOT.exists():
            shutil.rmtree(UPLOADS_ROOT)
        temp_root.replace(UPLOADS_ROOT)
        return restored
    except Exception:
        if temp_root.exists():
            shutil.rmtree(temp_root)
        raise


@router.get("/backup")
def create_backup(db: Session = Depends(get_db)):
    metadata = _metadata(db)
    database = _db_export(db)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("metadata.json", json.dumps(metadata, indent=2, sort_keys=True))
        archive.writestr("database.json", json.dumps(database, indent=2, sort_keys=True))
        if UPLOADS_ROOT.exists():
            for file in sorted(path for path in UPLOADS_ROOT.rglob("*") if path.is_file()):
                relative = file.relative_to(UPLOADS_ROOT).as_posix()
                archive.write(file, f"uploads/{relative}")

    buffer.seek(0)
    filename = f"litterbox-backup-{_utc_now().strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore/validate")
def validate_restore_artifact(body: RestoreArtifactIn):
    metadata, database, upload_names = _read_archive(_decode_archive(body.archive_data))
    return {
        "valid": True,
        "metadata": metadata,
        "tables": {table_name: len(rows) for table_name, rows in database.items()},
        "uploads": len(upload_names),
    }


@router.post("/restore")
def restore_backup(body: RestoreRequestIn, db: Session = Depends(get_db)):
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Restore confirmation is required")
    archive_bytes = _decode_archive(body.archive_data)
    metadata, database, upload_names = _read_archive(archive_bytes)
    _restore_database(db, database)
    restored_uploads = _restore_uploads(archive_bytes)
    return {
        "restored": True,
        "metadata": metadata,
        "tables": {table_name: len(rows) for table_name, rows in database.items()},
        "uploads": restored_uploads,
        "expected_uploads": len(upload_names),
    }
