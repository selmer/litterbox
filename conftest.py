"""
Root-level pytest configuration.

Sets required environment variables BEFORE any app module is imported so that
database.py and poller.py don't raise ValueError/RuntimeError at import time.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TUYA_DEVICE_ID", "test-device")
os.environ.setdefault("TUYA_API_KEY", "test-key")
os.environ.setdefault("TUYA_API_SECRET", "test-secret")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from app.database import get_db
from app.models import Base
from app.routers import cats, visits, cleaning_cycles, dashboard


# ---------------------------------------------------------------------------
# In-memory SQLite engine (shared across the session, reset per test)
# ---------------------------------------------------------------------------

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _make_app() -> FastAPI:
    """Build a minimal FastAPI app with all API routers but no poller thread."""
    app = FastAPI()
    app.include_router(cats.router)
    app.include_router(visits.router)
    app.include_router(cleaning_cycles.router)
    app.include_router(dashboard.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """Fresh in-memory database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    """TestClient wired to the in-memory database."""
    app = _make_app()
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_cloud():
    """Returns a MagicMock that looks like a tinytuya.Cloud instance."""
    cloud = MagicMock()
    cloud.getstatus.return_value = {"success": True, "result": []}
    return cloud
