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
from starlette.middleware.gzip import GZipMiddleware

from app.routers import cats, visits, cleaning_cycles, dashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

UPDATE_MODE = os.getenv("UPDATE_MODE", "polling")
if UPDATE_MODE not in ("polling", "webhook"):
    raise ValueError(f"UPDATE_MODE must be 'polling' or 'webhook', got: {UPDATE_MODE!r}")

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


def run_poller():
    """Runs the poller in a background thread."""
    from app.database import SessionLocal
    from app.poller import LitterboxPoller
    import app.routers.dashboard as dashboard_state

    logger.info("Poller thread started")
    while True:
        try:
            poller = LitterboxPoller(SessionLocal)
            while True:
                poller.poll()
                with dashboard_state._poll_lock:
                    dashboard_state.last_successful_poll_at = datetime.now(timezone.utc)
                time.sleep(POLL_INTERVAL_SECONDS)
        except Exception as e:
            logger.exception("Poller crashed, restarting")
            time.sleep(10)


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


app = FastAPI(title="Litterbox API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# API routes
app.include_router(cats.router)
app.include_router(visits.router)
app.include_router(cleaning_cycles.router)
app.include_router(dashboard.router)

if UPDATE_MODE == "webhook":
    from app.routers.webhook import router as webhook_router
    app.include_router(webhook_router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve uploaded cat photos
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Serve React frontend — must come AFTER API routes
if FRONTEND_DIST.exists():
    @app.get("/assets/{path:path}")
    async def serve_assets(path: str):
        file = FRONTEND_DIST / "assets" / path
        response = FileResponse(file)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Catch-all route that serves the React app for any non-API path."""
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    logger.warning(f"Frontend dist not found at {FRONTEND_DIST} — UI will not be served")