from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.frontend import frontend_index_response, wants_frontend_document
from app.durations import trusted_duration_seconds
from app.timezones import app_timezone, as_utc
from app.models import Cat, Visit, VisitDiagnostic
from app.schemas import VisitOut, VisitCreate, VisitUpdate, VisitDiagnosticOut, WeightHistory, WeightDataPoint, VisitSummaryBucket, VisitSummaryBucketOut, VisitSummaryCatOut

router = APIRouter(prefix="/visits", tags=["visits"])


def _confidence_reason(confidence: str | None) -> str | None:
    if confidence == "ignored":
        return "operator_ignored"
    if confidence == "normal":
        return "operator_restored"
    if confidence == "suspect":
        return "manual"
    return None


def _record_manual_edit(db: Session, visit: Visit, changes: dict):
    if not changes:
        return
    db.add(VisitDiagnostic(
        visit_id=visit.id,
        event_type="manual_edit",
        payload={"changes": changes},
        recorded_at=datetime.now(timezone.utc),
    ))



def _bucket_start(value: datetime, bucket: VisitSummaryBucket) -> datetime:
    local_value = as_utc(value).astimezone(app_timezone())
    local_start = local_value.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "week":
        local_start = local_start - timedelta(days=local_start.weekday())
    elif bucket == "month":
        local_start = local_start.replace(day=1)
    return local_start


def _bucket_end(start: datetime, bucket: VisitSummaryBucket) -> datetime:
    if bucket == "day":
        return start + timedelta(days=1)
    if bucket == "week":
        return start + timedelta(days=7)
    year = start.year + (1 if start.month == 12 else 0)
    month = 1 if start.month == 12 else start.month + 1
    return start.replace(year=year, month=month, day=1)


def _default_summary_range(bucket: VisitSummaryBucket) -> tuple[datetime, datetime]:
    now_utc = datetime.now(timezone.utc)
    local_end = _bucket_end(_bucket_start(now_utc, bucket), bucket)
    if bucket == "day":
        local_start = local_end - timedelta(days=180)
    elif bucket == "week":
        local_start = local_end - timedelta(weeks=104)
    else:
        local_start = local_end
        for _ in range(60):
            if local_start.month == 1:
                local_start = local_start.replace(year=local_start.year - 1, month=12, day=1)
            else:
                local_start = local_start.replace(month=local_start.month - 1, day=1)
    return local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)


def _average_int(values: list[int]) -> int | None:
    if not values:
        return None
    return int(round(sum(values) / len(values)))


def _average_float(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _bucket_days(start: datetime, end: datetime) -> float:
    seconds = (end - start).total_seconds()
    return max(seconds / 86400, 1)


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
        weight_confidence=visit_data.weight_confidence,
        weight_confidence_reason=_confidence_reason(visit_data.weight_confidence),
        last_weight_at=visit_data.started_at,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


@router.get("", response_model=list[VisitOut])
def list_visits(
    request: Request,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    cat_id: Optional[int] = Query(default=None, gt=0),
    unidentified: Optional[bool] = None,
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
):
    if wants_frontend_document(request):
        response = frontend_index_response()
        if response is not None:
            return response

    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")
    query = db.query(Visit).order_by(Visit.started_at.desc())
    if from_date:
        query = query.filter(Visit.started_at >= as_utc(from_date))
    if to_date:
        query = query.filter(Visit.started_at <= as_utc(to_date))
    if cat_id:
        query = query.filter(Visit.cat_id == cat_id)
    if unidentified:
        query = query.filter(Visit.cat_id == None)  # noqa: E711
    return query.offset(offset).limit(limit).all()


@router.get("/summary", response_model=list[VisitSummaryBucketOut])
def visit_summary(
    bucket: VisitSummaryBucket = "day",
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
    cat_id: Optional[int] = Query(default=None, gt=0),
    unidentified: Optional[bool] = None,
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    db: Session = Depends(get_db),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(status_code=400, detail="from_date must be before to_date")

    default_from, default_to = _default_summary_range(bucket)
    range_start = as_utc(from_date) if from_date else default_from
    range_end = as_utc(to_date) if to_date else default_to

    query = (
        db.query(Visit, Cat.name.label("cat_name"))
        .outerjoin(Cat, Visit.cat_id == Cat.id)
        .filter(Visit.started_at >= range_start, Visit.started_at <= range_end)
    )
    if cat_id:
        query = query.filter(Visit.cat_id == cat_id)
    if unidentified:
        query = query.filter(Visit.cat_id == None)  # noqa: E711

    rows = query.order_by(Visit.started_at.desc(), Visit.id.desc()).all()

    grouped: dict[datetime, list[tuple[Visit, str | None]]] = defaultdict(list)
    for visit, cat_name in rows:
        grouped[_bucket_start(visit.started_at, bucket)].append((visit, cat_name))

    summaries = []
    for bucket_start in sorted(grouped.keys(), reverse=True)[offset:offset + limit]:
        bucket_rows = grouped[bucket_start]
        bucket_end = _bucket_end(bucket_start, bucket)
        visits = [visit for visit, _ in bucket_rows]
        durations = [duration for duration in (trusted_duration_seconds(v) for v in visits) if duration is not None]
        latest_visit_at = max(v.started_at for v in visits) if visits else None

        per_cat: dict[int | None, dict] = {}
        for visit, cat_name in bucket_rows:
            key = visit.cat_id
            entry = per_cat.setdefault(key, {
                "cat_id": key,
                "cat_name": cat_name,
                "visits": [],
                "durations": [],
                "weights": [],
            })
            entry["visits"].append(visit)
            duration = trusted_duration_seconds(visit)
            if duration is not None:
                entry["durations"].append(duration)
            if visit.weight_kg is not None and visit.weight_confidence != "ignored":
                entry["weights"].append(visit.weight_kg)

        cat_summaries = []
        for entry in sorted(per_cat.values(), key=lambda item: (item["cat_name"] is None, item["cat_name"] or "")):
            cat_visits = entry["visits"]
            cat_summaries.append(VisitSummaryCatOut(
                cat_id=entry["cat_id"],
                cat_name=entry["cat_name"],
                visit_count=len(cat_visits),
                average_duration_seconds=_average_int(entry["durations"]),
                average_weight_kg=_average_float(entry["weights"]),
                latest_visit_at=max(v.started_at for v in cat_visits) if cat_visits else None,
            ))

        summaries.append(VisitSummaryBucketOut(
            bucket=bucket,
            bucket_start=bucket_start,
            bucket_end=bucket_end,
            visit_count=len(visits),
            identified_visit_count=sum(1 for v in visits if v.cat_id is not None),
            unidentified_visit_count=sum(1 for v in visits if v.cat_id is None),
            average_visits_per_day=round(len(visits) / _bucket_days(bucket_start, bucket_end), 2),
            average_duration_seconds=_average_int(durations),
            latest_visit_at=latest_visit_at,
            cats=cat_summaries,
        ))

    return summaries


@router.get("/weight-history", response_model=list[WeightHistory])
def weight_history(
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    cat_id: Optional[int] = Query(default=None, gt=0),
    include_ignored: bool = False,
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
    visit_query = (
        db.query(Visit)
        .filter(
            Visit.cat_id.in_(cat_ids),
            Visit.weight_kg.isnot(None),
            Visit.started_at >= from_date,
            Visit.started_at <= to_date,
        )
    )
    if not include_ignored:
        visit_query = visit_query.filter(Visit.weight_confidence != "ignored")
    visits = (
        visit_query
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
                weight_confidence=v.weight_confidence,
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
    """Allows manual correction of visit assignment, timing, duration, weight, and confidence."""
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")

    update_data = update.model_dump(exclude_unset=True)
    changes = {}

    if "cat_id" in update_data:
        cat_id = update_data["cat_id"]
        if cat_id is not None and not db.query(Cat.id).filter(Cat.id == cat_id).first():
            raise HTTPException(status_code=400, detail="Cat not found")
        if visit.cat_id != cat_id:
            changes["cat_id"] = {"from": visit.cat_id, "to": cat_id}
        visit.cat_id = cat_id
        visit.identified_by = "manual" if cat_id is not None else None

    if "started_at" in update_data:
        started_at = update_data["started_at"]
        if visit.started_at != started_at:
            changes["started_at"] = {"from": visit.started_at.isoformat(), "to": started_at.isoformat()}
        visit.started_at = started_at
        if visit.duration_seconds is not None:
            visit.ended_at = started_at + timedelta(seconds=visit.duration_seconds)
        if visit.last_weight_at is not None:
            visit.last_weight_at = started_at

    if "duration_seconds" in update_data:
        duration = update_data["duration_seconds"]
        if visit.duration_seconds != duration:
            changes["duration_seconds"] = {"from": visit.duration_seconds, "to": duration}
        visit.duration_seconds = duration
        visit.duration_source = "manual"
        visit.duration_is_estimated = False
        visit.ended_at = visit.started_at + timedelta(seconds=duration)

    if "weight_kg" in update_data:
        weight = update_data["weight_kg"]
        if visit.weight_kg != weight:
            changes["weight_kg"] = {"from": visit.weight_kg, "to": weight}
        visit.weight_kg = weight
        visit.last_weight_at = visit.started_at
        if "weight_confidence" not in update_data and visit.weight_confidence == "ignored":
            visit.weight_confidence = "normal"
            visit.weight_confidence_reason = "operator_restored"

    if "weight_confidence" in update_data:
        confidence = update_data["weight_confidence"]
        if visit.weight_confidence != confidence:
            changes["weight_confidence"] = {"from": visit.weight_confidence, "to": confidence}
        visit.weight_confidence = confidence
        visit.weight_confidence_reason = _confidence_reason(confidence)

    _record_manual_edit(db, visit, changes)
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
