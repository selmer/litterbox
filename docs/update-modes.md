# Update Modes: Polling vs Webhook

Litterbox supports two ways to receive device state from Tuya. Set `UPDATE_MODE` in your
`.env` to choose.

---

## Polling mode (default)

```
UPDATE_MODE=polling
```

The app starts a background thread that calls the Tuya Cloud API every
`POLL_INTERVAL_SECONDS` (default: 300 s as startup default, typically set to 5 s in
`.env`). No inbound network access is required.

All Tuya credentials must be present:

```
TUYA_DEVICE_ID=...
TUYA_API_KEY=...
TUYA_API_SECRET=...
TUYA_API_REGION=eu   # or us, cn, in
```

The dashboard's `poller_healthy` field turns `false` if no successful poll has been
recorded within `POLL_INTERVAL_SECONDS × 3` seconds.

---

## Webhook mode

```
UPDATE_MODE=webhook
```

The app registers a `POST /webhook/tuya` endpoint and waits for Tuya to push device status
changes. No background polling thread is started, and Tuya API credentials are not required
at runtime (though `TUYA_DEVICE_ID` is still used to filter payloads).

The dashboard's `poller_healthy` field is always `true` in this mode (the app is healthy as
long as it's running).

### Endpoint

```
POST /webhook/tuya
Content-Type: application/json
```

Expected payload (Tuya Message Subscription format):

```json
{
  "dataId": "abc123",
  "devId": "your-device-id",
  "productKey": "optional",
  "status": [
    { "code": "cat_weight", "value": 4200 },
    { "code": "smart_clean", "value": false }
  ]
}
```

Returns `204 No Content` on success.

### Optional shared secret

Set `WEBHOOK_SECRET` to require callers to include a matching header:

```
WEBHOOK_SECRET=your-secret-here
```

Every request must then include:

```
X-Webhook-Secret: your-secret-here
```

Requests with a missing or wrong header receive `401 Unauthorized`.

### Exposing the endpoint via Tailscale Funnel

```bash
tailscale funnel 8000
```

This gives you a public HTTPS URL like `https://hostname.ts.net`. Register it in the
Tuya IoT Platform under **Message Subscription → Device Status** for your product.

The full webhook URL to register is:

```
https://hostname.ts.net/webhook/tuya
```

---

## Switching modes

1. Update `UPDATE_MODE` in `.env`
2. Restart the app (`docker compose up --build -d` or `uvicorn app.main:app --reload`)

The `/webhook/tuya` route does **not** exist in polling mode (returns 404).
Polling does **not** start in webhook mode.

---

## Environment variable reference

| Variable | Default | Description |
|---|---|---|
| `UPDATE_MODE` | `polling` | `polling` or `webhook` |
| `POLL_INTERVAL_SECONDS` | `300` | Seconds between Tuya API polls (polling mode only) |
| `WEBHOOK_SECRET` | *(unset)* | If set, required in `X-Webhook-Secret` request header |
| `TUYA_DEVICE_ID` | — | Device ID; used to filter webhook payloads in both modes |
| `TUYA_API_KEY` | — | Required in polling mode |
| `TUYA_API_SECRET` | — | Required in polling mode |
| `TUYA_API_REGION` | `eu` | Tuya cloud region (`eu`, `us`, `cn`, `in`) |
