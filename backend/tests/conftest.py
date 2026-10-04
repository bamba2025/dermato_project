import os
import secrets

# Avant l'import de l'application : aucun secret fixe ni .env de production utilisé.
os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL="sqlite://",
    REDIS_URL="redis://localhost:6379/15",
    S3_ENDPOINT="http://localhost:9000",
    S3_BUCKET="derma-test",
    S3_ACCESS_KEY=secrets.token_hex(16),
    S3_SECRET_KEY=secrets.token_hex(32),
    JWT_SECRET=secrets.token_hex(32),
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.auth.dependencies import auth_rate_limit  # noqa: E402
from app.core.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db):
    def database():
        yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[auth_rate_limit] = lambda: None
    # Pas de lifespan : les connexions externes sont couvertes par la suite d'intégration.
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def registration():
    return {
        "email": "patient@example.com",
        "password": secrets.token_urlsafe(24),
        "application_consent": True,
    }
