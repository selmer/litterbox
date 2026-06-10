from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import Cat, Visit
from app.schemas import HealthSignal
from app.timezones import as_utc


# 031 choice log:
# - Weight changes are signalled at >=5% because smaller changes are common noise
#   in litterbox scale data. >=10% is promoted to attention.
# - Visit frequency compares the last 7 days with the previous 21 days normalized
#   to a weekly count. It requires a modest baseline so sparse data stays quiet.
# - Unidentified activity is global, recent, and only appears after repeated events.
# - All messages are prompts, not diagnoses; metadata carries the visible numbers.
ONE_MONTH_DAYS = 30
THREE_MONTH_DAYS = 90
ONE_MONTH_TOLERANCE_DAYS = 14
THREE_MONTH_TOLERANCE_DAYS = 21
WEIGHT_WATCH_PERCENT = 5.0
WEIGHT_ATTENTION_PERCENT = 10.0
VISIT_CURRENT_DAYS = 7
VISIT_BASELINE_DAYS = 21
VISIT_BASELINE_MIN_VISITS = 6
VISIT_BASELINE_MIN_WEEKLY = 2.0
VISIT_WATCH_PERCENT = 40.0
VISIT_ATTENTION_PERCENT = 70.0
UNIDENTIFIED_WATCH_COUNT = 3
UNIDENTIFIED_ATTENTION_COUNT = 6

SEVERITY_RANK = {"attention": 3, "watch": 2, "info": 1}


@dataclass(frozen=True)
class PollerHealthContext:
    healthy: bool
    last_successful_at: datetime | None = None
    last_error: str | None = None


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _change_percent(current: float, baseline: float) -> float:
    return ((current - baseline) / baseline) * 100


def _severity_for_percent(abs_percent: float) -> str:
    return "attention" if abs_percent >= WEIGHT_ATTENTION_PERCENT else "watch"


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
        distance = abs(as_utc(visit.started_at) - target)
        if distance > tolerance:
            continue
        if best_distance is None or distance < best_distance:
            best_visit = visit
            best_distance = distance
    return best_visit


def _weight_signal_for_window(
    cat: Cat,
    latest: Visit,
    historical: Visit | None,
    window_label: str,
    signal_suffix: str,
) -> HealthSignal | None:
    if historical is None or latest.weight_kg is None or historical.weight_kg is None:
        return None

    percent = _change_percent(latest.weight_kg, historical.weight_kg)
    abs_percent = abs(percent)
    if abs_percent < WEIGHT_WATCH_PERCENT:
        return None

    direction = "up" if percent > 0 else "down"
    message = f"Weight is {direction} compared with {window_label} ago."
    return HealthSignal(
        id=f"cat:{cat.id}:weight_{signal_suffix}:{direction}",
        type=f"weight_{direction}",
        severity=_severity_for_percent(abs_percent),
        cat_id=cat.id,
        cat_name=cat.name,
        message=message,
        detail=(
            f"{_round(latest.weight_kg, 3)} kg now vs "
            f"{_round(historical.weight_kg, 3)} kg around {window_label} ago."
        ),
        metadata={
            "comparison_window": window_label,
            "current_weight_kg": _round(latest.weight_kg, 3),
            "baseline_weight_kg": _round(historical.weight_kg, 3),
            "change_kg": _round(latest.weight_kg - historical.weight_kg, 3),
            "change_percent": _round(percent, 1),
            "current_measured_at": latest.started_at,
            "baseline_measured_at": historical.started_at,
        },
    )


def _weight_signals_for_cat(db: Session, cat: Cat, now: datetime) -> list[HealthSignal]:
    since = now - timedelta(days=THREE_MONTH_DAYS + THREE_MONTH_TOLERANCE_DAYS)
    visits = (
        db.query(Visit)
        .filter(
            Visit.cat_id == cat.id,
            Visit.weight_kg.isnot(None),
            Visit.weight_confidence != "ignored",
            Visit.started_at >= since,
            Visit.started_at <= now,
        )
        .order_by(Visit.started_at.asc(), Visit.id.asc())
        .all()
    )
    latest = visits[-1] if visits else None
    if latest is None:
        return []

    one_month = _nearest_historical_weight(
        visits,
        now - timedelta(days=ONE_MONTH_DAYS),
        timedelta(days=ONE_MONTH_TOLERANCE_DAYS),
        latest.id,
    )
    three_months = _nearest_historical_weight(
        visits,
        now - timedelta(days=THREE_MONTH_DAYS),
        timedelta(days=THREE_MONTH_TOLERANCE_DAYS),
        latest.id,
    )

    return [
        signal
        for signal in [
            _weight_signal_for_window(cat, latest, one_month, "1 month", "1m"),
            _weight_signal_for_window(cat, latest, three_months, "3 months", "3m"),
        ]
        if signal is not None
    ]


def _visit_frequency_signal_for_cat(db: Session, cat: Cat, now: datetime) -> HealthSignal | None:
    current_start = now - timedelta(days=VISIT_CURRENT_DAYS)
    baseline_start = current_start - timedelta(days=VISIT_BASELINE_DAYS)

    current_count = (
        db.query(Visit)
        .filter(
            Visit.cat_id == cat.id,
            Visit.started_at >= current_start,
            Visit.started_at <= now,
        )
        .count()
    )
    baseline_count = (
        db.query(Visit)
        .filter(
            Visit.cat_id == cat.id,
            Visit.started_at >= baseline_start,
            Visit.started_at < current_start,
        )
        .count()
    )
    baseline_weekly = baseline_count * (VISIT_CURRENT_DAYS / VISIT_BASELINE_DAYS)
    if baseline_count < VISIT_BASELINE_MIN_VISITS or baseline_weekly < VISIT_BASELINE_MIN_WEEKLY:
        return None

    percent = _change_percent(current_count, baseline_weekly)
    abs_percent = abs(percent)
    if abs_percent < VISIT_WATCH_PERCENT:
        return None

    direction = "higher" if percent > 0 else "lower"
    severity = "attention" if abs_percent >= VISIT_ATTENTION_PERCENT else "watch"
    return HealthSignal(
        id=f"cat:{cat.id}:visit_frequency:{direction}",
        type=f"visits_{direction}",
        severity=severity,
        cat_id=cat.id,
        cat_name=cat.name,
        message=f"Visits are {direction} than usual this week.",
        detail=(
            f"{current_count} visits in the last 7 days vs "
            f"{_round(baseline_weekly, 1)} per week recently."
        ),
        metadata={
            "comparison_window": "last 7 days",
            "baseline_window": "previous 21 days",
            "current_visits": current_count,
            "baseline_visits": baseline_count,
            "baseline_weekly_visits": _round(baseline_weekly, 1),
            "change_percent": _round(percent, 1),
        },
    )


def _unidentified_signal(db: Session, now: datetime) -> HealthSignal | None:
    since = now - timedelta(days=VISIT_CURRENT_DAYS)
    count = (
        db.query(Visit)
        .filter(
            Visit.cat_id.is_(None),
            Visit.ended_at.isnot(None),
            Visit.started_at >= since,
            Visit.started_at <= now,
        )
        .count()
    )
    if count < UNIDENTIFIED_WATCH_COUNT:
        return None

    return HealthSignal(
        id="global:unidentified_visits",
        type="unidentified_visits",
        severity="attention" if count >= UNIDENTIFIED_ATTENTION_COUNT else "watch",
        message="Several visits could not be assigned to a cat.",
        detail=f"{count} unidentified visits in the last 7 days.",
        metadata={
            "comparison_window": "last 7 days",
            "unidentified_visits": count,
        },
    )


def _poller_stale_signal(poller: PollerHealthContext | None) -> HealthSignal | None:
    if poller is None or poller.healthy:
        return None
    return HealthSignal(
        id="global:poller_stale",
        type="stale_device_data",
        severity="attention",
        message="Device data may be stale.",
        detail=poller.last_error or "The poller has not reported successfully recently.",
        metadata={
            "last_successful_at": poller.last_successful_at,
            "last_error": poller.last_error,
        },
    )


def _signal_sort_key(signal: HealthSignal) -> tuple[int, int, str]:
    type_priority = {
        "stale_device_data": 5,
        "weight_down": 4,
        "weight_up": 3,
        "visits_lower": 3,
        "visits_higher": 2,
        "unidentified_visits": 1,
    }
    return (
        SEVERITY_RANK[signal.severity],
        type_priority.get(signal.type, 0),
        signal.id,
    )


def most_relevant_signal(signals: list[HealthSignal], cat_id: int) -> HealthSignal | None:
    cat_signals = [signal for signal in signals if signal.cat_id == cat_id]
    if not cat_signals:
        return None
    return sorted(cat_signals, key=_signal_sort_key, reverse=True)[0]


def compute_health_signals(
    db: Session,
    cats: list[Cat],
    now: datetime,
    poller: PollerHealthContext | None = None,
) -> list[HealthSignal]:
    signals: list[HealthSignal] = []
    now = as_utc(now)

    for cat in cats:
        signals.extend(_weight_signals_for_cat(db, cat, now))
        frequency_signal = _visit_frequency_signal_for_cat(db, cat, now)
        if frequency_signal is not None:
            signals.append(frequency_signal)

    unidentified = _unidentified_signal(db, now)
    if unidentified is not None:
        signals.append(unidentified)

    stale = _poller_stale_signal(poller)
    if stale is not None:
        signals.append(stale)

    return sorted(signals, key=_signal_sort_key, reverse=True)
