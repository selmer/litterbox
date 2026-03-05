import logging
import os
import time
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import cats, visits, cleaning_cycles, dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


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
            logger.exception("Poller crashed, restarting")
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

# API routes
app.include_router(cats.router)
app.include_router(visits.router)
app.include_router(cleaning_cycles.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve React frontend — must come AFTER API routes
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Catch-all route that serves the React app for any non-API path."""
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    logger.warning(f"Frontend dist not found at {FRONTEND_DIST} — UI will not be served")