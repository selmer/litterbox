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
