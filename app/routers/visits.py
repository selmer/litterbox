from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Visit
from app.schemas import VisitOut, VisitCreate, VisitUpdate, WeightHistory, WeightDataPoint

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitOut, status_code=201)
def create_visit(visit_data: VisitCreate, db: Session = Depends(get_db)):
    """Creates a manual visit entry."""
    visit = Visit(
        cat_id=visit_data.cat_id,
        identified_by="manual",
        started_at=visit_data.started_at,
        duration_seconds=visit_data.duration_seconds,
        weight_kg=visit_data.weight_kg,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.get("", response_model=list[VisitOut])
def list_visits(
    limit: int = 50,
    offset: int = 0,
    cat_id: Optional[int] = None,
    unidentified: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Visit).order_by(Visit.started_at.desc())
    if cat_id:
        query = query.filter(Visit.cat_id == cat_id)
    if unidentified:
        query = query.filter(Visit.cat_id == None)  # noqa: E711
    return query.offset(offset).limit(limit).all()


@router.get("/weight-history", response_model=list[WeightHistory])
def weight_history(
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    cat_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Returns weight readings grouped by cat, ready for the chart.
    Defaults to the last 12 months if no date range is provided.
    """
    from app.models import Cat
    from datetime import timedelta

    if to_date is None:
        to_date = datetime.now(timezone.utc)
    if from_date is None:
        from_date = to_date - timedelta(days=365)

    cats_query = db.query(Cat).filter(Cat.active == True)
    if cat_id:
        cats_query = cats_query.filter(Cat.id == cat_id)
    cats = cats_query.all()

    result = []
    for cat in cats:
        visits = (
            db.query(Visit)
            .filter(
                Visit.cat_id == cat.id,
                Visit.weight_kg.isnot(None),
                Visit.started_at >= from_date,
                Visit.started_at <= to_date,
            )
            .order_by(Visit.started_at.asc())
            .all()
        )

        data_points = [
            WeightDataPoint(
                timestamp=v.started_at,
                weight_kg=v.weight_kg,
                visit_id=v.id,
            )
            for v in visits
        ]

        result.append(
            WeightHistory(
                cat_id=cat.id,
                cat_name=cat.name,
                data=data_points,
            )
        )

    return result


@router.get("/{visit_id}", response_model=VisitOut)
def get_visit(visit_id: int, db: Session = Depends(get_db)):
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    return visit


@router.patch("/{visit_id}", response_model=VisitOut)
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


@router.delete("/{visit_id}", status_code=204)
def delete_visit(visit_id: int, db: Session = Depends(get_db)):
    """Deletes a visit record."""
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    db.delete(visit)
    db.commit()
