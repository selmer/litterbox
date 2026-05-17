import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

import tinytuya

from app.cat_identifier import identify_cat, update_reference_weight
from app.models import Cat, CleaningCycle, DeviceSnapshot, SettingsHistory, Visit, VisitDiagnostic

logger = logging.getLogger(__name__)

# --- Device configuration ---
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")
TUYA_API_KEY = os.getenv("TUYA_API_KEY")
TUYA_API_SECRET = os.getenv("TUYA_API_SECRET")
TUYA_API_REGION = os.getenv("TUYA_API_REGION", "eu")

SNAPSHOT_INTERVAL_SECONDS = int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "300"))



SETTINGS_DPS = {"deodorization", "Clean_notice", "child_lock", "induction_delay",
                "induction_interval", "odourless", "capacity_calibration", "sand_surface_calibration"}

VISIT_TIMEOUT_SECONDS = 300  # Start report-log reconciliation after 5 minutes
VISIT_HARD_TIMEOUT_SECONDS = int(os.getenv("VISIT_HARD_TIMEOUT_SECONDS", "1800"))
DP_CAT_WEIGHT = "cat_weight"
DP_CLEANING_CYCLE = "smart_clean"
DP_EXCRETION_TIMES = "excretion_times_day"
DP_EXCRETION_TIME = "excretion_time_day"
REPORT_LOG_LOOKBACK_BUFFER_SECONDS = 30
REPORT_LOG_LOOKAHEAD_BUFFER_SECONDS = 60
REPORT_LOG_CODES = ",".join([DP_EXCRETION_TIMES, DP_EXCRETION_TIME, DP_CAT_WEIGHT])


@dataclass(frozen=True)
class PollOutcome:
    success: bool
    status: str
    message: Optional[str] = None


@dataclass(frozen=True)
class ReportLogCompletion:
    duration_seconds: int
    completed_at: datetime
    weight_kg: Optional[float] = None
    strategy: str = "counter"


def make_cloud() -> tinytuya.Cloud:
    if not TUYA_API_KEY or not TUYA_API_SECRET:
        raise RuntimeError("Tuya API credentials not configured (polling mode requires TUYA_API_KEY and TUYA_API_SECRET)")
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
    is received.

    A fresh DB session is created and closed on every call to poll() to avoid
    stale identity-map state and dropped-connection issues with a long-lived
    session.
    """

    def __init__(self, session_factory, mode: str = "polling"):
        self.mode = mode
        self._lock = threading.Lock()
        self.session_factory = session_factory
        self.db = None
        self.cloud: Optional[tinytuya.Cloud] = None
        self.previous_dps: dict = {}
        self.current_visit: Optional[Visit] = None
        self.current_visit_id: Optional[int] = None
        self.current_cleaning_cycle: Optional[CleaningCycle] = None
        self.current_cleaning_cycle_id: Optional[int] = None
        self.current_visit_excretion_times_at_start: Optional[int] = None
        self.last_snapshot_at: Optional[datetime] = None
        self.last_weight_at = None
        if mode == "polling":
            self._init_cloud()
        self._recover_open_state()

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

    def _recover_open_state(self):
        db = self.session_factory()
        try:
            open_visit = (
                db.query(Visit)
                .filter(Visit.ended_at.is_(None))
                .order_by(Visit.started_at.desc(), Visit.id.desc())
                .first()
            )
            if open_visit:
                self.current_visit_id = open_visit.id
                self.last_weight_at = open_visit.last_weight_at or open_visit.started_at
                self.current_visit_excretion_times_at_start = None
                logger.info("Recovered open visit %s", open_visit.id)

            open_cycle = (
                db.query(CleaningCycle)
                .filter(CleaningCycle.ended_at.is_(None))
                .order_by(CleaningCycle.started_at.desc(), CleaningCycle.id.desc())
                .first()
            )
            if open_cycle:
                self.current_cleaning_cycle_id = open_cycle.id
                logger.info("Recovered open cleaning cycle %s", open_cycle.id)

            latest_snapshot = (
                db.query(DeviceSnapshot)
                .order_by(DeviceSnapshot.recorded_at.desc(), DeviceSnapshot.id.desc())
                .first()
            )
            if latest_snapshot:
                self.last_snapshot_at = latest_snapshot.recorded_at
        finally:
            db.close()

    def poll(self) -> PollOutcome:
        """Single poll cycle — call this in a loop.

        Opens a fresh DB session for the duration of this poll and closes it
        before returning, ensuring no session state leaks between cycles.
        """
        if self.cloud is None:
            logger.warning("Cloud not initialized, retrying...")
            self._init_cloud()
            return PollOutcome(False, "cloud_unavailable", "Cloud connection is not initialized")

        try:
            result = self.cloud.getstatus(DEVICE_ID)
        except Exception as e:
            logger.exception("Failed to read device status from cloud")
            self._init_cloud()
            return PollOutcome(False, "cloud_error", str(e))

        if not result or not result.get("success"):
            logger.warning(f"Unexpected cloud response: {result}")
            return PollOutcome(False, "cloud_response_error", "Unexpected cloud response")

        # Convert list of {code, value} to a dict keyed by code
        dps = {item["code"]: item["value"] for item in result.get("result", [])}

        if not dps:
            logger.warning("Empty DPs in cloud response")
            return PollOutcome(False, "empty_dps", "Cloud response did not include device state")

        db = self.session_factory()
        try:
            self.db = db
            # Rehydrate any in-progress objects into the new session via their IDs
            self.current_visit = db.get(Visit, self.current_visit_id) if self.current_visit_id else None
            self.current_cleaning_cycle = db.get(CleaningCycle, self.current_cleaning_cycle_id) if self.current_cleaning_cycle_id else None

            now = datetime.now(timezone.utc)
            self._handle_changes(dps, now)
            self._check_visit_timeout(now)
            self._maybe_snapshot(dps, now)

            self.previous_dps = dps

            # Persist IDs so the next poll can reload these objects
            self.current_visit_id = self.current_visit.id if self.current_visit else None
            self.current_cleaning_cycle_id = self.current_cleaning_cycle.id if self.current_cleaning_cycle else None
            return PollOutcome(True, "success")
        finally:
            self.db = None
            db.close()

    def process_webhook_dps(self, changed_dps: dict):
        """Process a partial DPS update received from a Tuya webhook.

        Merges changed DPs into the accumulated previous_dps, reconstructs
        the full current state, then delegates to _handle_changes — reusing
        all visit/cleaning cycle logic unchanged.
        """
        with self._lock:
            current_dps = {**self.previous_dps, **changed_dps}

            db = self.session_factory()
            try:
                self.db = db
                self.current_visit = db.get(Visit, self.current_visit_id) if self.current_visit_id else None
                self.current_cleaning_cycle = db.get(CleaningCycle, self.current_cleaning_cycle_id) if self.current_cleaning_cycle_id else None

                now = datetime.now(timezone.utc)
                self._handle_changes(current_dps, now)
                self._check_visit_timeout(now)

                self.previous_dps = current_dps
                self.current_visit_id = self.current_visit.id if self.current_visit else None
                self.current_cleaning_cycle_id = self.current_cleaning_cycle.id if self.current_cleaning_cycle else None
            finally:
                self.db = None
                db.close()

    def _handle_changes(self, dps: dict, now: datetime):
        for dp, value in dps.items():
            if self.previous_dps.get(dp) == value:
                continue

            logger.debug(f"DP {dp} changed: {self.previous_dps.get(dp)} → {value}")

            if dp == DP_CAT_WEIGHT and value != 0:
                self._handle_weight_update(value, now)

            elif dp == DP_EXCRETION_TIMES:
                self._handle_visit_complete(dps, now)

            elif dp == DP_CLEANING_CYCLE:
                self._handle_cleaning_cycle(value, now)

            elif dp in SETTINGS_DPS:
                self._record_setting_change(dp, value, now)

    def _handle_visit_complete(self, dps: dict, now: datetime):
        duration = dps.get(DP_EXCRETION_TIME)
        logger.info(f"Visit completed from status DPs — duration: {duration}s")

        if self.current_visit is None:
            # Visit completed but we missed the weight — create one now
            weight_raw = dps.get(DP_CAT_WEIGHT, 0)
            weight_kg = round(weight_raw / 1000, 3) if weight_raw else None
            self.current_visit = Visit(
                started_at=now - timedelta(seconds=duration or 0),
                weight_kg=weight_kg,
            )
            self.db.add(self.current_visit)

        self.current_visit.ended_at = now
        self.current_visit.duration_seconds = duration
        self.current_visit.duration_source = "status_dp"
        self.current_visit.duration_is_estimated = False
        self._record_visit_diagnostic(
            self.current_visit,
            "completion_matched",
            {
                "strategy": "status_dp",
                "duration_seconds": duration,
                "completed_at": now,
            },
            now,
        )
        self._identify_visit_cat(self.current_visit, self.current_visit.weight_kg)
        self.db.commit()
        self.current_visit = None
        self.current_visit_excretion_times_at_start = None
        self.last_weight_at = None
    
    def _check_visit_timeout(self, now: datetime):
        """Reconcile overdue visits from Tuya logs before using a hard fallback."""
        if self.current_visit is None:
            return
        if self.last_weight_at is None:
            return

        elapsed = (now - self.last_weight_at).total_seconds()
        if elapsed < VISIT_TIMEOUT_SECONDS:
            return

        if self._try_reconcile_visit_completion_from_report_logs(now):
            return

        if elapsed < VISIT_HARD_TIMEOUT_SECONDS:
            logger.info(
                "Visit reconciliation pending after %.0fs — keeping visit open for retry",
                elapsed,
            )
            return

        logger.info("Visit hard-timed out after %.0fs — closing as unresolved fallback", elapsed)
        self.current_visit.ended_at = now
        self.current_visit.duration_seconds = None
        self.current_visit.duration_source = "hard_timeout"
        self.current_visit.duration_is_estimated = True
        self._record_visit_diagnostic(
            self.current_visit,
            "hard_timeout",
            {
                "elapsed_seconds": int(elapsed),
                "visit_timeout_seconds": VISIT_TIMEOUT_SECONDS,
                "visit_hard_timeout_seconds": VISIT_HARD_TIMEOUT_SECONDS,
                "last_weight_at": self.last_weight_at,
            },
            now,
        )
        self._identify_visit_cat(self.current_visit, self.current_visit.weight_kg)
        self.db.commit()
        self.current_visit = None
        self.current_visit_excretion_times_at_start = None
        self.last_weight_at = None

    def _try_reconcile_visit_completion_from_report_logs(self, now: datetime) -> bool:
        if self.current_visit is None:
            return False
        if self.cloud is None:
            logger.info("Skipping report-log reconciliation because cloud is unavailable")
            return False

        started_at = self.current_visit.started_at
        self._record_visit_diagnostic(
            self.current_visit,
            "reconciliation_attempt",
            {
                "started_at": started_at,
                "checked_at": now,
                "elapsed_seconds": int((now - (self.last_weight_at or started_at)).total_seconds()),
                "excretion_times_at_start": self.current_visit_excretion_times_at_start,
            },
            now,
        )
        try:
            logs = self._fetch_excretion_report_logs(started_at, now)
        except Exception as exc:
            logger.warning("Failed to fetch Tuya report logs for visit reconciliation: %s", exc)
            self._record_visit_diagnostic(
                self.current_visit,
                "pending_retry",
                {"reason": "report_log_fetch_failed", "error": str(exc)},
                now,
            )
            return False

        logger.info("Fetched %s Tuya report logs for visit reconciliation", len(logs))
        self._record_visit_diagnostic(
            self.current_visit,
            "report_logs_fetched",
            {"log_count": len(logs), "logs": self._summarize_report_logs(logs)},
            now,
        )
        completion = self._find_report_log_completion(logs, started_at, now)
        if completion is None:
            logger.info("No Tuya report-log completion found; pending_retry")
            self._record_visit_diagnostic(
                self.current_visit,
                "pending_retry",
                {"reason": "no_completion_match", "log_count": len(logs)},
                now,
            )
            return False

        logger.info(
            "Visit completed from Tuya report logs via %s — duration: %ss",
            completion.strategy,
            completion.duration_seconds,
        )
        self.current_visit.ended_at = completion.completed_at
        self.current_visit.duration_seconds = completion.duration_seconds
        self.current_visit.duration_source = (
            "report_log_counter" if completion.strategy == "counter" else "report_log_duration"
        )
        self.current_visit.duration_is_estimated = False
        if completion.weight_kg is not None:
            self.current_visit.weight_kg = completion.weight_kg
        self._record_visit_diagnostic(
            self.current_visit,
            "completion_matched",
            {
                "strategy": completion.strategy,
                "duration_seconds": completion.duration_seconds,
                "completed_at": completion.completed_at,
                "weight_kg": completion.weight_kg,
            },
            completion.completed_at,
        )
        self._identify_visit_cat(self.current_visit, self.current_visit.weight_kg)
        self.db.commit()
        self.current_visit = None
        self.current_visit_excretion_times_at_start = None
        self.last_weight_at = None
        return True

    def _fetch_excretion_report_logs(self, started_at: datetime, now: datetime) -> list[dict]:
        start_time = self._datetime_to_epoch_ms(
            started_at - timedelta(seconds=REPORT_LOG_LOOKBACK_BUFFER_SECONDS)
        )
        end_time = self._datetime_to_epoch_ms(
            now + timedelta(seconds=REPORT_LOG_LOOKAHEAD_BUFFER_SECONDS)
        )
        response = self.cloud.cloudrequest(
            f"/v2.0/cloud/thing/{DEVICE_ID}/report-logs",
            query={
                "codes": REPORT_LOG_CODES,
                "start_time": start_time,
                "end_time": end_time,
                "size": 100,
            },
        )
        if not response or not response.get("success"):
            raise RuntimeError(f"Unexpected Tuya report-log response: {response}")
        result = response.get("result") or {}
        logs = result.get("logs") or []
        if not isinstance(logs, list):
            raise RuntimeError(f"Unexpected Tuya report-log payload: {response}")
        return logs

    def _find_report_log_completion(
        self,
        logs: list[dict],
        started_at: datetime,
        now: datetime,
    ) -> Optional[ReportLogCompletion]:
        if not logs:
            return None

        started_ms = self._datetime_to_epoch_ms(started_at)
        now_ms = self._datetime_to_epoch_ms(now + timedelta(seconds=REPORT_LOG_LOOKAHEAD_BUFFER_SECONDS))
        sorted_logs = sorted(logs, key=lambda log: int(log.get("event_time") or 0))

        counter_completion = self._find_counter_completion(sorted_logs, started_ms, now_ms)
        if counter_completion is not None:
            completion_ms, _ = counter_completion
            duration = self._latest_int_log_value(
                sorted_logs,
                DP_EXCRETION_TIME,
                started_ms,
                completion_ms + REPORT_LOG_LOOKAHEAD_BUFFER_SECONDS * 1000,
            )
            if duration is not None and duration > 0:
                return self._build_report_log_completion(
                    sorted_logs,
                    started_ms,
                    completion_ms,
                    duration,
                    "counter",
                )

        duration_completion = self._find_duration_completion(sorted_logs, started_ms, now_ms)
        if duration_completion is None:
            return None

        completion_ms, duration = duration_completion
        return self._build_report_log_completion(
            sorted_logs,
            started_ms,
            completion_ms,
            duration,
            "duration_log",
        )

    def _find_counter_completion(
        self,
        logs: list[dict],
        started_ms: int,
        end_ms: int,
    ) -> Optional[tuple[int, int]]:
        completion_logs = []
        for log in logs:
            if log.get("code") != DP_EXCRETION_TIMES:
                continue
            event_time = self._coerce_int(log.get("event_time"))
            value = self._coerce_int(log.get("value"))
            if event_time is None or value is None:
                continue
            if event_time < started_ms or event_time > end_ms:
                continue
            if (
                self.current_visit_excretion_times_at_start is not None
                and value <= self.current_visit_excretion_times_at_start
            ):
                continue
            completion_logs.append((event_time, value))
        return completion_logs[-1] if completion_logs else None

    def _find_duration_completion(
        self,
        logs: list[dict],
        started_ms: int,
        end_ms: int,
    ) -> Optional[tuple[int, int]]:
        duration_logs = []
        for log in logs:
            if log.get("code") != DP_EXCRETION_TIME:
                continue
            event_time = self._coerce_int(log.get("event_time"))
            duration = self._coerce_int(log.get("value"))
            if event_time is None or duration is None:
                continue
            if duration <= 0:
                continue
            if event_time < started_ms or event_time > end_ms:
                continue
            duration_logs.append((event_time, duration))
        return duration_logs[-1] if duration_logs else None

    def _build_report_log_completion(
        self,
        logs: list[dict],
        started_ms: int,
        completion_ms: int,
        duration: int,
        strategy: str,
    ) -> ReportLogCompletion:
        weight_raw = self._latest_int_log_value(
            logs,
            DP_CAT_WEIGHT,
            started_ms,
            completion_ms + REPORT_LOG_LOOKAHEAD_BUFFER_SECONDS * 1000,
        )
        weight_kg = round(weight_raw / 1000, 3) if weight_raw else None
        return ReportLogCompletion(
            duration_seconds=duration,
            completed_at=datetime.fromtimestamp(completion_ms / 1000, timezone.utc),
            weight_kg=weight_kg,
            strategy=strategy,
        )

    def _latest_int_log_value(
        self,
        logs: list[dict],
        code: str,
        start_ms: int,
        end_ms: int,
    ) -> Optional[int]:
        latest_value = None
        latest_time = None
        for log in logs:
            if log.get("code") != code:
                continue
            event_time = self._coerce_int(log.get("event_time"))
            value = self._coerce_int(log.get("value"))
            if event_time is None or value is None:
                continue
            if event_time < start_ms or event_time > end_ms:
                continue
            if latest_time is None or event_time >= latest_time:
                latest_time = event_time
                latest_value = value
        return latest_value


    def _record_visit_diagnostic(self, visit: Visit, event_type: str, payload: dict, recorded_at: datetime):
        if self.db is None or visit is None:
            return
        if visit.id is None:
            self.db.flush()
        diagnostic = VisitDiagnostic(
            visit_id=visit.id,
            event_type=event_type,
            payload=self._json_safe(payload),
            recorded_at=recorded_at,
        )
        self.db.add(diagnostic)
        self.db.commit()

    def _summarize_report_logs(self, logs: list[dict], limit: int = 20) -> list[dict]:
        snippets = []
        for log in logs[:limit]:
            snippets.append({
                "code": log.get("code"),
                "value": log.get("value"),
                "event_time": log.get("event_time"),
            })
        return snippets

    def _json_safe(self, value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {str(k): self._json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._json_safe(v) for v in value]
        if isinstance(value, tuple):
            return [self._json_safe(v) for v in value]
        return value

    @staticmethod
    def _datetime_to_epoch_ms(value: datetime) -> int:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return int(value.timestamp() * 1000)

    @staticmethod
    def _coerce_int(value) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

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
                last_weight_at=now,
            )
            self.current_visit_excretion_times_at_start = self._coerce_int(
                self.previous_dps.get(DP_EXCRETION_TIMES)
            )
            self.db.add(self.current_visit)
            self.db.commit()
            self._record_visit_diagnostic(
                self.current_visit,
                "weight_seen",
                {
                    "weight_kg": weight_kg,
                    "raw_weight": raw_weight,
                    "excretion_times_at_start": self.current_visit_excretion_times_at_start,
                },
                now,
            )
        else:
            # Update weight on existing visit (take the latest reading)
            self.current_visit.weight_kg = weight_kg
            self.current_visit.last_weight_at = now
            self.db.commit()

    def _identify_visit_cat(self, visit: Visit, weight_kg: float):
        if weight_kg is None:
            logger.info("Visit has no weight reading — skipping cat identification")
            return

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
