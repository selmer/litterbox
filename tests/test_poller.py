"""
Tests for LitterboxPoller.

The Tuya Cloud connection is mocked throughout — these tests exercise the
state-machine logic of the poller, not the network layer.

Functions/scenarios needing owner input:
  - What does the real Tuya device return for `cat_weight`, `excretion_times_day`,
    and `excretion_time_day`? The tests assume raw weight in grams (e.g. 4200 → 4.2 kg)
    and integer seconds for duration. Confirm these match the real device behaviour.
  - VISIT_TIMEOUT_SECONDS is 300. Should tests cover shorter timeouts for faster
    iteration, or is the production value the only one that matters?
  - Should _handle_visit_complete create a visit when `excretion_time_day` is
    missing (None) from the DPS? Currently it stores duration_seconds=None.
  - What DP values trigger cleaning cycle start/end? The tests assume `smart_clean`
    is True to start and False to end — confirm this matches the real device.
"""
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit
from app.poller import (
    DP_CAT_WEIGHT,
    DP_CLEANING_CYCLE,
    DP_EXCRETION_TIME,
    DP_EXCRETION_TIMES,
    SNAPSHOT_INTERVAL_SECONDS,
    VISIT_TIMEOUT_SECONDS,
    LitterboxPoller,
)


@pytest.fixture
def mock_cloud():
    """Patches make_cloud so no real Tuya calls are made."""
    with patch("app.poller.make_cloud") as mock_make:
        instance = MagicMock()
        instance.getstatus.return_value = {"success": True, "result": []}
        mock_make.return_value = instance
        yield instance


@pytest.fixture
def poller(db, mock_cloud):
    return LitterboxPoller(db)


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Weight update
# ---------------------------------------------------------------------------

class TestHandleWeightUpdate:
    def test_creates_new_visit_on_first_weight(self, poller, db):
        now = _now()
        poller._handle_weight_update(4200, now)  # 4200g → 4.2 kg

        visits = db.query(Visit).all()
        assert len(visits) == 1
        assert visits[0].weight_kg == pytest.approx(4.2)
        assert visits[0].started_at == now

    def test_updates_weight_on_existing_visit(self, poller, db):
        now = _now()
        poller._handle_weight_update(4200, now)
        poller._handle_weight_update(4300, now)  # updated reading

        visits = db.query(Visit).all()
        assert len(visits) == 1
        assert visits[0].weight_kg == pytest.approx(4.3)

    def test_records_last_weight_at(self, poller):
        now = _now()
        poller._handle_weight_update(4000, now)
        assert poller.last_weight_at == now


# ---------------------------------------------------------------------------
# Visit completion
# ---------------------------------------------------------------------------

class TestHandleVisitComplete:
    def test_closes_existing_visit(self, poller, db):
        now = _now()
        poller._handle_weight_update(4200, now)
        assert poller.current_visit is not None

        dps = {DP_EXCRETION_TIME: 90, DP_CAT_WEIGHT: 4200}
        complete_time = now + timedelta(seconds=90)
        poller._handle_visit_complete(dps, complete_time)

        assert poller.current_visit is None
        visit = db.query(Visit).first()
        assert visit.ended_at == complete_time
        assert visit.duration_seconds == 90

    def test_creates_visit_when_weight_was_missed(self, poller, db):
        """If we missed the weight DP, visit complete should still record the visit."""
        assert poller.current_visit is None
        dps = {DP_EXCRETION_TIME: 60, DP_CAT_WEIGHT: 4000}
        poller._handle_visit_complete(dps, _now())

        visits = db.query(Visit).all()
        assert len(visits) == 1
        assert visits[0].weight_kg == pytest.approx(4.0)

    def test_assigns_cat_when_weight_matches(self, poller, db):
        cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
        db.add(cat)
        db.commit()

        now = _now()
        poller._handle_weight_update(4100, now)  # 4.1 kg — within 0.5 kg threshold
        dps = {DP_EXCRETION_TIME: 75, DP_CAT_WEIGHT: 4100}
        poller._handle_visit_complete(dps, now + timedelta(seconds=75))

        visit = db.query(Visit).first()
        assert visit.cat_id == cat.id
        assert visit.identified_by == "auto"


# ---------------------------------------------------------------------------
# Visit timeout
# ---------------------------------------------------------------------------

class TestCheckVisitTimeout:
    def test_closes_visit_after_timeout(self, poller, db):
        start = _now()
        poller._handle_weight_update(4200, start)
        assert poller.current_visit is not None

        # Simulate time passing beyond timeout
        later = start + timedelta(seconds=VISIT_TIMEOUT_SECONDS + 1)
        poller._check_visit_timeout(later)

        assert poller.current_visit is None
        visit = db.query(Visit).first()
        assert visit.ended_at is not None

    def test_does_not_close_visit_before_timeout(self, poller, db):
        start = _now()
        poller._handle_weight_update(4200, start)

        just_before = start + timedelta(seconds=VISIT_TIMEOUT_SECONDS - 1)
        poller._check_visit_timeout(just_before)

        assert poller.current_visit is not None

    def test_no_op_when_no_current_visit(self, poller, db):
        poller._check_visit_timeout(_now())  # Should not raise
        assert db.query(Visit).count() == 0


# ---------------------------------------------------------------------------
# Cleaning cycle
# ---------------------------------------------------------------------------

class TestHandleCleaningCycle:
    def test_starts_cleaning_cycle(self, poller, db):
        poller._handle_cleaning_cycle(True, _now())
        assert poller.current_cleaning_cycle is not None
        assert db.query(CleaningCycle).count() == 1

    def test_ends_cleaning_cycle(self, poller, db):
        start = _now()
        poller._handle_cleaning_cycle(True, start)
        end = start + timedelta(minutes=3)
        poller._handle_cleaning_cycle(False, end)

        assert poller.current_cleaning_cycle is None
        cycle = db.query(CleaningCycle).first()
        assert cycle.ended_at == end

    def test_ignores_duplicate_start(self, poller, db):
        now = _now()
        poller._handle_cleaning_cycle(True, now)
        poller._handle_cleaning_cycle(True, now + timedelta(seconds=5))  # already running

        assert db.query(CleaningCycle).count() == 1

    def test_ignores_stop_when_not_running(self, poller, db):
        poller._handle_cleaning_cycle(False, _now())  # no cycle in progress
        assert db.query(CleaningCycle).count() == 0


# ---------------------------------------------------------------------------
# Settings recording
# ---------------------------------------------------------------------------

class TestRecordSettingChange:
    def test_records_setting(self, poller, db):
        poller._record_setting_change("child_lock", True, _now())

        entries = db.query(SettingsHistory).all()
        assert len(entries) == 1
        assert entries[0].dp == "child_lock"
        assert entries[0].value == "True"

    def test_records_multiple_settings(self, poller, db):
        now = _now()
        poller._record_setting_change("child_lock", True, now)
        poller._record_setting_change("odourless", False, now)

        assert db.query(SettingsHistory).count() == 2


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------

class TestMaybeSnapshot:
    def test_saves_snapshot_on_first_poll(self, poller, db):
        dps = {DP_CAT_WEIGHT: 0}
        poller._maybe_snapshot(dps, _now())

        assert db.query(DeviceSnapshot).count() == 1

    def test_skips_snapshot_within_interval(self, poller, db):
        now = _now()
        poller._maybe_snapshot({}, now)
        poller._maybe_snapshot({}, now + timedelta(seconds=10))  # too soon

        assert db.query(DeviceSnapshot).count() == 1

    def test_saves_snapshot_after_interval(self, poller, db):
        now = _now()
        poller._maybe_snapshot({}, now)
        poller._maybe_snapshot({}, now + timedelta(seconds=SNAPSHOT_INTERVAL_SECONDS + 1))

        assert db.query(DeviceSnapshot).count() == 2


# ---------------------------------------------------------------------------
# handle_changes dispatch
# ---------------------------------------------------------------------------

class TestHandleChanges:
    def test_dispatches_weight_change(self, poller, db):
        dps = {DP_CAT_WEIGHT: 4200}
        poller._handle_changes(dps, _now())
        assert db.query(Visit).count() == 1

    def test_ignores_unchanged_dps(self, poller, db):
        dps = {DP_CAT_WEIGHT: 4200}
        poller.previous_dps = {DP_CAT_WEIGHT: 4200}  # same value, no change
        poller._handle_changes(dps, _now())
        assert db.query(Visit).count() == 0

    def test_ignores_zero_weight(self, poller, db):
        """A weight of 0 means the scale is idle — should not start a visit."""
        dps = {DP_CAT_WEIGHT: 0}
        poller._handle_changes(dps, _now())
        assert db.query(Visit).count() == 0

    def test_dispatches_cleaning_cycle(self, poller, db):
        dps = {DP_CLEANING_CYCLE: True}
        poller._handle_changes(dps, _now())
        assert db.query(CleaningCycle).count() == 1

    def test_dispatches_setting_change(self, poller, db):
        dps = {"child_lock": True}
        poller._handle_changes(dps, _now())
        assert db.query(SettingsHistory).count() == 1
