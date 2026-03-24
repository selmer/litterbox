# Plan: Polling / Webhook Dual-Mode Support

## Context

The app currently polls Tuya Cloud every N seconds for device state. The user wants an
alternative: receive push events from Tuya via webhooks through Tailscale Funnel. The mode
is selected via `UPDATE_MODE` env var. Both modes share all visit/cleaning cycle business
logic in `LitterboxPoller`.

---

## Files to Modify

| File | Action |
|------|--------|
| `app/poller.py` | Remove module-level env guards; add `mode` param; add threading lock; add `process_webhook_dps()` |
| `app/main.py` | Read `UPDATE_MODE`; branch lifespan; conditionally register webhook router |
| `app/routers/dashboard.py` | Add `update_mode` module var; skip time-based health check in webhook mode |
| `app/schemas.py` | Add `TuyaDPStatus` + `TuyaWebhookPayload` Pydantic models |
| `.env.example` | Add `UPDATE_MODE` and `WEBHOOK_SECRET` |
| `app/routers/webhook.py` | **NEW** — `POST /webhook/tuya` endpoint |

`conftest.py` requires no changes.

---

## Step-by-Step Implementation

### 1. `app/poller.py` — Remove module-level env guards

The current code raises `ValueError` at import time if Tuya env vars are absent. In webhook
mode these credentials aren't needed (no Tuya API calls are made). Remove the three guard
blocks:

```python
# REMOVE these three guard blocks (keep the os.getenv reads):
if not DEVICE_ID:
    raise ValueError(...)
if not TUYA_API_KEY:
    raise ValueError(...)
if not TUYA_API_SECRET:
    raise ValueError(...)
```

Move validation into `make_cloud()`:
```python
def make_cloud() -> tinytuya.Cloud:
    if not TUYA_API_KEY or not TUYA_API_SECRET:
        raise RuntimeError("Tuya API credentials not configured (polling mode requires TUYA_API_KEY and TUYA_API_SECRET)")
    return tinytuya.Cloud(...)
```

`DEVICE_ID` stays readable without guard — still used in webhook mode for payload filtering.

### 2. `app/poller.py` — Add `mode` param, threading lock, `process_webhook_dps()`

**`__init__` changes:**
```python
def __init__(self, session_factory, mode: str = "polling"):
    self.mode = mode
    self._lock = threading.Lock()   # protect against concurrent webhook calls
    # ... existing state init unchanged ...
    if mode == "polling":
        self._init_cloud()
    # webhook mode: skip _init_cloud(), previous_dps starts empty {}
```

Add `import threading` at the top of `poller.py`.

**New method** (mirrors the session management pattern of `poll()`):
```python
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
            self._check_visit_timeout(now)
            self._handle_changes(current_dps, now)

            self.previous_dps = current_dps
            self.current_visit_id = self.current_visit.id if self.current_visit else None
            self.current_cleaning_cycle_id = self.current_cleaning_cycle.id if self.current_cleaning_cycle else None
        finally:
            self.db = None
            db.close()
```

**Why merging works:** `_handle_changes(current_dps, now)` iterates over `current_dps` and
skips any dp where `self.previous_dps.get(dp) == value`. Since `current_dps` = previous +
changes, only the changed DPs differ → only those are processed. `_handle_visit_complete`
can still call `dps.get(DP_EXCRETION_TIME)` on the full merged dict. No changes to any
`_handle_*` methods.

### 3. `app/main.py` — Mode-aware lifespan and routing

Near top, after existing `POLL_INTERVAL_SECONDS`:
```python
UPDATE_MODE = os.getenv("UPDATE_MODE", "polling")
if UPDATE_MODE not in ("polling", "webhook"):
    raise ValueError(f"UPDATE_MODE must be 'polling' or 'webhook', got: {UPDATE_MODE!r}")
```

Replace `lifespan`:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if UPDATE_MODE == "polling":
        thread = threading.Thread(target=run_poller, daemon=True)
        thread.start()
        logger.info("Poller thread started (polling mode)")
    else:
        from app.database import SessionLocal
        from app.poller import LitterboxPoller
        app.state.webhook_poller = LitterboxPoller(SessionLocal, mode="webhook")
        import app.routers.dashboard as dashboard_state
        dashboard_state.update_mode = "webhook"
        logger.info("Webhook poller ready (webhook mode)")
    yield
    logger.info("Shutting down")
```

After `app.include_router(dashboard.router)`:
```python
if UPDATE_MODE == "webhook":
    from app.routers.webhook import router as webhook_router
    app.include_router(webhook_router)
```

### 4. `app/routers/dashboard.py` — Webhook-mode health check

Add module-level var below `last_successful_poll_at`:
```python
update_mode: str = "polling"   # set to "webhook" by main.py lifespan
```

Replace the `poller_healthy` assignment in `get_dashboard`:
```python
if update_mode == "webhook":
    poller_healthy = True   # webhook mode: healthy as long as app is running
else:
    poller_healthy = (
        last_poll is not None
        and (now - last_poll).total_seconds() < POLLER_HEALTHY_THRESHOLD_SECONDS
    )
```

### 5. `app/schemas.py` — Tuya webhook payload models

Add after existing schemas (import `Any` from `typing`):
```python
from typing import Any, Literal, Optional   # add Any

# --- Tuya webhook payload schemas ---

class TuyaDPStatus(BaseModel):
    code: str
    value: Any          # int, bool, or str depending on DP

class TuyaWebhookPayload(BaseModel):
    dataId: str
    devId: str
    productKey: Optional[str] = None
    status: list[TuyaDPStatus]
```

### 6. `app/routers/webhook.py` — New file

```python
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from app.schemas import TuyaWebhookPayload

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
_DEVICE_ID = os.getenv("TUYA_DEVICE_ID")


@router.post("/tuya", status_code=status.HTTP_204_NO_CONTENT)
async def receive_tuya_webhook(payload: TuyaWebhookPayload, request: Request):
    if _WEBHOOK_SECRET:
        if request.headers.get("X-Webhook-Secret") != _WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    if _DEVICE_ID and payload.devId != _DEVICE_ID:
        logger.debug(f"Ignoring webhook for device {payload.devId!r}")
        return

    changed_dps = {item.code: item.value for item in payload.status}
    if not changed_dps:
        return

    logger.info(f"Webhook received: {list(changed_dps.keys())}")

    poller = request.app.state.webhook_poller
    try:
        poller.process_webhook_dps(changed_dps)
    except Exception:
        logger.exception("Error processing webhook DPs")
        raise HTTPException(status_code=500, detail="Internal processing error")

    import app.routers.dashboard as dashboard_state
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
```

### 7. `.env.example` — Add new vars

Append after the polling intervals block:
```
# Update mode: "polling" (default) or "webhook"
# In webhook mode, configure Tuya IoT Platform to POST to POST /webhook/tuya
UPDATE_MODE=polling

# Optional shared secret — if set, require X-Webhook-Secret header on webhook calls
WEBHOOK_SECRET=
```

---

## What Does NOT Change

- All `_handle_*` methods in `LitterboxPoller` — untouched
- `conftest.py` — `LitterboxPoller(lambda: db_session)` still works; `mode` defaults to `"polling"`
- All existing tests — `UPDATE_MODE` unset → defaults to `"polling"` → same behavior
- `run_poller()` — unchanged, simply never called in webhook mode
- All existing routers and schemas

---

## Verification

1. **Polling mode (existing behavior):** `UPDATE_MODE=polling` (or unset) → app starts poller thread, `GET /dashboard` shows `poller_healthy` based on last poll time. `/webhook/tuya` route does NOT exist.

2. **Webhook mode:** `UPDATE_MODE=webhook` → no poller thread started, `GET /webhook/tuya` returns 405 (GET not allowed), `POST /webhook/tuya` with valid payload returns 204 and creates Visit/CleaningCycle records.

3. **Secret enforcement:** Set `WEBHOOK_SECRET=abc123`, send POST without header → 401. Send with `X-Webhook-Secret: abc123` → 204.

4. **Device filtering:** Set `TUYA_DEVICE_ID=mydev`, send payload with `devId=otherdev` → 204 but no DB writes.

5. **Run existing tests:** `python3 -m pytest tests/ -v` — all pass (no regressions).

6. **Tailscale Funnel:** `tailscale funnel 8000` exposes the FastAPI server. Register `https://<host>.ts.net/webhook/tuya` in Tuya IoT Platform → Message Subscription → device status topic.
