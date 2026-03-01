import logging
import os
import time
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routers import cats, visits, cleaning_cycles, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))


def run_poller():
    """Runs the poller in a background thread."""
    from app.database import SessionLocal
    from app.poller import LitterboxPoller
    import app.routers.dashboard as dashboard_state

    logger.info("Poller thread started")
    while True:
        db = None
        try:
            db = SessionLocal()
            poller = LitterboxPoller(db)
            while True:
                poller.poll()
                dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
                time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Poller crashed, restarting: {e}")
            time.sleep(10)
        finally:
            if db:
                db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=run_poller, daemon=True)
    thread.start()
    logger.info("Poller started")
    yield
    logger.info("Shutting down")


app = FastAPI(title="Litterbox API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cats.router)
app.include_router(visits.router)
app.include_router(cleaning_cycles.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}