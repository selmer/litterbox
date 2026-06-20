import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TuyaWebhookPayload
from app.settings import resolve_tuya_config

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")


@router.post("/tuya", status_code=status.HTTP_204_NO_CONTENT)
async def receive_tuya_webhook(payload: TuyaWebhookPayload, request: Request, db: Session = Depends(get_db)):
    if _WEBHOOK_SECRET:
        if request.headers.get("X-Webhook-Secret") != _WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

    device_id = resolve_tuya_config(db).device_id
    if device_id and payload.devId != device_id:
        logger.debug("Ignoring webhook for device %r", payload.devId)
        return

    changed_dps = {item.code: item.value for item in payload.status}
    if not changed_dps:
        return

    logger.info("Webhook received: %s", list(changed_dps.keys()))

    poller = request.app.state.webhook_poller
    try:
        poller.process_webhook_dps(changed_dps)
    except Exception:
        logger.exception("Error processing webhook DPs")
        raise HTTPException(status_code=500, detail="Internal processing error")

    import app.routers.dashboard as dashboard_state
    with dashboard_state._poll_lock:
        dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
