import pytest
from app.cat_identifier import identify_cat, update_reference_weight, IDENTIFICATION_THRESHOLD_KG

# --- Test fixtures ---

CAT_LUNA = {"id": 1, "name": "Luna", "reference_weight_kg": 4.0}
CAT_MOCHI = {"id": 2, "name": "Mochi", "reference_weight_kg": 6.0}
TWO_CATS = [CAT_LUNA, CAT_MOCHI]


# --- identify_cat tests ---

def test_identifies_closest_cat():
    match = identify_cat(4.1, TWO_CATS)
    assert match.cat_id == 1
    assert match.cat_name == "Luna"


def test_identifies_heavier_cat():
    match = identify_cat(5.9, TWO_CATS)
    assert match.cat_id == 2
    assert match.cat_name == "Mochi"


def test_returns_none_when_outside_threshold():
    # 3.0kg is 1.0kg away from Luna (4.0) — outside default 0.5kg threshold
    match = identify_cat(3.0, TWO_CATS)
    assert match is None


def test_returns_none_for_zero_weight():
    match = identify_cat(0.0, TWO_CATS)
    assert match is None


def test_returns_none_for_negative_weight():
    match = identify_cat(-1.0, TWO_CATS)
    assert match is None


def test_returns_none_when_no_cats():
    match = identify_cat(4.0, [])
    assert match is None


def test_returns_none_when_no_reference_weights():
    cats = [{"id": 1, "name": "Luna", "reference_weight_kg": None}]
    match = identify_cat(4.0, cats)
    assert match is None


def test_deviation_is_calculated_correctly():
    match = identify_cat(4.2, TWO_CATS)
    assert match is not None
    assert abs(match.deviation_kg - 0.2) < 0.001


def test_identified_by_is_auto():
    match = identify_cat(4.0, TWO_CATS)
    assert match.identified_by == "auto"


def test_exactly_at_threshold_is_accepted():
    match = identify_cat(4.0 + IDENTIFICATION_THRESHOLD_KG, TWO_CATS)
    assert match is not None
    assert match.cat_id == 1


def test_just_over_threshold_is_rejected():
    match = identify_cat(4.0 + IDENTIFICATION_THRESHOLD_KG + 0.001, TWO_CATS)
    assert match is None


def test_single_cat_identified_within_threshold():
    match = identify_cat(4.3, [CAT_LUNA])
    assert match.cat_id == 1


# --- update_reference_weight tests ---

def test_reference_weight_nudges_toward_new_reading():
    updated = update_reference_weight(4.0, 4.5, smoothing=0.1)
    assert updated == pytest.approx(4.05, abs=0.001)


def test_reference_weight_does_not_jump_drastically():
    updated = update_reference_weight(4.0, 10.0, smoothing=0.1)
    # Should move slightly toward 10.0 but not all the way
    assert 4.0 < updated < 4.7


def test_reference_weight_with_high_smoothing():
    updated = update_reference_weight(4.0, 5.0, smoothing=0.5)
    assert updated == pytest.approx(4.5, abs=0.001)


def test_reference_weight_stable_when_no_change():
    updated = update_reference_weight(4.0, 4.0, smoothing=0.1)
    assert updated == pytest.approx(4.0, abs=0.001)