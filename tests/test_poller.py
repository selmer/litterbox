"""Tests for LitterboxPoller business logic.

These tests use an in-memory SQLite database to verify that the poller
correctly creates and updates Visits, CleaningCycles, DeviceSnapshots,
and SettingsHistory records.

The Tuya cloud connection is mocked out — see the `poller` fixture in conftest.py.
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit, VisitDiagnostic


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _report_log(code, value, timestamp):
    return {
        "code": code,
        "value": value,
        "event_time": int(timestamp.timestamp() * 1000),
    }


# ---------------------------------------------------------------------------
# _handle_weight_update
# ---------------------------------------------------------------------------

def test_weight_update_creates_new_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)

    visits = db_session.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].weight_kg == pytest.approx(4.1)
    assert visits[0].started_at == NOW
    diagnostic = db_session.query(VisitDiagnostic).filter_by(visit_id=visits[0].id, event_type="weight_seen").one()
    assert diagnostic.payload["weight_kg"] == pytest.approx(4.1)


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
    assert poller.current_visit.last_weight_at == NOW


def test_weight_update_identifies_clear_cat_immediately(poller, db_session):
    cat = Cat(name="Plurk", reference_weight_kg=3.8, active=True)
    db_session.add(cat)
    db_session.commit()

    poller._handle_weight_update(3830, NOW)

    visit = db_session.query(Visit).first()
    assert visit.cat_id == cat.id
    assert visit.identified_by == "auto"
    diagnostic = db_session.query(VisitDiagnostic).filter_by(
        visit_id=visit.id,
        event_type="identification_attempt",
    ).one()
    assert diagnostic.payload["strategy"] == "reference_weight"
    assert diagnostic.payload["selected_cat_id"] == cat.id
    assert diagnostic.payload["reason"] == "single_reference_match"


def test_weight_update_does_not_update_reference_until_visit_closes(poller, db_session):
    cat = Cat(name="Plurk", reference_weight_kg=3.8, active=True)
    db_session.add(cat)
    db_session.commit()

    poller._handle_weight_update(3830, NOW)
    assert cat.reference_weight_kg == pytest.approx(3.8)

    dps = {"excretion_time_day": 60, "cat_weight": 3830, "excretion_times_day": 1}
    poller._handle_visit_complete(dps, NOW + timedelta(seconds=60))

    assert cat.reference_weight_kg == pytest.approx(3.803)


def test_weight_update_records_unmatched_identification_diagnostic(poller, db_session):
    cat = Cat(name="Plurk", reference_weight_kg=3.8, active=True)
    db_session.add(cat)
    db_session.commit()

    poller._handle_weight_update(5200, NOW)

    visit = db_session.query(Visit).first()
    assert visit.cat_id is None
    diagnostic = db_session.query(VisitDiagnostic).filter_by(
        visit_id=visit.id,
        event_type="identification_attempt",
    ).one()
    assert diagnostic.payload["selected_cat_id"] is None
    assert diagnostic.payload["reason"] == "no_match"
    assert diagnostic.payload["candidates"][0]["cat_name"] == "Plurk"


def test_recent_baseline_fallback_identifies_single_clear_match(poller, db_session):
    plurk = Cat(name="Plurk", reference_weight_kg=None, active=True)
    mochi = Cat(name="Mochi", reference_weight_kg=None, active=True)
    db_session.add_all([plurk, mochi])
    db_session.commit()
    db_session.add_all([
        Visit(cat_id=plurk.id, identified_by="auto", started_at=NOW - timedelta(hours=3), weight_kg=3.78),
        Visit(cat_id=plurk.id, identified_by="auto", started_at=NOW - timedelta(hours=2), weight_kg=3.80),
        Visit(cat_id=mochi.id, identified_by="auto", started_at=NOW - timedelta(hours=3), weight_kg=5.9),
        Visit(cat_id=mochi.id, identified_by="auto", started_at=NOW - timedelta(hours=2), weight_kg=6.0),
    ])
    db_session.commit()

    poller._handle_weight_update(3830, NOW)

    visit = db_session.query(Visit).order_by(Visit.id.desc()).first()
    assert visit.cat_id == plurk.id
    diagnostic = db_session.query(VisitDiagnostic).filter_by(
        visit_id=visit.id,
        event_type="identification_attempt",
    ).one()
    assert diagnostic.payload["strategy"] == "recent_baseline"
    assert diagnostic.payload["selected_cat_id"] == plurk.id


def test_recent_baseline_fallback_rejects_ambiguous_matches(poller, db_session):
    plurk = Cat(name="Plurk", reference_weight_kg=None, active=True)
    luna = Cat(name="Luna", reference_weight_kg=None, active=True)
    db_session.add_all([plurk, luna])
    db_session.commit()
    db_session.add_all([
        Visit(cat_id=plurk.id, identified_by="auto", started_at=NOW - timedelta(hours=4), weight_kg=3.78),
        Visit(cat_id=plurk.id, identified_by="auto", started_at=NOW - timedelta(hours=3), weight_kg=3.80),
        Visit(cat_id=luna.id, identified_by="auto", started_at=NOW - timedelta(hours=4), weight_kg=3.90),
        Visit(cat_id=luna.id, identified_by="auto", started_at=NOW - timedelta(hours=3), weight_kg=3.95),
    ])
    db_session.commit()

    poller._handle_weight_update(3830, NOW)

    visit = db_session.query(Visit).order_by(Visit.id.desc()).first()
    assert visit.cat_id is None
    diagnostic = db_session.query(VisitDiagnostic).filter_by(
        visit_id=visit.id,
        event_type="identification_attempt",
    ).one()
    assert diagnostic.payload["strategy"] == "recent_baseline"
    assert diagnostic.payload["reason"] == "ambiguous_recent_baseline_matches"


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
    assert visit.duration_source == "status_dp"
    assert visit.duration_is_estimated is False
    diagnostic = db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="completion_matched").one()
    assert diagnostic.payload["strategy"] == "status_dp"
    assert poller.current_visit is None
    assert poller.last_weight_at is None


def test_visit_complete_without_prior_visit_creates_one(poller, db_session):
    """If a completion event arrives without a preceding weight event, a visit is created."""
    dps = {"excretion_time_day": 30, "cat_weight": 4100, "excretion_times_day": 1}

    poller._handle_visit_complete(dps, NOW)

    visits = db_session.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].duration_seconds == 30
    assert visits[0].duration_source == "status_dp"


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

def test_visit_timeout_keeps_overdue_visit_open_when_reconciliation_is_pending(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    poller.cloud.cloudrequest.return_value = {"success": True, "result": {"logs": []}}
    far_future = NOW + timedelta(seconds=400)  # > VISIT_TIMEOUT_SECONDS (300)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at is None
    assert visit.duration_seconds is None
    assert db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="pending_retry").count() == 1
    assert poller.current_visit is not None


def test_visit_timeout_uses_report_log_completion_when_status_poll_missed_it(poller, db_session):
    poller.previous_dps = {"excretion_times_day": 3}
    poller._handle_weight_update(4100, NOW)
    completed_at = NOW + timedelta(seconds=75)
    poller.cloud.cloudrequest.return_value = {
        "success": True,
        "result": {
            "logs": [
                _report_log("cat_weight", 4100, NOW + timedelta(seconds=5)),
                _report_log("excretion_time_day", 75, completed_at),
                _report_log("excretion_times_day", 4, completed_at),
            ],
        },
    }

    poller._check_visit_timeout(NOW + timedelta(seconds=400))

    visit = db_session.query(Visit).first()
    assert visit.ended_at == completed_at
    assert visit.duration_seconds == 75
    assert visit.weight_kg == pytest.approx(4.1)
    assert visit.duration_source == "report_log_counter"
    assert visit.duration_is_estimated is False
    diagnostic = db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="completion_matched").one()
    assert diagnostic.payload["strategy"] == "counter"
    assert poller.current_visit is None
    poller.cloud.cloudrequest.assert_called_once()


def test_visit_timeout_uses_duration_only_report_log_completion(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    completed_at = NOW + timedelta(seconds=75)
    poller.cloud.cloudrequest.return_value = {
        "success": True,
        "result": {
            "logs": [
                _report_log("cat_weight", 4100, NOW + timedelta(seconds=5)),
                _report_log("excretion_time_day", 75, completed_at),
            ],
        },
    }

    poller._check_visit_timeout(NOW + timedelta(seconds=400))

    visit = db_session.query(Visit).first()
    assert visit.ended_at == completed_at
    assert visit.duration_seconds == 75
    assert visit.weight_kg == pytest.approx(4.1)
    assert visit.duration_source == "report_log_duration"
    assert visit.duration_is_estimated is False
    assert poller.current_visit is None


def test_visit_timeout_retries_when_report_log_lookup_fails_before_hard_timeout(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    poller.cloud.cloudrequest.return_value = {"success": False, "msg": "permission denied"}
    far_future = NOW + timedelta(seconds=400)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at is None
    assert visit.duration_seconds is None
    assert db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="pending_retry").count() == 1
    assert poller.current_visit is not None


def test_visit_hard_timeout_falls_back_when_report_logs_never_reconcile(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    poller.cloud.cloudrequest.return_value = {"success": False, "msg": "permission denied"}
    far_future = NOW + timedelta(seconds=1800)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at == far_future
    assert visit.duration_seconds is None
    assert visit.duration_source == "hard_timeout"
    assert visit.duration_is_estimated is True
    diagnostic = db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="hard_timeout").one()
    assert diagnostic.payload["elapsed_seconds"] == 1800
    assert poller.current_visit is None


def test_visit_timeout_uses_duration_log_when_counter_does_not_increase(poller, db_session):
    poller.previous_dps = {"excretion_times_day": 7}
    poller._handle_weight_update(4100, NOW)
    completed_at = NOW + timedelta(seconds=80)
    poller.cloud.cloudrequest.return_value = {
        "success": True,
        "result": {
            "logs": [
                _report_log("excretion_time_day", 80, completed_at),
                _report_log("excretion_times_day", 7, completed_at),
            ],
        },
    }
    far_future = NOW + timedelta(seconds=400)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at == completed_at
    assert visit.duration_seconds == 80
    assert visit.duration_source == "report_log_duration"
    assert poller.current_visit is None


def test_visit_timeout_ignores_invalid_duration_logs_and_keeps_visit_open(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    poller.cloud.cloudrequest.return_value = {
        "success": True,
        "result": {
            "logs": [
                _report_log("excretion_time_day", 0, NOW + timedelta(seconds=80)),
                _report_log("excretion_time_day", -1, NOW + timedelta(seconds=90)),
                _report_log("excretion_time_day", 70, NOW - timedelta(seconds=10)),
            ],
        },
    }
    far_future = NOW + timedelta(seconds=400)

    poller._check_visit_timeout(far_future)

    visit = db_session.query(Visit).first()
    assert visit.ended_at is None
    assert visit.duration_seconds is None
    assert db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="pending_retry").count() == 1
    assert poller.current_visit is not None


def test_visit_timeout_does_not_close_recent_visit(poller, db_session):
    poller._handle_weight_update(4100, NOW)
    soon_after = NOW + timedelta(seconds=100)  # < VISIT_TIMEOUT_SECONDS

    poller._check_visit_timeout(soon_after)

    assert poller.current_visit is not None


def test_visit_timeout_does_nothing_without_visit(poller):
    # Should not raise
    poller._check_visit_timeout(NOW)
    assert poller.current_visit is None


def test_poller_recovers_open_visit_and_cleaning_cycle(db_session):
    open_visit = Visit(started_at=NOW, weight_kg=4.1, last_weight_at=NOW + timedelta(seconds=5))
    open_cycle = CleaningCycle(started_at=NOW)
    db_session.add_all([open_visit, open_cycle])
    db_session.commit()
    open_visit_id = open_visit.id
    open_cycle_id = open_cycle.id
    open_visit_last_weight_at = open_visit.last_weight_at

    mock_cloud = MagicMock()
    mock_cloud.getstatus.return_value = {"success": True, "result": []}
    with patch("app.poller.make_cloud", return_value=mock_cloud):
        from app.poller import LitterboxPoller
        recovered = LitterboxPoller(lambda: db_session)

    assert recovered.current_visit_id == open_visit_id
    assert recovered.current_cleaning_cycle_id == open_cycle_id
    assert recovered.last_weight_at == open_visit_last_weight_at


def test_recovered_open_visit_retries_report_log_reconciliation(db_session):
    open_visit = Visit(started_at=NOW, weight_kg=4.1, last_weight_at=NOW)
    db_session.add(open_visit)
    db_session.commit()
    open_visit_id = open_visit.id
    completed_at = NOW + timedelta(seconds=70)

    mock_cloud = MagicMock()
    mock_cloud.getstatus.return_value = {"success": True, "result": []}
    mock_cloud.cloudrequest.return_value = {
        "success": True,
        "result": {
            "logs": [
                _report_log("excretion_time_day", 70, completed_at),
            ],
        },
    }
    with patch("app.poller.make_cloud", return_value=mock_cloud):
        from app.poller import LitterboxPoller
        recovered = LitterboxPoller(lambda: db_session)

    recovered.db = db_session
    recovered.current_visit = db_session.get(Visit, open_visit_id)
    recovered._check_visit_timeout(NOW + timedelta(seconds=400))

    visit = db_session.get(Visit, open_visit_id)
    assert visit.ended_at == completed_at
    assert visit.duration_seconds == 70
    assert visit.duration_source == "report_log_duration"
    assert recovered.current_visit is None


def test_poll_returns_failed_outcome_for_empty_dps(poller):
    poller.cloud.getstatus.return_value = {"success": True, "result": []}

    outcome = poller.poll()

    assert outcome.success is False
    assert outcome.status == "empty_dps"


def test_poll_returns_success_outcome_for_valid_dps(poller):
    poller.cloud.getstatus.return_value = {
        "success": True,
        "result": [{"code": "cat_weight", "value": 0}],
    }

    outcome = poller.poll()

    assert outcome.success is True




def test_status_completion_without_duration_keeps_visit_open(poller, db_session):
    poller._handle_weight_update(4100, NOW)

    poller._handle_visit_complete({"excretion_times_day": 1, "cat_weight": 4100}, NOW + timedelta(seconds=60))

    visit = db_session.query(Visit).first()
    assert visit.ended_at is None
    assert visit.duration_seconds is None
    assert poller.current_visit is not None
    diagnostic = db_session.query(VisitDiagnostic).filter_by(visit_id=visit.id, event_type="pending_retry").one()
    assert diagnostic.payload["reason"] == "status_completion_without_duration"


def test_adaptive_polling_uses_short_delay_for_open_visit(monkeypatch, poller):
    import app.poller as poller_module

    monkeypatch.setattr(poller_module, "ADAPTIVE_VISIT_POLLING", True)
    monkeypatch.setattr(poller_module, "ADAPTIVE_POLL_INTERVAL_SECONDS", 30)
    monkeypatch.setattr(poller_module, "ADAPTIVE_POLL_MAX_SECONDS", 100000000)

    poller._handle_weight_update(4100, NOW)
    poller.current_visit_id = poller.current_visit.id

    assert poller.next_poll_delay_seconds(300) == 30


def test_adaptive_polling_respects_daily_budget(monkeypatch, poller, db_session):
    import app.poller as poller_module

    monkeypatch.setattr(poller_module, "ADAPTIVE_VISIT_POLLING", True)
    monkeypatch.setattr(poller_module, "ADAPTIVE_POLL_DAILY_BUDGET", 1)
    monkeypatch.setattr(poller_module, "ADAPTIVE_POLL_MAX_SECONDS", 100000000)

    poller._handle_weight_update(4100, NOW)
    poller.current_visit_id = poller.current_visit.id
    poller.adaptive_daily_count = 1

    assert poller.next_poll_delay_seconds(300) == 300


def test_adaptive_poll_captures_status_duration(monkeypatch, poller, db_session):
    import app.poller as poller_module

    monkeypatch.setattr(poller_module, "ADAPTIVE_VISIT_POLLING", True)
    monkeypatch.setattr(poller_module, "ADAPTIVE_POLL_MAX_SECONDS", 100000000)
    poller.previous_dps = {"cat_weight": 4100, "excretion_time_day": 0, "excretion_times_day": 1}
    poller._handle_weight_update(4100, NOW)
    visit_id = poller.current_visit.id
    poller.current_visit_id = visit_id
    poller.db = None
    poller.cloud.getstatus.return_value = {
        "success": True,
        "result": [
            {"code": "cat_weight", "value": 4100},
            {"code": "excretion_time_day", "value": 75},
            {"code": "excretion_times_day", "value": 1},
        ],
    }

    outcome = poller.poll()

    visit = db_session.get(Visit, visit_id)
    assert outcome.success is True
    assert visit.ended_at is not None
    assert visit.duration_seconds == 75
    assert visit.duration_source == "status_dp"
    assert poller.current_visit is None
    event_types = [row[0] for row in db_session.query(VisitDiagnostic.event_type).filter_by(visit_id=visit_id).all()]
    assert "adaptive_poll_started" in event_types
    assert "adaptive_poll_attempt" in event_types
    assert "adaptive_poll_stopped" in event_types


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

def test_identify_visit_cat_with_none_weight_does_not_raise(poller, db_session):
    """_identify_visit_cat should skip identification gracefully when weight is None."""
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db_session.add(cat)
    db_session.commit()

    visit = Visit(started_at=NOW, weight_kg=None)
    db_session.add(visit)
    db_session.commit()

    poller._identify_visit_cat(visit, None)

    assert visit.cat_id is None
    assert visit.identified_by is None


def test_identify_visit_cat_updates_reference_weight(poller, db_session):
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db_session.add(cat)
    db_session.commit()

    visit = Visit(started_at=NOW, weight_kg=4.2)
    db_session.add(visit)
    db_session.commit()

    poller._identify_visit_cat(visit, 4.2)

    # Reference weight is updated in-memory (callers commit); check without refresh
    # to verify the in-session state before the caller would commit.
    assert cat.reference_weight_kg != pytest.approx(4.0)
    assert 4.0 < cat.reference_weight_kg < 4.2
