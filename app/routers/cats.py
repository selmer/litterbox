import base64
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat
from app.schemas import CatCreate, CatOut, CatUpdate

router = APIRouter(prefix="/cats", tags=["cats"])

UPLOADS_DIR = Path("uploads/cat_photos")


def cat_to_out(cat: Cat) -> CatOut:
    photo_url = f"/uploads/cat_photos/{cat.id}.jpg" if cat.photo_path else None
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

    # Parse data URL: "data:image/jpeg;base64,<data>"
    if not body.photo_data.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Invalid image data URL")
    try:
        header, encoded = body.photo_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode image data")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    photo_path = UPLOADS_DIR / f"{cat_id}.jpg"
    photo_path.write_bytes(image_bytes)

    cat.photo_path = str(photo_path)
    db.commit()
    db.refresh(cat)
    return cat_to_out(cat)


@router.delete("/{cat_id}/photo", response_model=CatOut)
def delete_cat_photo(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    if cat.photo_path:
        photo_file = Path(cat.photo_path)
        if photo_file.exists():
            photo_file.unlink()
        cat.photo_path = None
        db.commit()
        db.refresh(cat)

    return cat_to_out(cat)
