import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, CleaningCycle, Visit
from app.schemas import CatDashboard, DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Mirror the same env var as the poller so the health window scales automatically.
# Defaults to 2× the poll interval — healthy as long as the last poll was within
# the previous two cycles. Override via POLLER_HEALTHY_THRESHOLD_SECONDS if needed.
_poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
POLLER_HEALTHY_THRESHOLD_SECONDS = int(
    os.getenv("POLLER_HEALTHY_THRESHOLD_SECONDS", str(_poll_interval * 2))
)

# Shared state updated by the poller — imported in main.py
last_successful_poll_at: datetime = None


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    from app.routers.dashboard import last_successful_poll_at

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    active_cats = db.query(Cat).filter(Cat.active == True).all()

    cat_dashboards = []
    for cat in active_cats:
        visits_today = (
            db.query(Visit)
            .filter(
                Visit.cat_id == cat.id,
                Visit.started_at >= today_start,
            )
            .all()
        )

        total_time = sum(v.duration_seconds or 0 for v in visits_today)

        last_visit = (
            db.query(Visit)
            .filter(
                Visit.cat_id == cat.id,
            )
            .order_by(Visit.started_at.desc())
            .first()
        )

        cat_dashboards.append(
            CatDashboard(
                cat_id=cat.id,
                cat_name=cat.name,
                reference_weight_kg=cat.reference_weight_kg,
                visits_today=len(visits_today),
                time_in_box_today_seconds=total_time,
                last_visit_at=last_visit.started_at if last_visit else None,
                last_visit_weight_kg=last_visit.weight_kg if last_visit else None,
                last_visit_duration_seconds=last_visit.duration_seconds if last_visit else None,
            )
        )

    unidentified_today = (
        db.query(Visit)
        .filter(
            Visit.cat_id.is_(None),
            Visit.started_at >= today_start,
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
