import base64
import binascii
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat
from app.schemas import CatCreate, CatOut, CatUpdate

router = APIRouter(prefix="/cats", tags=["cats"])

UPLOADS_ROOT = Path(os.getenv("UPLOADS_DIR", "uploads")).resolve()
UPLOADS_DIR = UPLOADS_ROOT / "cat_photos"
MAX_PHOTO_BYTES = int(os.getenv("MAX_CAT_PHOTO_BYTES", str(2 * 1024 * 1024)))
IMAGE_SIGNATURES = {
    "jpg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
}


def _stored_photo_url(photo_path: str | None) -> str | None:
    if not photo_path:
        return None
    normalized = photo_path.replace("\\", "/")
    if normalized.startswith("uploads/"):
        normalized = normalized[len("uploads/"):]
    return f"/uploads/{normalized}"


def _safe_photo_path(photo_path: str) -> Path:
    normalized = photo_path.replace("\\", "/")
    if normalized.startswith("uploads/"):
        normalized = normalized[len("uploads/"):]
    candidate = (UPLOADS_ROOT / normalized).resolve()
    if not candidate.is_relative_to(UPLOADS_ROOT):
        raise HTTPException(status_code=400, detail="Invalid stored photo path")
    return candidate


def _detect_image_extension(image_bytes: bytes) -> str | None:
    for extension, signatures in IMAGE_SIGNATURES.items():
        if any(image_bytes.startswith(signature) for signature in signatures):
            if extension == "webp" and image_bytes[8:12] != b"WEBP":
                continue
            return extension
    return None


def cat_to_out(cat: Cat) -> CatOut:
    photo_url = _stored_photo_url(cat.photo_path)
    return CatOut(
        id=cat.id,
        name=cat.name,
        active=cat.active,
        reference_weight_kg=cat.reference_weight_kg,
        photo_url=photo_url,
        created_at=cat.created_at,
    )


@router.post("", response_model=CatOut)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    db_cat = Cat(name=cat.name, reference_weight_kg=cat.reference_weight_kg)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return cat_to_out(db_cat)


@router.get("", response_model=list[CatOut])
def list_cats(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(Cat)
    if not include_inactive:
        query = query.filter(Cat.active == True)
    return [cat_to_out(c) for c in query.all()]


@router.get("/{cat_id}", response_model=CatOut)
def get_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat_to_out(cat)


@router.patch("/{cat_id}", response_model=CatOut)
def update_cat(cat_id: int, update: CatUpdate, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat_to_out(cat)


class PhotoUpload(BaseModel):
    photo_data: str  # base64 data URL, e.g. "data:image/jpeg;base64,..."


@router.post("/{cat_id}/photo", response_model=CatOut)
def upload_cat_photo(cat_id: int, body: PhotoUpload, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    if not body.photo_data.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Invalid image data URL")
    try:
        header, encoded = body.photo_data.split(",", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image data URL")
    if ";base64" not in header:
        raise HTTPException(status_code=400, detail="Image data must be base64 encoded")
    if len(encoded) > MAX_PHOTO_BYTES * 4 // 3 + 4:
        raise HTTPException(status_code=413, detail="Image is too large")

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="Could not decode image data")
    if len(image_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large")

    extension = _detect_image_extension(image_bytes)
    if extension is None:
        raise HTTPException(status_code=400, detail="Uploaded data is not a supported image")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    photo_path = UPLOADS_DIR / f"{cat_id}.{extension}"
    photo_path.write_bytes(image_bytes)

    cat.photo_path = f"cat_photos/{cat_id}.{extension}"
    db.commit()
    db.refresh(cat)
    return cat_to_out(cat)


@router.delete("/{cat_id}/photo", response_model=CatOut)
def delete_cat_photo(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    if cat.photo_path:
        photo_file = _safe_photo_path(cat.photo_path)
        if photo_file.exists():
            photo_file.unlink()
        cat.photo_path = None
        db.commit()
        db.refresh(cat)

    return cat_to_out(cat)
