"""
Tests for LitterboxPoller state machine.

Assumptions confirmed by device owner:
- cat_weight DP: integer grams (e.g. 4200 → 4.2 kg)
- excretion_time_day DP: integer seconds
- smart_clean DP: True = cycle started, False = cycle ended
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models import Base, Cat, CleaningCycle, Visit
from app.poller import LitterboxPoller


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_poller(db, initial_dps=None):
    """Construct a LitterboxPoller with a mocked cloud connection."""
    cloud = MagicMock()
    cloud.getstatus.return_value = {
        "success": True,
        "result": [{"code": k, "value": v} for k, v in (initial_dps or {}).items()],
    }

    with patch("app.poller.make_cloud", return_value=cloud):
        poller = LitterboxPoller(db)

    poller.cloud = cloud
    return poller, cloud


def _dps_response(dps: dict):
    return {
        "success": True,
        "result": [{"code": k, "value": v} for k, v in dps.items()],
    }


def _poll_with(poller, cloud, dps: dict):
    cloud.getstatus.return_value = _dps_response(dps)
    poller.poll()


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture()
def cat_luna(db):
    cat = Cat(name="Luna", reference_weight_kg=4.0, active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture()
def cat_mochi(db):
    cat = Cat(name="Mochi", reference_weight_kg=6.0, active=True)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ---------------------------------------------------------------------------
# Weight events → visit lifecycle
# ---------------------------------------------------------------------------

def test_weight_event_opens_visit(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4200})

    visits = db.query(Visit).all()
    assert len(visits) == 1
    assert visits[0].weight_kg == pytest.approx(4.2)
    assert visits[0].ended_at is None


def test_excretion_event_closes_visit(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4200})
    _poll_with(poller, cloud, {"cat_weight": 4200, "excretion_times_day": 1, "excretion_time_day": 90})

    visits = db.query(Visit).all()
    assert len(visits) == 1
    visit = visits[0]
    assert visit.ended_at is not None
    assert visit.duration_seconds == 90


def test_weight_zero_does_not_open_visit(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 0})
    assert db.query(Visit).count() == 0


def test_latest_weight_reading_wins(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4100})
    _poll_with(poller, cloud, {"cat_weight": 4300})

    visit = db.query(Visit).first()
    assert visit.weight_kg == pytest.approx(4.3)


# ---------------------------------------------------------------------------
# Cat identification
# ---------------------------------------------------------------------------

def test_visit_identified_by_weight(db, cat_luna):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4050})
    _poll_with(poller, cloud, {"cat_weight": 4050, "excretion_times_day": 1, "excretion_time_day": 60})

    visit = db.query(Visit).first()
    assert visit.cat_id == cat_luna.id
    assert visit.identified_by == "auto"


def test_unidentified_visit_when_no_cats(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4000})
    _poll_with(poller, cloud, {"cat_weight": 4000, "excretion_times_day": 1, "excretion_time_day": 60})

    visit = db.query(Visit).first()
    assert visit.cat_id is None


def test_unidentified_visit_when_weight_outside_threshold(db, cat_luna):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 2000})  # 2.0 kg — 2 kg from Luna
    _poll_with(poller, cloud, {"cat_weight": 2000, "excretion_times_day": 1, "excretion_time_day": 60})

    visit = db.query(Visit).first()
    assert visit.cat_id is None


# ---------------------------------------------------------------------------
# Visit timeout fallback
# ---------------------------------------------------------------------------

def test_visit_times_out_after_threshold(db):
    from app.poller import VISIT_TIMEOUT_SECONDS

    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"cat_weight": 4200})

    # Wind the clock past the timeout
    poller.last_weight_at -= timedelta(seconds=VISIT_TIMEOUT_SECONDS + 1)
    _poll_with(poller, cloud, {"cat_weight": 4200})

    visit = db.query(Visit).first()
    assert visit.ended_at is not None
    assert poller.current_visit is None


# ---------------------------------------------------------------------------
# Cleaning cycles
# ---------------------------------------------------------------------------

def test_cleaning_cycle_starts_on_true(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"smart_clean": True})

    cycles = db.query(CleaningCycle).all()
    assert len(cycles) == 1
    assert cycles[0].ended_at is None


def test_cleaning_cycle_ends_on_false(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"smart_clean": True})
    _poll_with(poller, cloud, {"smart_clean": False})

    cycle = db.query(CleaningCycle).first()
    assert cycle.ended_at is not None


def test_duplicate_true_does_not_create_extra_cycles(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {"smart_clean": True})
    _poll_with(poller, cloud, {"smart_clean": True})

    assert db.query(CleaningCycle).count() == 1


# ---------------------------------------------------------------------------
# Excretion event with no prior weight event (missed weight)
# ---------------------------------------------------------------------------

def test_missed_weight_visit_created_from_excretion_event(db):
    poller, cloud = _make_poller(db)
    _poll_with(poller, cloud, {
        "excretion_times_day": 1,
        "excretion_time_day": 120,
        "cat_weight": 4200,
    })

    visit = db.query(Visit).first()
    assert visit is not None
    assert visit.ended_at is not None
    assert visit.duration_seconds == 120
