from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Visit, VisitDiagnostic
from app.routers import dashboard as dashboard_state
from app.routers.display import get_display_summary
from app.schemas import (
    DiagnosticsEndpointOut,
    DiagnosticsOpenVisitOut,
    DiagnosticsOpenVisitsOut,
    DiagnosticsPollerOut,
    DiagnosticsReconciliationOut,
    DiagnosticsSummaryOut,
    VisitDiagnosticOut,
)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

RECENT_DIAGNOSTIC_LIMIT = 25
REDACTED = "[redacted]"
SENSITIVE_KEY_PARTS = ("secret", "token", "password", "credential", "api_key", "apikey", "auth")
RECONCILIATION_EVENT_TYPES = {
    "reconciliation_attempt",
    "report_logs_fetched",
    "pending_retry",
    "completion_matched",
    "hard_timeout",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                redacted[key_text] = REDACTED
            else:
                redacted[key_text] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def _poller_summary(now: datetime) -> DiagnosticsPollerOut:
    with dashboard_state._poll_lock:
        last_successful = dashboard_state.last_successful_poll_at
        last_attempted = dashboard_state.last_poll_attempted_at
        last_error = dashboard_state.last_poll_error
        update_mode = dashboard_state.update_mode

    if update_mode == "webhook":
        healthy = True
    else:
        healthy = (
            last_successful is not None
            and (now - _as_utc(last_successful)).total_seconds() < dashboard_state.POLLER_HEALTHY_THRESHOLD_SECONDS
        )

    return DiagnosticsPollerOut(
        mode=update_mode,
        healthy=healthy,
        last_successful_at=last_successful,
        last_attempted_at=last_attempted,
        last_error=last_error,
        interval_seconds=dashboard_state.POLL_INTERVAL_SECONDS,
        healthy_threshold_seconds=dashboard_state.POLLER_HEALTHY_THRESHOLD_SECONDS,
    )


def _open_visits_summary(db: Session, now: datetime) -> DiagnosticsOpenVisitsOut:
    visits = (
        db.query(Visit)
        .filter(Visit.ended_at.is_(None))
        .order_by(Visit.started_at.asc(), Visit.id.asc())
        .all()
    )
    open_visits = [
        DiagnosticsOpenVisitOut(
            id=visit.id,
            cat_id=visit.cat_id,
            identified_by=visit.identified_by,
            started_at=visit.started_at,
            age_seconds=max(0, int((now - _as_utc(visit.started_at)).total_seconds())),
            weight_kg=visit.weight_kg,
            last_weight_at=visit.last_weight_at,
            duration_source=visit.duration_source,
        )
        for visit in visits
    ]
    oldest = open_visits[0] if open_visits else None
    return DiagnosticsOpenVisitsOut(
        count=len(open_visits),
        oldest_started_at=oldest.started_at if oldest else None,
        oldest_age_seconds=oldest.age_seconds if oldest else None,
        visits=open_visits,
    )


def _recent_diagnostics(db: Session) -> list[VisitDiagnosticOut]:
    rows = (
        db.query(VisitDiagnostic)
        .order_by(VisitDiagnostic.recorded_at.desc(), VisitDiagnostic.id.desc())
        .limit(RECENT_DIAGNOSTIC_LIMIT)
        .all()
    )
    return [
        VisitDiagnosticOut(
            id=row.id,
            visit_id=row.visit_id,
            event_type=row.event_type,
            payload=_redact(row.payload or {}),
            recorded_at=row.recorded_at,
        )
        for row in rows
    ]


def _reconciliation_summary(db: Session) -> DiagnosticsReconciliationOut:
    rows = (
        db.query(VisitDiagnostic.event_type, func.count(VisitDiagnostic.id), func.max(VisitDiagnostic.recorded_at))
        .filter(VisitDiagnostic.event_type.in_(RECONCILIATION_EVENT_TYPES))
        .group_by(VisitDiagnostic.event_type)
        .all()
    )
    counts = {event_type: int(count) for event_type, count, _ in rows}
    latest_values = [latest for _, _, latest in rows if latest is not None]
    return DiagnosticsReconciliationOut(
        reconciliation_attempts=counts.get("reconciliation_attempt", 0),
        report_logs_fetched=counts.get("report_logs_fetched", 0),
        pending_retries=counts.get("pending_retry", 0),
        completion_matches=counts.get("completion_matched", 0),
        hard_timeouts=counts.get("hard_timeout", 0),
        latest_event_at=max(latest_values) if latest_values else None,
    )


@router.get("/summary", response_model=DiagnosticsSummaryOut)
def get_diagnostics_summary(db: Session = Depends(get_db)):
    now = _utc_now()
    return DiagnosticsSummaryOut(
        generated_at=now,
        poller=_poller_summary(now),
        open_visits=_open_visits_summary(db, now),
        recent_diagnostics=_recent_diagnostics(db),
        reconciliation=_reconciliation_summary(db),
        display=get_display_summary(db),
        endpoints=[
            DiagnosticsEndpointOut(label="Diagnostics summary", method="GET", path="/diagnostics/summary"),
            DiagnosticsEndpointOut(label="Display summary", method="GET", path="/display/summary"),
            DiagnosticsEndpointOut(label="Visits", method="GET", path="/visits?limit=50"),
            DiagnosticsEndpointOut(label="Visit diagnostics", method="GET", path="/visits/{visit_id}/diagnostics"),
            DiagnosticsEndpointOut(label="OpenAPI", method="GET", path="/openapi.json"),
        ],
    )
