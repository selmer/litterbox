# Plan: Migrate to Tuya Cloud Webhooks (with Polling Fallback)

## Context

Litterbox currently polls the Tuya Cloud API every N seconds to detect device state changes. This introduces latency (up to `POLL_INTERVAL_SECONDS`) and wastes API quota on unchanged state. The goal is to migrate to Tuya's HTTP push (webhook) model, where Tuya proactively sends device DP changes to a registered HTTPS endpoint. Since the NAS is not publicly accessible, Tailscale Funnel will expose a public HTTPS endpoint that proxies into the local FastAPI app. A `LITTERBOX_MODE` env var allows toggling between modes without code changes.

## Key Decisions

- **Both modes reuse the same state machine** — extract DP-processing logic from `LitterboxPoller` into a new `LitterboxEventHandler` class; both modes call it
- **`poller_healthy` field in dashboard stays** — populated from whichever mode is active; no frontend changes needed
- **Webhook mode requires single worker** — `LitterboxEventHandler` holds visit state in memory; multi-worker uvicorn would diverge state
- **Signature verification is defensive** — log mismatches to ease initial calibration of Tuya's exact signing format

---

## Phase 0: Set Up Tailscale Funnel on NAS

Run these commands **on the NAS** (SSH in first):

```bash
# Verify Tailscale is authenticated
tailscale status

# Enable Funnel for port 8001 (the litterbox app port)
sudo tailscale funnel --bg 8001

# Get your public Funnel URL
tailscale funnel status
```

The output will show a URL like `https://<hostname>.<tailnet>.ts.net`. **This is the base URL to register with Tuya.** The webhook path will be `https://<hostname>.<tailnet>.ts.net/webhook/tuya`.

Funnel persists across reboots automatically once enabled with `--bg`.

---

## Phase 1: Extract `app/event_handler.py`

**New file.** Move these from `LitterboxPoller` into `LitterboxEventHandler`:

**Attributes to move:**
- `previous_dps`, `current_visit`, `current_visit_id`, `current_cleaning_cycle`, `current_cleaning_cycle_id`, `last_snapshot_at`, `last_weight_at`

**Methods to move (unchanged logic):**
- `_handle_changes`, `_handle_visit_complete`, `_check_visit_timeout`, `_handle_weight_update`, `_identify_visit_cat`, `_handle_cleaning_cycle`, `_record_setting_change`, `_maybe_snapshot`

**Constants to move:**
- `SETTINGS_DPS`, `VISIT_TIMEOUT_SECONDS`, `DP_CAT_WEIGHT`, `DP_CLEANING_CYCLE`, `DP_EXCRETION_TIMES`, `DP_EXCRETION_TIME`, `SNAPSHOT_INTERVAL_SECONDS`

**Public interface:**

```python
class LitterboxEventHandler:
    def __init__(self, session_factory):
        ...  # initialise all state attributes

    def handle_dps(
        self,
        dps: dict,
        now: datetime,
        *,
        diff: bool = True,
        snapshot: bool = True,
    ) -> None:
        """
        Process incoming DPs.
        diff=True  → skip DPs unchanged from previous_dps (polling mode)
        diff=False → treat all DPs as changes (webhook mode — Tuya only sends deltas)
        snapshot=False → skip _maybe_snapshot (webhook sends partial DPs, not full state)
        Caller must set self.db to an open session before calling.
        """
```

The `diff` flag threads into `_handle_changes` to conditionally skip the `if self.previous_dps.get(dp) == value: continue` guard.

---

## Phase 2: Refactor `app/poller.py`

`LitterboxPoller` becomes a thin wrapper around `LitterboxEventHandler`:

```python
from app.event_handler import LitterboxEventHandler

class LitterboxPoller:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.handler = LitterboxEventHandler(session_factory)
        self._init_cloud()

    def poll(self):
        # ... cloud fetch unchanged ...
        db = self.session_factory()
        try:
            self.handler.db = db
            # Rehydrate in-progress objects (unchanged logic)
            self.handler.current_visit = db.get(Visit, self.handler.current_visit_id) if self.handler.current_visit_id else None
            self.handler.current_cleaning_cycle = db.get(CleaningCycle, self.handler.current_cleaning_cycle_id) if self.handler.current_cleaning_cycle_id else None
            now = datetime.now(timezone.utc)
            self.handler._check_visit_timeout(now)
            self.handler.handle_dps(dps, now, diff=True, snapshot=True)
            # Persist IDs for next poll
            self.handler.current_visit_id = self.handler.current_visit.id if self.handler.current_visit else None
            self.handler.current_cleaning_cycle_id = self.handler.current_cleaning_cycle.id if self.handler.current_cleaning_cycle else None
        finally:
            self.handler.db = None
            db.close()
```

All Tuya cloud init/connection code stays in `LitterboxPoller` unchanged.

---

## Phase 3: Create `app/routers/webhook.py`

New router with:

**Pydantic models for payload:**
```python
class TuyaDP(BaseModel):
    code: str
    t: int
    value: Any

class TuyaWebhookPayload(BaseModel):
    data: dict  # contains devId + status list
    sign: str
    t: int
```

**Signature verification:**
```python
def _verify_signature(body_bytes: bytes, sign: str, t: int) -> bool:
    if not TUYA_WEBHOOK_SECRET:
        logger.warning("TUYA_WEBHOOK_SECRET not set — skipping verification")
        return True
    # Tuya IoT Core webhook signing: HMAC-SHA256(secret, str(t) + raw_body)
    # Log mismatches so the canonical string can be adjusted from real traffic
    canonical = str(t).encode() + body_bytes
    expected = hmac.new(TUYA_WEBHOOK_SECRET.encode(), canonical, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sign):
        logger.warning("Signature mismatch. t=%s, expected=%s, got=%s", t, expected, sign)
        return False
    return True
```

> **Note:** Tuya's exact signing canonical string varies by API version. The implementation above covers the most common form. On first real traffic, if verification fails, the log output will show what was computed — adjust `canonical` construction from there.

**Endpoint:**
```python
@router.post("/tuya")
async def receive_tuya_webhook(request: Request, db: Session = Depends(get_db)):
    body_bytes = await request.body()
    payload = TuyaWebhookPayload.model_validate_json(body_bytes)

    if not _verify_signature(body_bytes, payload.sign, payload.t):
        raise HTTPException(status_code=401, detail="Invalid signature")

    dev_id = payload.data.get("devId")
    if dev_id != TUYA_DEVICE_ID:
        return {"ok": True}  # ack unknown device, no processing

    dps = {item["code"]: item["value"] for item in payload.data.get("status", [])}
    now = datetime.now(timezone.utc)

    handler = request.app.state.event_handler
    async with request.app.state.webhook_lock:  # serialise concurrent webhooks
        handler.db = db
        try:
            handler._check_visit_timeout(now)
            handler.handle_dps(dps, now, diff=False, snapshot=False)
        finally:
            handler.db = None

    with dashboard_state._event_lock:
        dashboard_state.last_webhook_received_at = now

    return {"ok": True}
```

The `asyncio.Lock` on `app.state.webhook_lock` serialises concurrent webhook requests so handler state is never accessed by two requests simultaneously.

---

## Phase 4: Update `app/main.py`

```python
import asyncio
LITTERBOX_MODE = os.getenv("LITTERBOX_MODE", "polling")

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import SessionLocal
    if LITTERBOX_MODE == "webhook":
        logger.info("Starting in WEBHOOK mode — no poller thread")
        # NOTE: requires --workers 1; multi-worker = diverged visit state
        from app.event_handler import LitterboxEventHandler
        app.state.event_handler = LitterboxEventHandler(SessionLocal)
        app.state.webhook_lock = asyncio.Lock()
    else:
        logger.info("Starting in POLLING mode")
        thread = threading.Thread(target=run_poller, daemon=True)
        thread.start()
    yield
```

Register webhook router unconditionally (returns 503 if handler not initialised, useful for debugging):
```python
from app.routers import webhook
app.include_router(webhook.router)
```

---

## Phase 5: Update `app/routers/dashboard.py`

Add alongside existing poll state:
```python
LITTERBOX_MODE = os.getenv("LITTERBOX_MODE", "polling")
WEBHOOK_HEALTHY_THRESHOLD_SECONDS = int(os.getenv("WEBHOOK_HEALTHY_THRESHOLD_SECONDS", "3600"))

_event_lock = threading.Lock()
last_webhook_received_at: Optional[datetime] = None
```

In `get_dashboard`, drive `poller_healthy` from whichever mode is active:
```python
if LITTERBOX_MODE == "webhook":
    with _event_lock:
        last = last_webhook_received_at
    poller_healthy = last is not None and (now - last).total_seconds() < WEBHOOK_HEALTHY_THRESHOLD_SECONDS
else:
    with _poll_lock:
        last = last_successful_poll_at
    poller_healthy = last is not None and (now - last).total_seconds() < POLLER_HEALTHY_THRESHOLD_SECONDS
```

No schema or frontend changes needed.

---

## Phase 6: Update `conftest.py` and Tests

**`conftest.py` additions:**
```python
os.environ.setdefault("LITTERBOX_MODE", "polling")
os.environ.setdefault("TUYA_WEBHOOK_SECRET", "test_secret")

@pytest.fixture
def event_handler(db_session):
    from app.event_handler import LitterboxEventHandler
    h = LitterboxEventHandler(lambda: db_session)
    h.db = db_session
    return h
```

Update `poller` fixture: `p.handler.db = db_session` (instead of `p.db = db_session`).

Migrate existing `test_poller.py` state-machine tests to `test_event_handler.py` using the `event_handler` fixture (change `poller.x` → `event_handler.x`). Keep a minimal `test_poller.py` covering just the polling loop / cloud interaction.

**New `tests/test_api_webhook.py`** covering:
1. Invalid signature → 401
2. Unknown device ID → 200, no DB writes
3. `cat_weight` DP → `Visit` created
4. `excretion_times_day` DP after weight → visit closed with cat identified
5. `smart_clean: true` → `CleaningCycle` created
6. `smart_clean: false` after true → cycle closed
7. Settings DP → `SettingsHistory` entry created
8. Successful request updates `last_webhook_received_at`

Use a `webhook_client` fixture that sets `app.state.event_handler` and `app.state.webhook_lock` before yielding `TestClient(app)`.

---

## Phase 7: Update `.env.example`

```
# Event mode: 'polling' (default) or 'webhook'
LITTERBOX_MODE=polling

# Required when LITTERBOX_MODE=webhook
# From Tuya IoT Platform → Cloud → Messaging Service → signing secret
TUYA_WEBHOOK_SECRET=

# Health check thresholds (seconds)
POLLER_HEALTHY_THRESHOLD_SECONDS=30   # polling mode
WEBHOOK_HEALTHY_THRESHOLD_SECONDS=3600  # webhook mode (device may be idle)
```

---

## Phase 8: Tuya Developer Portal Setup

1. Log into [iot.tuya.com](https://iot.tuya.com) → Cloud → your project
2. Navigate to **Messaging Service** (or **Event Subscription** / **Automation** depending on plan tier)
3. Enable **Device Status Push** for your device
4. Set **Notification URL** to `https://<your-funnel-hostname>/webhook/tuya`
5. Copy the **Message Signing Secret** → set as `TUYA_WEBHOOK_SECRET` in `.env`
6. Subscribe to **Device ID** = `TUYA_DEVICE_ID` events
7. Use the portal's **Send Test** button → verify the NAS receives it and returns HTTP 200
8. If signature verification fails on first real traffic, check the server logs — the `logger.warning` in `_verify_signature` shows the computed canonical string; adjust the `canonical` construction to match

---

## Implementation Order

Execute in this sequence (each step leaves tests green):

1. `app/event_handler.py` — new file, extract methods (no deletions yet)
2. `conftest.py` — add `event_handler` fixture, env var defaults
3. `tests/test_event_handler.py` — migrate state-machine tests; run suite ✓
4. `app/poller.py` — refactor to use handler; update `poller` fixture; run suite ✓
5. `app/routers/webhook.py` — new router
6. `tests/test_api_webhook.py` — webhook endpoint tests; run suite ✓
7. `app/main.py` — conditional startup + app state
8. `app/routers/dashboard.py` — dual-mode health
9. `.env.example` — new vars
10. Tailscale Funnel on NAS (Phase 0)
11. Tuya portal setup (Phase 8)
12. Deploy with `LITTERBOX_MODE=webhook`

## Files Modified

| File | Change |
|------|--------|
| `app/event_handler.py` | NEW — shared state machine |
| `app/routers/webhook.py` | NEW — Tuya webhook endpoint |
| `tests/test_event_handler.py` | NEW — migrated state-machine tests |
| `tests/test_api_webhook.py` | NEW — webhook endpoint tests |
| `app/poller.py` | Thin wrapper; delegate to `LitterboxEventHandler` |
| `app/main.py` | Conditional thread/handler startup; register webhook router |
| `app/routers/dashboard.py` | Dual-mode health tracking |
| `conftest.py` | New fixtures; env var defaults |
| `.env.example` | `LITTERBOX_MODE`, `TUYA_WEBHOOK_SECRET`, threshold vars |

## Verification

```bash
# After implementation:
python3 -m pytest tests/ -v

# Smoke test webhook mode locally:
LITTERBOX_MODE=webhook uvicorn app.main:app --reload
curl -X POST http://localhost:8001/webhook/tuya \
  -H "Content-Type: application/json" \
  -d '{"data":{"devId":"test","status":[]},"sign":"x","t":1}'
# Expect 401 (bad sig) or 200 (if TUYA_WEBHOOK_SECRET unset)

# After Tuya portal setup:
# Use the portal Test button → verify server logs show received event
# Set LITTERBOX_MODE=webhook, redeploy, observe dashboard shows connection_healthy
```
