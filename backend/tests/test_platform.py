import logging
import secrets

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from redis.exceptions import ConnectionError
from sqlalchemy import create_engine, inspect
from starlette.requests import Request

from app.auth.dependencies import auth_rate_limit
from app.core.config import Settings
from app.main import app
from app.models import Base


def test_openapi_and_no_sensitive_request_log(client, caplog):
    with caplog.at_level(logging.INFO, logger="derma.requests"):
        assert client.get("/health/live?private=secret-do-not-log").status_code == 200
    assert "secret-do-not-log" not in caplog.text
    schema = client.get("/openapi.json").json()
    assert "/api/v1/auth/register" in schema["paths"]
    assert "/api/v1/auth/refresh" in schema["paths"]
    assert "/api/v1/me" in schema["paths"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]


def test_production_rejects_unsafe_configuration():
    values = dict(
        environment="production",
        database_url="sqlite://",
        redis_url="redis://localhost",
        s3_endpoint="http://localhost:9000",
        s3_access_key=secrets.token_hex(16),
        s3_secret_key=secrets.token_hex(32),
        jwt_secret=secrets.token_hex(32),
    )
    with pytest.raises(ValueError):
        Settings(_env_file=None, **values)
    with pytest.raises(ValueError):
        Settings(_env_file=None, **{**values, "environment": "test", "jwt_secret": "short"})


def test_rate_limiter_and_unavailable_redis():
    class Counter:
        def __init__(self):
            self.count = 0

        def eval(self, *_):
            self.count += 1
            return self.count

    app.state.redis = Counter()
    request = Request({"type": "http", "app": app, "client": ("127.0.0.1", 1234)})
    for _ in range(10):
        auth_rate_limit(request)
    with pytest.raises(HTTPException) as error:
        auth_rate_limit(request)
    assert error.value.status_code == 429

    class Broken:
        def eval(self, *_):
            raise ConnectionError()

    app.state.redis = Broken()
    with pytest.raises(HTTPException) as error:
        auth_rate_limit(request)
    assert error.value.status_code == 503


def test_migration_roundtrip_and_schema_alignment(tmp_path, monkeypatch):
    from app.core.config import get_settings

    path = tmp_path / "migration.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path.as_posix()}")
    get_settings.cache_clear()
    config = Config("alembic.ini")
    try:
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{path.as_posix()}")
        inspector = inspect(engine)
        assert set(inspector.get_table_names()) == {*Base.metadata.tables, "alembic_version"}
        for name, table in Base.metadata.tables.items():
            assert {c["name"] for c in inspector.get_columns(name)} == set(table.columns.keys())
        engine.dispose()
        command.downgrade(config, "base")
        engine = create_engine(f"sqlite:///{path.as_posix()}")
        assert inspect(engine).get_table_names() == ["alembic_version"]
        engine.dispose()
    finally:
        get_settings.cache_clear()
