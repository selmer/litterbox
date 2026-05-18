from sqlalchemy import and_, case

from app.models import Visit

TRUSTED_DURATION_SOURCES = {"status_dp", "report_log_counter", "report_log_duration", "manual"}
LEGACY_TIMEOUT_SECONDS = 1800


def is_trusted_duration(visit: Visit) -> bool:
    if visit.duration_seconds is None:
        return False
    if visit.duration_is_estimated:
        return False
    if visit.duration_source not in TRUSTED_DURATION_SOURCES:
        return False
    return True


def trusted_duration_seconds(visit: Visit) -> int | None:
    return visit.duration_seconds if is_trusted_duration(visit) else None


def trusted_duration_expr():
    return case(
        (
            and_(
                Visit.duration_seconds.isnot(None),
                Visit.duration_is_estimated.is_(False),
                Visit.duration_source.in_(tuple(TRUSTED_DURATION_SOURCES)),
                ~and_(
                    Visit.duration_source == "unknown",
                    Visit.duration_seconds >= LEGACY_TIMEOUT_SECONDS,
                ),
            ),
            Visit.duration_seconds,
        ),
        else_=None,
    )


def likely_legacy_timeout_filter():
    return and_(
        Visit.duration_source == "unknown",
        Visit.duration_seconds >= LEGACY_TIMEOUT_SECONDS,
        Visit.duration_is_estimated.is_(False),
    )
