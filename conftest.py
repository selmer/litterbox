import os

# Must be set before any app imports — database.py and poller.py raise at module level
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TUYA_DEVICE_ID", "test_device_id")
os.environ.setdefault("TUYA_API_KEY", "test_api_key")
os.environ.setdefault("TUYA_API_SECRET", "test_api_secret")

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.models import Base

# In-memory SQLite with a single shared connection — isolates tests without
# needing a real Postgres instance.
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture
def db():
    """Yields a database session with a clean schema for each test."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def client(db):
    """
    Yields a FastAPI TestClient with:
    - get_db overridden to use the in-memory test database
    - run_poller patched out so no background thread or Tuya calls happen
    """
    from app.database import get_db
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.run_poller"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
