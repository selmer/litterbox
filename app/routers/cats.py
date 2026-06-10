import base64
import binascii
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.frontend import frontend_index_response, wants_frontend_document
from app.models import Cat, CatEvent
from app.schemas import CatCreate, CatEventCreate, CatEventOut, CatEventUpdate, CatOut, CatUpdate

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
        birth_date=cat.birth_date,
        photo_url=photo_url,
        created_at=cat.created_at,
    )


@router.post("", response_model=CatOut)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    db_cat = Cat(name=cat.name, reference_weight_kg=cat.reference_weight_kg, birth_date=cat.birth_date)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return cat_to_out(db_cat)


@router.get("", response_model=list[CatOut])
def list_cats(request: Request, include_inactive: bool = False, db: Session = Depends(get_db)):
    if wants_frontend_document(request):
        response = frontend_index_response()
        if response is not None:
            return response

    query = db.query(Cat)
    if not include_inactive:
        query = query.filter(Cat.active == True)
    return [cat_to_out(c) for c in query.all()]


def _get_cat_or_404(cat_id: int, db: Session) -> Cat:
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat


def _ordered_unique_cat_ids(cat_ids: list[int]) -> list[int]:
    result = []
    for cat_id in cat_ids:
        if cat_id not in result:
            result.append(cat_id)
    return result


def _selected_cats_or_400(path_cat_id: int, requested_cat_ids: list[int] | None, db: Session) -> list[Cat]:
    cat_ids = _ordered_unique_cat_ids(requested_cat_ids or [path_cat_id])
    if path_cat_id not in cat_ids:
        raise HTTPException(status_code=400, detail="Selected cats must include the current cat")

    cats = db.query(Cat).filter(Cat.id.in_(cat_ids)).all()
    cats_by_id = {cat.id: cat for cat in cats}
    missing = [cat_id for cat_id in cat_ids if cat_id not in cats_by_id]
    if missing:
        raise HTTPException(status_code=400, detail="Selected cat not found")
    return [cats_by_id[cat_id] for cat_id in cat_ids]


def _event_cat_ids(event: CatEvent) -> list[int]:
    cat_ids = [cat.id for cat in event.cats]
    if not cat_ids and event.cat_id is not None:
        cat_ids = [event.cat_id]
    return cat_ids


def _get_cat_event_or_404(cat_id: int, event_id: int, db: Session) -> CatEvent:
    event = db.query(CatEvent).filter(CatEvent.id == event_id).first()
    if not event or cat_id not in _event_cat_ids(event):
        raise HTTPException(status_code=404, detail="Cat event not found")
    return event


def cat_event_to_out(event: CatEvent) -> CatEventOut:
    linked_cats = list(event.cats)
    if not linked_cats and event.cat is not None:
        linked_cats = [event.cat]
    linked_cats.sort(key=lambda cat: (cat.name.lower(), cat.id))
    return CatEventOut(
        id=event.id,
        cat_id=event.cat_id,
        cat_ids=[cat.id for cat in linked_cats],
        cat_names=[cat.name for cat in linked_cats],
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        title=event.title,
        notes=event.notes,
        cost_amount=event.cost_amount,
        cost_currency=event.cost_currency,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


@router.get("/{cat_id}/events", response_model=list[CatEventOut])
def list_cat_events(cat_id: int, db: Session = Depends(get_db)):
    _get_cat_or_404(cat_id, db)
    events = (
        db.query(CatEvent)
        .filter(or_(CatEvent.cat_id == cat_id, CatEvent.cats.any(Cat.id == cat_id)))
        .order_by(CatEvent.occurred_at.desc(), CatEvent.id.desc())
        .all()
    )
    return [cat_event_to_out(event) for event in events]


@router.post("/{cat_id}/events", response_model=CatEventOut, status_code=201)
def create_cat_event(cat_id: int, event_data: CatEventCreate, db: Session = Depends(get_db)):
    _get_cat_or_404(cat_id, db)
    selected_cats = _selected_cats_or_400(cat_id, event_data.cat_ids, db)
    event = CatEvent(cat_id=cat_id, **event_data.model_dump(exclude={"cat_ids"}))
    event.cats = selected_cats
    db.add(event)
    db.commit()
    db.refresh(event)
    return cat_event_to_out(event)


@router.patch("/{cat_id}/events/{event_id}", response_model=CatEventOut)
def update_cat_event(cat_id: int, event_id: int, update: CatEventUpdate, db: Session = Depends(get_db)):
    _get_cat_or_404(cat_id, db)
    event = _get_cat_event_or_404(cat_id, event_id, db)
    payload = update.model_dump(exclude_unset=True)
    selected_cat_ids = payload.pop("cat_ids", None)
    if selected_cat_ids is not None:
        event.cats = _selected_cats_or_400(cat_id, selected_cat_ids, db)
    for field, value in payload.items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return cat_event_to_out(event)


@router.delete("/{cat_id}/events/{event_id}", status_code=204)
def delete_cat_event(cat_id: int, event_id: int, db: Session = Depends(get_db)):
    _get_cat_or_404(cat_id, db)
    event = _get_cat_event_or_404(cat_id, event_id, db)
    db.delete(event)
    db.commit()


@router.get("/{cat_id}", response_model=CatOut)
def get_cat(cat_id: int, request: Request, db: Session = Depends(get_db)):
    if wants_frontend_document(request):
        response = frontend_index_response()
        if response is not None:
            return response

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
