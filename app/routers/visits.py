from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, Visit, VisitDiagnostic
from app.schemas import VisitOut, VisitCreate, VisitUpdate, VisitDiagnosticOut, WeightHistory, WeightDataPoint

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=VisitOut, status_code=201)
def create_visit(visit_data: VisitCreate, db: Session = Depends(get_db)):
    """Creates a manual visit entry."""
    if not db.query(Cat.id).filter(Cat.id == visit_data.cat_id).first():
        raise HTTPException(status_code=400, detail="Cat not found")

    visit = Visit(
        cat_id=visit_data.cat_id,
        identified_by="manual",
        started_at=visit_data.started_at,
        ended_at=visit_data.started_at + timedelta(seconds=visit_data.duration_seconds),
        duration_seconds=visit_data.duration_seconds,
        duration_source="manual",
        duration_is_estimated=False,
        weight_kg=visit_data.weight_kg,
        last_weight_at=visit_data.started_at,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.get("", response_model=list[VisitOut])
def list_visits(
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    cat_id: Optional[int] = Query(default=None, gt=0),
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
    cat_id: Optional[int] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    """
    Returns weight readings grouped by cat, ready for the chart.
    Defaults to the last 12 months if no date range is provided.
    """
    if to_date is None:
        to_date = datetime.now(timezone.utc)
    if from_date is None:
        from_date = to_date - timedelta(days=365)
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")

    cats_query = db.query(Cat).filter(Cat.active == True)
    if cat_id:
        cats_query = cats_query.filter(Cat.id == cat_id)
    cats = cats_query.all()

    if not cats:
        return []

    cat_ids = [cat.id for cat in cats]
    visits = (
        db.query(Visit)
        .filter(
            Visit.cat_id.in_(cat_ids),
            Visit.weight_kg.isnot(None),
            Visit.started_at >= from_date,
            Visit.started_at <= to_date,
        )
        .order_by(Visit.cat_id.asc(), Visit.started_at.asc(), Visit.id.asc())
        .all()
    )

    visits_by_cat = defaultdict(list)
    for visit in visits:
        visits_by_cat[visit.cat_id].append(visit)

    result = []
    for cat in cats:
        data_points = [
            WeightDataPoint(
                timestamp=v.started_at,
                weight_kg=v.weight_kg,
                visit_id=v.id,
            )
            for v in visits_by_cat[cat.id]
        ]

        result.append(
            WeightHistory(
                cat_id=cat.id,
                cat_name=cat.name,
                data=data_points,
            )
        )

    return result


@router.get("/{visit_id}/diagnostics", response_model=list[VisitDiagnosticOut])
def get_visit_diagnostics(visit_id: int, db: Session = Depends(get_db)):
    if not db.query(Visit.id).filter(Visit.id == visit_id).first():
        raise HTTPException(status_code=404, detail="Visit not found")
    return (
        db.query(VisitDiagnostic)
        .filter(VisitDiagnostic.visit_id == visit_id)
        .order_by(VisitDiagnostic.recorded_at.asc(), VisitDiagnostic.id.asc())
        .all()
    )


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
    update_data = update.model_dump(exclude_unset=True)
    if "cat_id" in update_data:
        cat_id = update_data["cat_id"]
        if cat_id is not None and not db.query(Cat.id).filter(Cat.id == cat_id).first():
            raise HTTPException(status_code=400, detail="Cat not found")
        visit.cat_id = cat_id
        visit.identified_by = "manual" if cat_id is not None else None
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
