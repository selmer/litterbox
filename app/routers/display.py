from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cat, CleaningCycle, Visit
from app.durations import trusted_duration_expr, trusted_duration_seconds
from app.schemas import (
    DisplayCatSummary,
    DisplayChart,
    DisplayChartPoint,
    DisplayLatestVisit,
    DisplayStatus,
    DisplaySummaryOut,
    DisplayToday,
    DisplayWeightComparison,
)
from app.routers import dashboard as dashboard_state

router = APIRouter(prefix="/display", tags=["display"])

DISPLAY_REFRESH_SECONDS = 60 * 60
DISPLAY_CHART_DAYS = 30
MIN_CHART_POINTS = 2
ONE_MONTH_LOOKBACK_DAYS = 30
THREE_MONTH_LOOKBACK_DAYS = 90
ONE_MONTH_TOLERANCE_DAYS = 14
THREE_MONTH_TOLERANCE_DAYS = 21
SPARKLINE_POINTS = 4


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
        db.query(func.sum(func.coalesce(trusted_duration_expr(), 0)))
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
            duration_seconds=trusted_duration_seconds(visit),
            weight_kg=visit.weight_kg,
            identified_by=visit.identified_by,
        ),
        visit.cat_id,
    )


def _comparison_for_visit(latest: Visit | None, historical: Visit | None) -> DisplayWeightComparison | None:
    if latest is None or latest.weight_kg is None or historical is None or historical.weight_kg is None:
        return None
    return DisplayWeightComparison(
        weight_kg=historical.weight_kg,
        measured_at=historical.started_at,
        delta_kg=round(latest.weight_kg - historical.weight_kg, 3),
    )


def _nearest_historical_weight(
    visits: list[Visit],
    target: datetime,
    tolerance: timedelta,
    latest_visit_id: int | None,
) -> Visit | None:
    best_visit = None
    best_distance = None
    for visit in visits:
        if latest_visit_id is not None and visit.id == latest_visit_id:
            continue
        distance = abs(_as_utc(visit.started_at) - target)
        if distance > tolerance:
            continue
        if best_distance is None or distance < best_distance:
            best_visit = visit
            best_distance = distance
    return best_visit


def _sparkline_values(visits: list[Visit]) -> list[float]:
    if not visits:
        return []
    if len(visits) <= SPARKLINE_POINTS:
        return [visit.weight_kg for visit in visits if visit.weight_kg is not None]

    last_index = len(visits) - 1
    selected_indexes = []
    for index in range(SPARKLINE_POINTS):
        selected = round((last_index * index) / (SPARKLINE_POINTS - 1))
        if selected not in selected_indexes:
            selected_indexes.append(selected)
    return [visits[index].weight_kg for index in selected_indexes if visits[index].weight_kg is not None]


def _cat_summaries(db: Session, today_start: datetime, now: datetime) -> list[DisplayCatSummary]:
    today_counts = dict(
        db.query(Visit.cat_id, func.count(Visit.id))
        .filter(Visit.cat_id.isnot(None), Visit.started_at >= today_start)
        .group_by(Visit.cat_id)
        .all()
    )

    cats = (
        db.query(Cat)
        .filter(Cat.active == True)
        .order_by(Cat.name.asc(), Cat.id.asc())
        .all()
    )

    since = now - timedelta(days=THREE_MONTH_LOOKBACK_DAYS + THREE_MONTH_TOLERANCE_DAYS)
    result = []
    for cat in cats:
        visits = (
            db.query(Visit)
            .filter(
                Visit.cat_id == cat.id,
                Visit.weight_kg.isnot(None),
                Visit.started_at >= since,
                Visit.started_at <= now,
            )
            .order_by(Visit.started_at.asc(), Visit.id.asc())
            .all()
        )
        latest = visits[-1] if visits else None
        one_month = _nearest_historical_weight(
            visits,
            now - timedelta(days=ONE_MONTH_LOOKBACK_DAYS),
            timedelta(days=ONE_MONTH_TOLERANCE_DAYS),
            latest.id if latest else None,
        )
        three_months = _nearest_historical_weight(
            visits,
            now - timedelta(days=THREE_MONTH_LOOKBACK_DAYS),
            timedelta(days=THREE_MONTH_TOLERANCE_DAYS),
            latest.id if latest else None,
        )

        result.append(
            DisplayCatSummary(
                name=cat.name,
                visits_today=int(today_counts.get(cat.id, 0)),
                last_weight_kg=latest.weight_kg if latest else None,
                latest_weight_kg=latest.weight_kg if latest else None,
                latest_weight_at=latest.started_at if latest else None,
                one_month_ago=_comparison_for_visit(latest, one_month),
                three_months_ago=_comparison_for_visit(latest, three_months),
                sparkline=_sparkline_values(visits),
            )
        )

    return result


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
        cats=_cat_summaries(db, today_start, now),
        alert=_alert(status, latest_visit, today),
    )
