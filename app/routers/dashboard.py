import threading
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, CleaningCycle, Visit
from app.durations import trusted_duration_expr
from app.schemas import CatDashboard, DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

POLL_INTERVAL_SECONDS = 300

# How long since the last successful poll before we consider the poller unhealthy
POLLER_HEALTHY_THRESHOLD_SECONDS = POLL_INTERVAL_SECONDS * 3

# Shared state updated by the poller — protected by _poll_lock
_poll_lock = threading.Lock()
last_successful_poll_at: datetime = None
last_poll_attempted_at: datetime = None
last_poll_error: str = None
update_mode: str = "polling"   # set to "webhook" by main.py lifespan


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    with _poll_lock:
        last_poll = last_successful_poll_at
        last_attempt = last_poll_attempted_at
        poll_error = last_poll_error

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    trusted_duration = trusted_duration_expr()

    # Aggregate today's visits per cat (count + total trusted duration)
    today_subq = (
        db.query(
            Visit.cat_id,
            func.count(Visit.id).label("visits_today"),
            func.sum(func.coalesce(trusted_duration, 0)).label("time_in_box_today_seconds"),
        )
        .filter(Visit.cat_id.isnot(None), Visit.started_at >= today_start)
        .group_by(Visit.cat_id)
        .subquery()
    )

    # Latest visit per cat, with visit ID as the tie-breaker for deterministic rows.
    last_visit_subq = (
        db.query(
            Visit.cat_id.label("cat_id"),
            Visit.started_at.label("started_at"),
            Visit.weight_kg.label("weight_kg"),
            trusted_duration.label("duration_seconds"),
            func.row_number()
            .over(
                partition_by=Visit.cat_id,
                order_by=(Visit.started_at.desc(), Visit.id.desc()),
            )
            .label("row_num"),
        )
        .filter(Visit.cat_id.isnot(None))
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
        .outerjoin(
            last_visit_subq,
            and_(Cat.id == last_visit_subq.c.cat_id, last_visit_subq.c.row_num == 1),
        )
        .all()
    )

    cat_dashboards = [
        CatDashboard(
            cat_id=cat.id,
            cat_name=cat.name,
            reference_weight_kg=cat.reference_weight_kg,
            photo_url=f"/uploads/cat_photos/{cat.id}.jpg" if cat.photo_path else None,
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

    if update_mode == "webhook":
        poller_healthy = True   # webhook mode: healthy as long as app is running
    else:
        poller_healthy = (
            last_poll is not None
            and (now - last_poll).total_seconds() < POLLER_HEALTHY_THRESHOLD_SECONDS
        )

    return DashboardOut(
        cats=cat_dashboards,
        unidentified_visits_today=unidentified_today,
        cleaning_cycles_today=cleaning_cycles_today,
        poller_healthy=poller_healthy,
        poller_last_successful_at=last_poll,
        poller_last_attempted_at=last_attempt,
        poller_last_error=poll_error,
        generated_at=now,
    )
