"""Tests for LitterboxPoller business logic.

These tests use an in-memory SQLite database to verify that the poller
correctly creates and updates Visits, CleaningCycles, DeviceSnapshots,
and SettingsHistory records.

The Tuya cloud connection is mocked out — see the `poller` fixture in conftest.py.
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# _handle_weight_update
# ---------------------------------------------------------------------------

def test_weight_update_creates_new_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)

    visits = db_session.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].weight_kg == pytest.approx(4.1)
    assert visits[0].started_at == NOW


def test_weight_update_sets_current_visit(poller):
    assert poller.current_visit is None
    poller._handle_weight_update(4100, NOW)
    assert poller.current_visit is not None


def test_weight_update_updates_existing_visit(poller, db_session):
    # First reading starts a visit
    poller._handle_weight_update(4100, NOW)
    # Second reading (different weight) updates the same visit
    poller._handle_weight_update(4200, NOW + timedelta(seconds=10))

    visits = db_session.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].weight_kg == pytest.approx(4.2)


def test_weight_update_records_last_weight_at(poller):
    poller._handle_weight_update(4100, NOW)
    assert poller.last_weight_at == NOW


# ---------------------------------------------------------------------------
# _handle_visit_complete
# ---------------------------------------------------------------------------

def test_visit_complete_closes_current_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    dps = {"excretion_time_day": 45, "cat_weight": 4100, "excretion_times_day": 1}

    poller._handle_visit_complete(dps, NOW + timedelta(seconds=45))

    visit = db_session.query(Visit).first()
    assert visit.ended_at is not None
    assert visit.duration_seconds == 45
    assert poller.current_visit is None


def test_visit_complete_without_prior_visit_creates_one(poller, db_session):
    """If a completion event arrives without a preceding weight event, a visit is created."""
    dps = {"excretion_time_day": 30, "cat_weight": 4100, "excretion_times_day": 1}

    poller._handle_visit_complete(dps, NOW)

    visits = db_session.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].duration_seconds == 30


def test_visit_complete_assigns_cat_when_matching_weight(poller, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db_session.add(cat)
    db_session.commit()

    poller._handle_weight_update(4050, NOW)
    dps = {"excretion_time_day": 60, "cat_weight": 4050, "excretion_times_day": 1}
    poller._handle_visit_complete(dps, NOW + timedelta(seconds=60))

    visit = db_session.query(Visit).first()
    assert visit.cat_id == cat.id
    assert visit.identified_by == "auto"


def test_visit_complete_leaves_cat_unassigned_for_unknown_weight(poller, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db_session.add(cat)
    db_session.commit()

    # Weight far outside any cat's threshold
    poller._handle_weight_update(1000, NOW)
    dps = {"excretion_time_day": 60, "cat_weight": 1000, "excretion_times_day": 1}
    poller._handle_visit_complete(dps, NOW + timedelta(seconds=60))

    visit = db_session.query(Visit).first()
    assert visit.cat_id is None


# ---------------------------------------------------------------------------
# _check_visit_timeout
# ---------------------------------------------------------------------------

def test_visit_timeout_closes_overdue_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    far_future = NOW + timedelta(seconds=400)  # > VISIT_TIMEOUT_SECONDS (300)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at is not None
    assert poller.current_visit is None


def test_visit_timeout_does_not_close_recent_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    soon_after = NOW + timedelta(seconds=100)  # < VISIT_TIMEOUT_SECONDS

    poller._check_visit_timeout(soon_after)

    assert poller.current_visit is not None


def test_visit_timeout_does_nothing_without_visit(poller):
    # Should not raise
    poller._check_visit_timeout(NOW)
    assert poller.current_visit is None


# ---------------------------------------------------------------------------
# _handle_cleaning_cycle
# ---------------------------------------------------------------------------

def test_cleaning_cycle_starts_on_true(poller, db_session):
    poller._handle_cleaning_cycle(True, NOW)

    cycles = db_session.query(CleaningCycle).all()
    assert len(cycles) == 1
    assert cycles[0].started_at == NOW
    assert cycles[0].ended_at is None
    assert poller.current_cleaning_cycle is not None


def test_cleaning_cycle_ends_on_false(poller, db_session):
    poller._handle_cleaning_cycle(True, NOW)
    end_time = NOW + timedelta(minutes=5)
    poller._handle_cleaning_cycle(False, end_time)

    cycle = db_session.query(CleaningCycle).first()
    assert cycle.ended_at == end_time
    assert poller.current_cleaning_cycle is None


def test_cleaning_cycle_false_without_active_cycle_is_noop(poller, db_session):
    poller._handle_cleaning_cycle(False, NOW)
    assert db_session.query(CleaningCycle).count() == 0


def test_cleaning_cycle_true_while_already_active_is_noop(poller, db_session):
    poller._handle_cleaning_cycle(True, NOW)
    poller._handle_cleaning_cycle(True, NOW + timedelta(seconds=10))

    assert db_session.query(CleaningCycle).count() == 1


# ---------------------------------------------------------------------------
# _record_setting_change
# ---------------------------------------------------------------------------

def test_record_setting_change_saves_entry(poller, db_session):
    poller._record_setting_change("deodorization", True, NOW)

    entries = db_session.query(SettingsHistory).all()
    assert len(entries) == 1
    assert entries[0].dp == "deodorization"
    assert entries[0].value == "True"
    assert entries[0].changed_at == NOW


def test_record_multiple_setting_changes(poller, db_session):
    poller._record_setting_change("child_lock", False, NOW)
    poller._record_setting_change("child_lock", True, NOW + timedelta(seconds=5))

    assert db_session.query(SettingsHistory).count() == 2


# ---------------------------------------------------------------------------
# _maybe_snapshot
# ---------------------------------------------------------------------------

def test_maybe_snapshot_saves_on_first_call(poller, db_session):
    dps = {"cat_weight": 0, "smart_clean": False}
    poller._maybe_snapshot(dps, NOW)

    snapshots = db_session.query(DeviceSnapshot).all()
    assert len(snapshots) == 1
    assert snapshots[0].raw_dps == dps


def test_maybe_snapshot_skips_if_interval_not_elapsed(poller, db_session):
    dps = {"cat_weight": 0}
    poller._maybe_snapshot(dps, NOW)
    poller._maybe_snapshot(dps, NOW + timedelta(seconds=10))

    assert db_session.query(DeviceSnapshot).count() == 1


def test_maybe_snapshot_saves_after_interval(poller, db_session):
    from app.poller import SNAPSHOT_INTERVAL_SECONDS
    dps = {"cat_weight": 0}
    poller._maybe_snapshot(dps, NOW)
    poller._maybe_snapshot(dps, NOW + timedelta(seconds=SNAPSHOT_INTERVAL_SECONDS + 1))

    assert db_session.query(DeviceSnapshot).count() == 2


# ---------------------------------------------------------------------------
# _identify_visit_cat (weight update reference weight)
# ---------------------------------------------------------------------------

def test_identify_visit_cat_updates_reference_weight(poller, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db_session.add(cat)
    db_session.commit()

    visit = Visit(started_at=NOW, weight_kg=4.2)
    db_session.add(visit)
    db_session.commit()

    poller._identify_visit_cat(visit, 4.2)
    db_session.refresh(cat)

    # Reference weight should have been nudged toward 4.2
    assert cat.reference_weight_kg != pytest.approx(4.0)
    assert 4.0 < cat.reference_weight_kg < 4.2
