import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import tinytuya

from app.cat_identifier import identify_cat, update_reference_weight
from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit

logger = logging.getLogger(__name__)

# --- Device configuration ---
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
if not DEVICE_ID:
    raise ValueError("TUYA_DEVICE_ID environment variable not set")

TUYA_API_KEY = os.getenv("TUYA_API_KEY")
if not TUYA_API_KEY:
    raise ValueError("TUYA_API_KEY environment variable not set")

TUYA_API_SECRET = os.getenv("TUYA_API_SECRET")
if not TUYA_API_SECRET:
    raise ValueError("TUYA_API_SECRET environment variable not set")

TUYA_API_REGION = os.getenv("TUYA_API_REGION", "eu")

SNAPSHOT_INTERVAL_SECONDS = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "300"))

# How long after the last weight reading before we close the visit
VISIT_TIMEOUT_SECONDS = int(os.getenv("VISIT_TIMEOUT_SECONDS", "60"))

SETTINGS_DPS = {"deodorization", "Clean_notice", "child_lock", "induction_delay",
                "induction_interval", "odourless", "capacity_calibration", "sand_surface_calibration"}

DP_CAT_WEIGHT = "cat_weight"
DP_CLEANING_CYCLE = "smart_clean"


def make_cloud() -> tinytuya.Cloud:
    return tinytuya.Cloud(
        apiRegion=TUYA_API_REGION,
        apiKey=TUYA_API_KEY,
        apiSecret=TUYA_API_SECRET,
        apiDeviceID=DEVICE_ID,
    )


class LitterboxPoller:
    """
    Stateful poller that tracks the litterbox's DP changes via Tuya cloud API.
    Visit detection is based on weight readings — a visit starts when a weight
    is received and closes after VISIT_TIMEOUT_SECONDS of no new weight.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.cloud: Optional[tinytuya.Cloud] = None
        self.previous_dps: dict = {}
        self.current_visit: Optional[Visit] = None
        self.last_weight_at: Optional[datetime] = None
        self.current_cleaning_cycle: Optional[CleaningCycle] = None
        self.last_snapshot_at: Optional[datetime] = None
        self._init_cloud()

    def _init_cloud(self):
        try:
            self.cloud = make_cloud()
            logger.info("Cloud connection initialized")
            # Prime previous_dps silently to avoid firing events on startup
            result = self.cloud.getstatus(DEVICE_ID)
            if result and result.get("success"):
                self.previous_dps = {
                    item["code"]: item["value"]
                    for item in result.get("result", [])
                }
                logger.info("Initial device state loaded")
        except Exception as e:
            logger.error(f"Failed to initialize cloud connection: {e}")
            self.cloud = None

    def poll(self):
        """Single poll cycle — call this in a loop."""
        if self.cloud is None:
            logger.warning("Cloud not initialized, retrying...")
            self._init_cloud()
            return

        try:
            result = self.cloud.getstatus(DEVICE_ID)
        except Exception as e:
            logger.exception("Failed to read device status from cloud")
            self._init_cloud()
            return

        if not result or not result.get("success"):
            logger.warning(f"Unexpected cloud response: {result}")
            return

        # Convert list of {code, value} to a dict keyed by code
        dps = {item["code"]: item["value"] for item in result.get("result", [])}

        if not dps:
            logger.warning("Empty DPs in cloud response")
            return

        now = datetime.now(timezone.utc)

        self._check_visit_timeout(now)
        self._handle_changes(dps, now)
        self._maybe_snapshot(dps, now)

        self.previous_dps = dps

    def _check_visit_timeout(self, now: datetime):
        """Close an open visit if we haven't seen a weight update recently."""
        if self.current_visit is None:
            return
        if self.last_weight_at is None:
            return
        elapsed = (now - self.last_weight_at).total_seconds()
        if elapsed >= VISIT_TIMEOUT_SECONDS:
            logger.info(f"Visit timed out after {elapsed:.0f}s of no weight reading — closing")
            self._close_visit(now)

    def _handle_changes(self, dps: dict, now: datetime):
        for dp, value in dps.items():
            if self.previous_dps.get(dp) == value:
                continue

            logger.debug(f"DP {dp} changed: {self.previous_dps.get(dp)} → {value}")

            if dp == DP_CAT_WEIGHT and value != 0:
                self._handle_weight_update(value, now)

            elif dp == DP_CLEANING_CYCLE:
                self._handle_cleaning_cycle(value, now)

            elif dp in SETTINGS_DPS:
                self._record_setting_change(dp, value, now)

    def _handle_weight_update(self, raw_weight: int, now: datetime):
        weight_kg = round(raw_weight / 1000, 3)
        logger.info(f"Weight reading: {weight_kg} kg")

        self.last_weight_at = now

        if self.current_visit is None:
            # New visit — weight reading is our trigger
            logger.info("Visit started (weight-based detection)")
            self.current_visit = Visit(
                started_at=now,
                weight_kg=weight_kg,
            )
            self.db.add(self.current_visit)
            self.db.commit()
        else:
            # Update weight on existing visit (take the latest reading)
            self.current_visit.weight_kg = weight_kg
            self.db.commit()

    def _close_visit(self, now: datetime):
        """Finalise the current visit — identify cat and set end time."""
        if self.current_visit is None:
            return

        self.current_visit.ended_at = now
        self.current_visit.duration_seconds = int(
            (now - self.current_visit.started_at).total_seconds()
        )

        if self.current_visit.weight_kg:
            self._identify_visit_cat(self.current_visit, self.current_visit.weight_kg)

        self.db.commit()
        logger.info(
            f"Visit closed — duration: {self.current_visit.duration_seconds}s, "
            f"weight: {self.current_visit.weight_kg} kg"
        )
        self.current_visit = None
        self.last_weight_at = None

    def _identify_visit_cat(self, visit: Visit, weight_kg: float):
        active_cats = self.db.query(Cat).filter(Cat.active == True).all()
        cat_dicts = [
            {"id": c.id, "name": c.name, "reference_weight_kg": c.reference_weight_kg}
            for c in active_cats
        ]

        match = identify_cat(weight_kg, cat_dicts)
        if match:
            visit.cat_id = match.cat_id
            visit.identified_by = match.identified_by
            logger.info(f"Visit assigned to {match.cat_name} (deviation: {match.deviation_kg:.3f} kg)")

            cat = next(c for c in active_cats if c.id == match.cat_id)
            if cat.reference_weight_kg is not None:
                cat.reference_weight_kg = update_reference_weight(
                    cat.reference_weight_kg, weight_kg
                )
        else:
            logger.info(f"Visit unidentified — weight {weight_kg} kg outside all thresholds")

    def _handle_cleaning_cycle(self, running: bool, now: datetime):
        if running and self.current_cleaning_cycle is None:
            logger.info("Cleaning cycle started")
            self.current_cleaning_cycle = CleaningCycle(started_at=now)
            self.db.add(self.current_cleaning_cycle)
            self.db.commit()

        elif not running and self.current_cleaning_cycle is not None:
            logger.info("Cleaning cycle ended")
            self.current_cleaning_cycle.ended_at = now
            self.db.commit()
            self.current_cleaning_cycle = None

    def _record_setting_change(self, dp: str, value, now: datetime):
        logger.info(f"Setting changed — DP {dp}: {value}")
        entry = SettingsHistory(dp=dp, value=str(value), changed_at=now)
        self.db.add(entry)
        self.db.commit()

    def _maybe_snapshot(self, dps: dict, now: datetime):
        if (
            self.last_snapshot_at is None
            or (now - self.last_snapshot_at).total_seconds() >= SNAPSHOT_INTERVAL_SECONDS
        ):
            snapshot = DeviceSnapshot(recorded_at=now, raw_dps=dps)
            self.db.add(snapshot)
            self.db.commit()
            self.last_snapshot_at = now
            logger.debug("Snapshot saved")