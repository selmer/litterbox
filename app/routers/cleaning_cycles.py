from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CleaningCycle
from app.schemas import CleaningCycleOut

router = APIRouter(prefix="/cleaning-cycles", tags=["cleaning-cycles"])


@router.get("", response_model=list[CleaningCycleOut])
def list_cleaning_cycles(limit: int = Query(default=50, le=500), db: Session = Depends(get_db)):
    return (
        db.query(CleaningCycle)
        .order_by(CleaningCycle.started_at.desc())
        .limit(limit)
        .all()
    )
