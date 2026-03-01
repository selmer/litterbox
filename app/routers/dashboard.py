from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
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
                photo_url=cat.photo_url,
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
