from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, CleaningCycle, Visit
from app.schemas import (
    DisplayCatSummary,
    DisplayChart,
    DisplayChartPoint,
    DisplayLatestVisit,
    DisplayStatus,
    DisplaySummaryOut,
    DisplayToday,
)
from app.routers import dashboard as dashboard_state

router = APIRouter(prefix="/display", tags=["display"])

DISPLAY_REFRESH_SECONDS = dashboard_state.POLL_INTERVAL_SECONDS
DISPLAY_CHART_DAYS = 30
MIN_CHART_POINTS = 2


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_time_ago(value: datetime, now: datetime) -> str:
    seconds = max(0, int((now - _as_utc(value)).total_seconds()))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return "1 minute ago" if minutes == 1 else f"{minutes} minutes ago"
    hours = minutes // 60
    if hours < 24:
        return "about 1 hour ago" if hours == 1 else f"about {hours} hours ago"
    days = hours // 24
    return "1 day ago" if days == 1 else f"{days} days ago"


def _poller_status(now: datetime) -> DisplayStatus:
    with dashboard_state._poll_lock:
        last_poll = dashboard_state.last_successful_poll_at
        poll_error = dashboard_state.last_poll_error
        update_mode = dashboard_state.update_mode

    if update_mode == "webhook":
        healthy = True
        label = "Webhook"
    else:
        healthy = (
            last_poll is not None
            and (now - _as_utc(last_poll)).total_seconds() < dashboard_state.POLLER_HEALTHY_THRESHOLD_SECONDS
        )
        label = "Polling"

    message = None
    if not healthy:
        message = poll_error or (
            "Poller has not reported successfully yet."
            if last_poll is None
            else "Poller data is stale."
        )

    return DisplayStatus(
        label=label,
        healthy=healthy,
        last_successful_at=last_poll,
        message=message,
    )


def _today_start(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _today_summary(db: Session, today_start: datetime) -> DisplayToday:
    visits_today = (
        db.query(Visit)
        .filter(Visit.started_at >= today_start)
        .count()
    )
    time_in_box = (
        db.query(func.sum(func.coalesce(Visit.duration_seconds, 0)))
        .filter(Visit.started_at >= today_start)
        .scalar()
        or 0
    )
    cleaning_cycles = (
        db.query(CleaningCycle)
        .filter(CleaningCycle.started_at >= today_start)
        .count()
    )
    unidentified = (
        db.query(Visit)
        .filter(
            Visit.cat_id.is_(None),
            Visit.started_at >= today_start,
            Visit.ended_at.isnot(None),
        )
        .count()
    )
    return DisplayToday(
        visits=visits_today,
        time_in_box_seconds=int(time_in_box),
        cleaning_cycles=cleaning_cycles,
        unidentified_visits=unidentified,
    )


def _latest_visit(db: Session, now: datetime) -> tuple[DisplayLatestVisit | None, int | None]:
    visit = (
        db.query(Visit)
        .order_by(Visit.started_at.desc(), Visit.id.desc())
        .first()
    )
    if visit is None:
        return None, None

    cat_name = "Unknown cat"
    identified = False
    if visit.cat_id is not None and visit.cat is not None:
        cat_name = visit.cat.name
        identified = True

    return (
        DisplayLatestVisit(
            cat_name=cat_name,
            identified=identified,
            started_at=visit.started_at,
            time_ago_label=_format_time_ago(visit.started_at, now),
            duration_seconds=visit.duration_seconds,
            weight_kg=visit.weight_kg,
            identified_by=visit.identified_by,
        ),
        visit.cat_id,
    )


def _cat_summaries(db: Session, today_start: datetime) -> list[DisplayCatSummary]:
    today_subq = (
        db.query(
            Visit.cat_id,
            func.count(Visit.id).label("visits_today"),
        )
        .filter(Visit.cat_id.isnot(None), Visit.started_at >= today_start)
        .group_by(Visit.cat_id)
        .subquery()
    )

    latest_subq = (
        db.query(
            Visit.cat_id.label("cat_id"),
            Visit.weight_kg.label("weight_kg"),
            func.row_number()
            .over(
                partition_by=Visit.cat_id,
                order_by=(Visit.started_at.desc(), Visit.id.desc()),
            )
            .label("row_num"),
        )
        .filter(Visit.cat_id.isnot(None), Visit.weight_kg.isnot(None))
        .subquery()
    )

    rows = (
        db.query(
            Cat.name,
            func.coalesce(today_subq.c.visits_today, 0),
            latest_subq.c.weight_kg,
        )
        .filter(Cat.active == True)
        .outerjoin(today_subq, Cat.id == today_subq.c.cat_id)
        .outerjoin(
            latest_subq,
            and_(Cat.id == latest_subq.c.cat_id, latest_subq.c.row_num == 1),
        )
        .order_by(Cat.name.asc(), Cat.id.asc())
        .all()
    )

    return [
        DisplayCatSummary(
            name=name,
            visits_today=int(visits_today),
            last_weight_kg=weight_kg,
        )
        for name, visits_today, weight_kg in rows
    ]


def _chart_cat_id(db: Session, latest_visit_cat_id: int | None, since: datetime) -> int | None:
    if latest_visit_cat_id is not None:
        count = (
            db.query(Visit)
            .filter(
                Visit.cat_id == latest_visit_cat_id,
                Visit.started_at >= since,
                Visit.weight_kg.isnot(None),
            )
            .count()
        )
        return latest_visit_cat_id if count >= MIN_CHART_POINTS else None

    row = (
        db.query(Visit.cat_id, func.count(Visit.id).label("points"))
        .join(Cat, Cat.id == Visit.cat_id)
        .filter(
            Cat.active == True,
            Visit.started_at >= since,
            Visit.weight_kg.isnot(None),
        )
        .group_by(Visit.cat_id)
        .having(func.count(Visit.id) >= MIN_CHART_POINTS)
        .order_by(func.max(Visit.started_at).desc())
        .first()
    )
    return row[0] if row else None


def _weight_chart(db: Session, latest_visit_cat_id: int | None, now: datetime) -> DisplayChart | None:
    since = now - timedelta(days=DISPLAY_CHART_DAYS)
    cat_id = _chart_cat_id(db, latest_visit_cat_id, since)
    if cat_id is None:
        return None

    visits = (
        db.query(Visit)
        .filter(
            Visit.cat_id == cat_id,
            Visit.started_at >= since,
            Visit.weight_kg.isnot(None),
        )
        .order_by(Visit.started_at.asc(), Visit.id.asc())
        .all()
    )
    if len(visits) < MIN_CHART_POINTS:
        return None

    points = [
        DisplayChartPoint(
            date=_as_utc(visit.started_at).date().isoformat(),
            weight_kg=visit.weight_kg,
        )
        for visit in visits
    ]
    weights = [point.weight_kg for point in points]
    return DisplayChart(
        label="30d weight",
        unit="kg",
        min_kg=min(weights),
        max_kg=max(weights),
        points=points,
    )


def _alert(status: DisplayStatus, latest_visit: DisplayLatestVisit | None, today: DisplayToday) -> str | None:
    if not status.healthy:
        return status.message or "Device data may be stale."
    if latest_visit is not None and not latest_visit.identified:
        return "Latest visit is unidentified."
    if today.unidentified_visits > 0:
        return f"{today.unidentified_visits} unidentified visit today."
    return None


@router.get("/summary", response_model=DisplaySummaryOut)
def get_display_summary(db: Session = Depends(get_db)):
    now = _utc_now()
    today_start = _today_start(now)
    status = _poller_status(now)
    latest_visit, latest_visit_cat_id = _latest_visit(db, now)
    today = _today_summary(db, today_start)

    return DisplaySummaryOut(
        generated_at=now,
        refresh_after_seconds=DISPLAY_REFRESH_SECONDS,
        status=status,
        latest_visit=latest_visit,
        today=today,
        chart=_weight_chart(db, latest_visit_cat_id, now),
        cats=_cat_summaries(db, today_start),
        alert=_alert(status, latest_visit, today),
    )
