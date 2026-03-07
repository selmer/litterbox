from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, CleaningCycle, Visit
from app.schemas import CatDashboard, DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# How long since the last successful poll before we consider the poller unhealthy
POLLER_HEALTHY_THRESHOLD_SECONDS = 30

# Shared state updated by the poller — imported in main.py
last_successful_poll_at: datetime = None


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    from app.routers.dashboard import last_successful_poll_at

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Aggregate today's visits per cat (count + total duration)
    today_subq = (
        db.query(
            Visit.cat_id,
            func.count(Visit.id).label("visits_today"),
            func.sum(func.coalesce(Visit.duration_seconds, 0)).label("time_in_box_today_seconds"),
        )
        .filter(Visit.cat_id.isnot(None), Visit.started_at >= today_start)
        .group_by(Visit.cat_id)
        .subquery()
    )

    # Latest visit per cat: first find the max started_at per cat_id
    max_started_subq = (
        db.query(
            Visit.cat_id,
            func.max(Visit.started_at).label("max_started_at"),
        )
        .filter(Visit.cat_id.isnot(None))
        .group_by(Visit.cat_id)
        .subquery()
    )

    # Then join back to visits to get the full row for the last visit
    last_visit_subq = (
        db.query(Visit)
        .join(
            max_started_subq,
            (Visit.cat_id == max_started_subq.c.cat_id)
            & (Visit.started_at == max_started_subq.c.max_started_at),
        )
        .subquery()
    )

    # Single query: active cats LEFT JOINed with today aggregates and last visit
    rows = (
        db.query(
            Cat,
            func.coalesce(today_subq.c.visits_today, 0).label("visits_today"),
            func.coalesce(today_subq.c.time_in_box_today_seconds, 0).label("time_in_box_today_seconds"),
            last_visit_subq.c.started_at.label("last_visit_at"),
            last_visit_subq.c.weight_kg.label("last_visit_weight_kg"),
            last_visit_subq.c.duration_seconds.label("last_visit_duration_seconds"),
        )
        .filter(Cat.active == True)
        .outerjoin(today_subq, Cat.id == today_subq.c.cat_id)
        .outerjoin(last_visit_subq, Cat.id == last_visit_subq.c.cat_id)
        .all()
    )

    cat_dashboards = [
        CatDashboard(
            cat_id=cat.id,
            cat_name=cat.name,
            reference_weight_kg=cat.reference_weight_kg,
            visits_today=visits_today,
            time_in_box_today_seconds=time_in_box_today_seconds,
            last_visit_at=last_visit_at,
            last_visit_weight_kg=last_visit_weight_kg,
            last_visit_duration_seconds=last_visit_duration_seconds,
        )
        for cat, visits_today, time_in_box_today_seconds, last_visit_at, last_visit_weight_kg, last_visit_duration_seconds in rows
    ]

    unidentified_today = (
        db.query(Visit)
        .filter(
            Visit.cat_id.is_(None),
            Visit.started_at >= today_start,
            Visit.ended_at.isnot(None),
        )
        .count()
    )

    cleaning_cycles_today = (
        db.query(CleaningCycle)
        .filter(CleaningCycle.started_at >= today_start)
        .count()
    )

    poller_healthy = (
        last_successful_poll_at is not None
        and (now - last_successful_poll_at).total_seconds() < POLLER_HEALTHY_THRESHOLD_SECONDS
    )

    return DashboardOut(
        cats=cat_dashboards,
        unidentified_visits_today=unidentified_today,
        cleaning_cycles_today=cleaning_cycles_today,
        poller_healthy=poller_healthy,
        generated_at=now,
    )
