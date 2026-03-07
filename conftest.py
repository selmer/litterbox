import os

# Must be set before any app imports to avoid module-level errors
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("TUYA_DEVICE_ID", "test_device_id")
os.environ.setdefault("TUYA_API_KEY", "test_api_key")
os.environ.setdefault("TUYA_API_SECRET", "test_api_secret")

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models import Base
from app.database import get_db
from app.main import app


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient backed by an in-memory SQLite database.

    The Tuya poller background thread is patched out so tests don't
    require real device credentials.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.run_poller"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture
def poller(db_session):
    """LitterboxPoller with a mocked Tuya cloud connection.

    Uses the same in-memory SQLite db_session so database interactions
    (visits, cleaning cycles, etc.) can be verified after each call.
    """
    mock_cloud = MagicMock()
    mock_cloud.getstatus.return_value = {"success": True, "result": []}
    with patch("app.poller.make_cloud", return_value=mock_cloud):
        from app.poller import LitterboxPoller
        p = LitterboxPoller(db_session)
    yield p
