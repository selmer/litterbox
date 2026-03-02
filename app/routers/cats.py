from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat
from app.schemas import CatCreate, CatOut, CatUpdate

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
