import logging
import os
from datetime import datetime, timezone
from typing import Optional

import tinytuya

from app.cat_identifier import identify_cat, update_reference_weight
from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit

logger = logging.getLogger(__name__)

# --- Device configuration (override via environment variables) ---
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
if not DEVICE_ID:
    raise ValueError("DEVICE_IP environment variable not set")

DEVICE_IP = os.getenv("TUYA_DEVICE_IP")
if not DEVICE_IP:
    raise ValueError("DEVICE_IP environment variable not set")

DEVICE_VERSION = float(os.getenv("TUYA_DEVICE_VERSION", "3.4"))
if not DEVICE_IP:
    raise ValueError("DEVICE_IP environment variable not set")

# Tuya cloud credentials for key refresh
TUYA_API_KEY = os.getenv("TUYA_API_KEY", "sukk7w34kvkkukheppa8")
if not TUYA_API_KEY:
    raise ValueError("TUYA_API_KEY environment variable not set")

TUYA_API_SECRET = os.getenv("TUYA_API_SECRET")
if not TUYA_API_SECRET:
    raise ValueError("TUYA_API_SECRET environment variable not set")
TUYA_API_REGION = os.getenv("TUYA_API_REGION", "eu")

# How often to take a full snapshot of all DPs (in seconds)
SNAPSHOT_INTERVAL_SECONDS = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "300"))

# DPs that represent device settings (changes get logged to settings_history)
SETTINGS_DPS = {"17", "111", "114", "117", "118", "120", "124", "125"}

# DP codes
DP_CAT_WEIGHT = "6"
DP_OBJECT_IN_BOX = "104"
DP_CLEANING_CYCLE = "121"


def fetch_device_key() -> Optional[str]:
    """Fetch the current local key from Tuya cloud."""
    try:
        logger.info("Fetching device key from Tuya cloud...")
        cloud = tinytuya.Cloud(
            apiRegion=TUYA_API_REGION,
            apiKey=TUYA_API_KEY,
            apiSecret=TUYA_API_SECRET,
        )
        devices = cloud.getdevices()
        for device in devices:
            if device.get("id") == DEVICE_ID:
                key = device.get("key")
                logger.info("Device key fetched successfully")
                return key
        logger.warning("Device not found in cloud response")
    except Exception as e:
        logger.exception("Failed to fetch device key")
    return None


def make_device(key: str) -> tinytuya.OutletDevice:
    d = tinytuya.OutletDevice(
        dev_id=DEVICE_ID,
        address=DEVICE_IP,
        local_key=key,
        version=DEVICE_VERSION,
    )
    return d


class LitterboxPoller:
    """
    Stateful poller that tracks the litterbox's DP changes and writes
    visits, cleaning cycles, snapshots, and settings changes to the DB.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.device: Optional[tinytuya.OutletDevice] = None
        self.device_key: Optional[str] = None
        self.previous_dps: dict = {}
        self.current_visit: Optional[Visit] = None
        self.current_cleaning_cycle: Optional[CleaningCycle] = None
        self.last_snapshot_at: Optional[datetime] = None
        self._init_device()

    def _init_device(self):
        """Fetch key from cloud and initialize the device connection."""
        key = fetch_device_key()
        if key:
            self.device_key = key
            self.device = make_device(key)
        else:
            logger.error("Could not initialize device — no key available")

    def _refresh_device(self):
        """Re-fetch key and reinitialize device — called on 914 errors."""
        logger.info("Refreshing device key due to 914 error...")
        self._init_device()

    def poll(self):
        """Single poll cycle — call this in a loop."""
        if self.device is None:
            logger.warning("Device not initialized, retrying...")
            self._init_device()
            return

        try:
            data = self.device.status()
        except Exception as e:
            logger.exception("Failed to read device status")
            return

        if not data or "dps" not in data:
            err = data.get("Err") if data else None
            if err == "914":
                self._refresh_device()
            else:
                logger.warning(f"Unexpected device response: {data}")
            return

        dps = data["dps"]
        now = datetime.now(timezone.utc)

        self._handle_changes(dps, now)
        self._maybe_snapshot(dps, now)

        self.previous_dps = dps

    def _handle_changes(self, dps: dict, now: datetime):
        for dp, value in dps.items():
            if self.previous_dps.get(dp) == value:
                continue

            logger.debug(f"DP {dp} changed: {self.previous_dps.get(dp)} → {value}")

            if dp == DP_OBJECT_IN_BOX:
                self._handle_object_in_box(value, now)

            elif dp == DP_CLEANING_CYCLE:
                self._handle_cleaning_cycle(value, now)

            elif dp == DP_CAT_WEIGHT and not value == 0:
                self._handle_weight_update(value)

            elif dp in SETTINGS_DPS:
                self._record_setting_change(dp, value, now)

    def _handle_object_in_box(self, present: bool, now: datetime):
        if present and self.current_visit is None:
            logger.info("Visit started")
            self.current_visit = Visit(started_at=now)
            self.db.add(self.current_visit)
            self.db.commit()

        elif not present and self.current_visit is not None:
            logger.info("Visit ended")
            self.current_visit.ended_at = now
            self.current_visit.duration_seconds = int(
                (now - self.current_visit.started_at).total_seconds()
            )
            self.db.commit()

    def _handle_weight_update(self, raw_weight: int):
        weight_kg = round(raw_weight / 1000, 3)
        logger.info(f"Weight reading: {weight_kg} kg")

        if self.current_visit is None:
            logger.warning("Weight update received but no active visit — ignoring")
            return

        self.current_visit.weight_kg = weight_kg
        self._identify_visit_cat(self.current_visit, weight_kg)
        self.db.commit()

        self.current_visit = None  # visit fully recorded

    def _identify_visit_cat(self, visit: Visit, weight_kg: float):
        active_cats = (
            self.db.query(Cat)
            .filter(Cat.active == True)
            .all()
        )
        cat_dicts = [
            {"id": c.id, "name": c.name, "reference_weight_kg": c.reference_weight_kg}
            for c in active_cats
        ]

        match = identify_cat(weight_kg, cat_dicts)
        if match:
            visit.cat_id = match.cat_id
            visit.identified_by = match.identified_by
            logger.info(f"Visit assigned to {match.cat_name} (deviation: {match.deviation_kg} kg)")

            # Gradually update reference weight
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