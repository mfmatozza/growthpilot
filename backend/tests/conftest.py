import os

# Must be set before `app.main` is imported anywhere — Settings() reads env
# once and get_settings() caches the result for the process lifetime.
os.environ.setdefault("ADMIN_EMAIL", "test@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "test-password")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.site import Site

TEST_AUTH_HEADERS = {"Authorization": "Bearer test-secret-key"}

# SQLite in-memory for tests — no Postgres dependency in CI. All models use
# generic SQLAlchemy types (JSON, non-native Enum) specifically so this works;
# see docs/DECISIONS.md if that ever needs to change.
_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
_TestSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@event.listens_for(_engine, "connect")
def _enable_sqlite_fk_cascades(dbapi_connection, _):
    # SQLite ignores ondelete="CASCADE" unless FK enforcement is turned on
    # per-connection — without this, deleting a site would silently leave
    # its keywords/articles/etc orphaned instead of cascading, unlike Postgres.
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


@pytest.fixture
def db_session():
    Base.metadata.create_all(_engine)
    session = _TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers=TEST_AUTH_HEADERS) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class SequencedLLM:
    """Feeds each successive complete_json call its own canned FakeLLMClient
    response in order — for pipelines (like keyword research) that call the
    LLM more than once per run with different expected response shapes."""

    def __init__(self, *responses):
        self._responses = list(responses)

    def complete_json(self, **kwargs):
        return self._responses.pop(0).complete_json(**kwargs)

    def complete_text(self, **kwargs):
        raise NotImplementedError


class RoutedLLM:
    """Routes every complete_json call to one fake client and every
    complete_text call to another, each called as many times as needed —
    for pipelines (like article generation) that call complete_json once
    and complete_text repeatedly (once per section) in the same run."""

    def __init__(self, json_client, text_client):
        self._json_client = json_client
        self._text_client = text_client

    def complete_json(self, **kwargs):
        return self._json_client.complete_json(**kwargs)

    def complete_text(self, **kwargs):
        return self._text_client.complete_text(**kwargs)


@pytest.fixture
def site(db_session: Session) -> Site:
    site = Site(url="https://example.com", name="Example Co")
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site
