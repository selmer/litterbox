import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat
from app.schemas import CatCreate, CatOut, CatUpdate

UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads" / "cat_photos"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/cats", tags=["cats"])


@router.post("", response_model=CatOut)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    db_cat = Cat(name=cat.name, reference_weight_kg=cat.reference_weight_kg)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


@router.get("", response_model=list[CatOut])
def list_cats(include_inactive: bool = False, db: Session = Depends(get_db)):
    query = db.query(Cat)
    if not include_inactive:
        query = query.filter(Cat.active == True)
    return query.all()


@router.get("/{cat_id}", response_model=CatOut)
def get_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat


@router.patch("/{cat_id}", response_model=CatOut)
def update_cat(cat_id: int, update: CatUpdate, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.post("/{cat_id}/photo", response_model=CatOut)
async def upload_cat_photo(cat_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, GIF, or WebP)")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must not exceed 5 MB")

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    filename = f"{cat_id}_{uuid.uuid4().hex}{ext}"
    file_path = UPLOADS_DIR / filename

    # Remove old photo file if it exists
    if cat.photo_url:
        old_filename = cat.photo_url.split("/")[-1]
        old_path = UPLOADS_DIR / old_filename
        if old_path.exists():
            old_path.unlink()

    file_path.write_bytes(contents)
    cat.photo_url = f"/uploads/cat_photos/{filename}"
    db.commit()
    db.refresh(cat)
    return cat
