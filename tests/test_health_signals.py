from datetime import datetime, timezone, timedelta

from app.health_signals import PollerHealthContext, compute_health_signals
from app.models import Cat, Visit


def add_visit(db_session, cat_id, started_at, weight_kg=None):
    visit = Visit(
        cat_id=cat_id,
        started_at=started_at,
        ended_at=started_at + timedelta(minutes=2),
        weight_kg=weight_kg,
    )
    db_session.add(visit)
    return visit


def signal_by_type(signals, signal_type):
    return next(signal for signal in signals if signal.type == signal_type)


def test_weight_decrease_signal_uses_cat_baseline(db_session):
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    cat = Cat(name="Plurk", reference_weight_kg=5.0)
    db_session.add(cat)
    db_session.commit()

    add_visit(db_session, cat.id, now - timedelta(days=30), weight_kg=5.0)
    add_visit(db_session, cat.id, now - timedelta(hours=1), weight_kg=4.7)
    db_session.commit()

    signals = compute_health_signals(db_session, [cat], now, PollerHealthContext(healthy=True))

    signal = signal_by_type(signals, "weight_down")
    assert signal.severity == "watch"
    assert signal.message == "Weight is down compared with 1 month ago."
    assert signal.metadata["baseline_weight_kg"] == 5.0
    assert signal.metadata["current_weight_kg"] == 4.7
    assert signal.cat_id == cat.id


def test_weight_increase_signal_promotes_larger_change(db_session):
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    cat = Cat(name="Miez", reference_weight_kg=5.0)
    db_session.add(cat)
    db_session.commit()

    add_visit(db_session, cat.id, now - timedelta(days=90), weight_kg=5.0)
    add_visit(db_session, cat.id, now - timedelta(minutes=30), weight_kg=5.6)
    db_session.commit()

    signals = compute_health_signals(db_session, [cat], now, PollerHealthContext(healthy=True))

    signal = signal_by_type(signals, "weight_up")
    assert signal.severity == "attention"
    assert signal.message == "Weight is up compared with 3 months ago."
    assert signal.metadata["change_percent"] == 12.0


def test_visit_frequency_signal_compares_recent_week_to_baseline(db_session):
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    cat = Cat(name="Luna")
    db_session.add(cat)
    db_session.commit()

    for days_ago in range(8, 29, 2):
        add_visit(db_session, cat.id, now - timedelta(days=days_ago))
    add_visit(db_session, cat.id, now - timedelta(days=1))
    db_session.commit()

    signals = compute_health_signals(db_session, [cat], now, PollerHealthContext(healthy=True))

    signal = signal_by_type(signals, "visits_lower")
    assert signal.severity == "attention"
    assert signal.message == "Visits are lower than usual this week."
    assert signal.metadata["current_visits"] == 1
    assert signal.metadata["baseline_window"] == "previous 21 days"


def test_sparse_data_stays_quiet(db_session):
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    cat = Cat(name="Sparse")
    db_session.add(cat)
    db_session.commit()

    add_visit(db_session, cat.id, now - timedelta(days=1), weight_kg=4.2)
    add_visit(db_session, cat.id, now - timedelta(days=10))
    db_session.commit()

    signals = compute_health_signals(db_session, [cat], now, PollerHealthContext(healthy=True))

    assert signals == []


def test_repeated_unidentified_visits_create_data_quality_signal(db_session):
    now = datetime(2026, 5, 17, 12, 0, tzinfo=timezone.utc)
    cat = Cat(name="Known")
    db_session.add(cat)
    db_session.commit()

    for days_ago in [1, 2, 3]:
        add_visit(db_session, None, now - timedelta(days=days_ago))
    db_session.commit()

    signals = compute_health_signals(db_session, [cat], now, PollerHealthContext(healthy=True))

    signal = signal_by_type(signals, "unidentified_visits")
    assert signal.severity == "watch"
    assert signal.message == "Several visits could not be assigned to a cat."
    assert signal.metadata["unidentified_visits"] == 3
