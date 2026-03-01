import logging
import os
import time
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, engine
from app.models import Base, Cat, Visit, CleaningCycle
from app.poller import LitterboxPoller
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))


# --- Pydantic schemas ---

class CatCreate(BaseModel):
    name: str
    reference_weight_kg: Optional[float] = None


class CatUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    reference_weight_kg: Optional[float] = None


class CatOut(BaseModel):
    id: int
    name: str
    active: bool
    reference_weight_kg: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class VisitOut(BaseModel):
    id: int
    cat_id: Optional[int]
    identified_by: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    weight_kg: Optional[float]

    class Config:
        from_attributes = True


class VisitUpdate(BaseModel):
    cat_id: Optional[int] = None
    identified_by: Optional[str] = None


class CleaningCycleOut(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True


# --- Background poller thread ---

def run_poller():
    """Runs the poller in a background thread, one DB session per poll cycle."""
    from app.database import SessionLocal
    logger.info("Poller thread started")
    while True:
        try:
            db = SessionLocal()
            poller = LitterboxPoller(db)
            while True:
                poller.poll()
                time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Poller crashed, restarting: {e}")
            time.sleep(10)
        finally:
            db.close()


# --- App lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    logger.info("Database tables created")

    # Start poller in background thread
    thread = threading.Thread(target=run_poller, daemon=True)
    thread.start()
    logger.info("Poller started")

    yield

    logger.info("Shutting down")


app = FastAPI(title="Litterbox API", lifespan=lifespan)


# --- Cat endpoints ---

@app.post("/cats", response_model=CatOut)
def create_cat(cat: CatCreate, db: Session = Depends(get_db)):
    db_cat = Cat(name=cat.name, reference_weight_kg=cat.reference_weight_kg)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


@app.get("/cats", response_model=list[CatOut])
def list_cats(db: Session = Depends(get_db)):
    return db.query(Cat).all()


@app.get("/cats/{cat_id}", response_model=CatOut)
def get_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat


@app.patch("/cats/{cat_id}", response_model=CatOut)
def update_cat(cat_id: int, update: CatUpdate, db: Session = Depends(get_db)):
    cat = db.query(Cat).filter(Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


# --- Visit endpoints ---

@app.get("/visits", response_model=list[VisitOut])
def list_visits(
    limit: int = 50,
    cat_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Visit).order_by(Visit.started_at.desc())
    if cat_id:
        query = query.filter(Visit.cat_id == cat_id)
    return query.limit(limit).all()


@app.get("/visits/{visit_id}", response_model=VisitOut)
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@app.patch("/visits/{visit_id}", response_model=VisitOut)
def update_visit(visit_id: int, update: VisitUpdate, db: Session = Depends(get_db)):
    """Allows manual correction of cat assignment."""
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(visit, field, value)
    if update.cat_id is not None:
        visit.identified_by = "manual"
    db.commit()
    db.refresh(visit)
    return visit


# --- Cleaning cycle endpoints ---

@app.get("/cleaning-cycles", response_model=list[CleaningCycleOut])
def list_cleaning_cycles(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(CleaningCycle)
        .order_by(CleaningCycle.started_at.desc())
        .limit(limit)
        .all()
    )


# --- Health check ---

@app.get("/health")
def health():
    return {"status": "ok"}