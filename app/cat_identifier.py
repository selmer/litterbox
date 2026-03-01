from dataclasses import dataclass
from typing import Optional


# Maximum deviation from a cat's reference weight to still consider it a match.
# A cat typically weighs less during a visit than their true weight due to
# them not having eaten/drunk recently, so we use a generous threshold.
IDENTIFICATION_THRESHOLD_KG = 0.5


@dataclass
class CatMatch:
    cat_id: int
    cat_name: str
    reference_weight_kg: float
    deviation_kg: float
    identified_by: str = "auto"


def identify_cat(
    weight_kg: float,
    cats: list[dict],
    threshold_kg: float = IDENTIFICATION_THRESHOLD_KG,
) -> Optional[CatMatch]:
    """
    Given a weight reading and a list of active cats, returns the best matching
    cat or None if no cat is within the threshold.

    Each cat dict should have: id, name, reference_weight_kg

    Returns None if:
    - No active cats have a reference weight set
    - The closest match is further than threshold_kg away
    - The weight is 0 or negative (sensor error)
    """
    if weight_kg <= 0:
        return None

    eligible = [c for c in cats if c.get("reference_weight_kg") is not None]
    if not eligible:
        return None

    closest = min(eligible, key=lambda c: abs(c["reference_weight_kg"] - weight_kg))
    deviation = abs(closest["reference_weight_kg"] - weight_kg)

    if deviation > threshold_kg:
        return None

    return CatMatch(
        cat_id=closest["id"],
        cat_name=closest["name"],
        reference_weight_kg=closest["reference_weight_kg"],
        deviation_kg=deviation,
    )


def update_reference_weight(
    current_reference: float,
    new_weight: float,
    smoothing: float = 0.1,
) -> float:
    """
    Gradually update a cat's reference weight using exponential moving average.
    A smoothing factor of 0.1 means new readings only nudge the reference
    weight slightly, preventing a single outlier from skewing the average.

    smoothing=0.1 → slow drift, stable reference
    smoothing=0.5 → faster adaptation to weight changes
    """
    return round(current_reference * (1 - smoothing) + new_weight * smoothing, 3)
