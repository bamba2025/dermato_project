import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

import boto3
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.api.identity import router
from app.core.config import get_settings
from app.core.database import session_factory

logger = logging.getLogger("derma.requests")
logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.redis = Redis.from_url(settings.redis_url, socket_timeout=2)
    app.state.s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )
    yield
    app.state.redis.close()


app = FastAPI(
    title="Derma AI — API",
    version="0.1.0",
    description="Phase 1. Aucune inférence ou sortie diagnostique dans cette version.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Les erreurs par défaut peuvent refléter le mot de passe dans le champ « input ».
    return JSONResponse(
        {"detail": [{"loc": e["loc"], "type": e["type"], "msg": e["msg"]} for e in exc.errors()]},
        status_code=422,
    )


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    if request.url.path.startswith("/api/v1/auth/"):
        response.headers["Cache-Control"] = "no-store"
    route = request.scope.get("route")
    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "method": request.method,
                # Route modèle uniquement : pas de query string, jeton ou données personnelles.
                "route": getattr(route, "path", "unmatched"),
                "status": response.status_code,
                "latency_ms": round((time.monotonic() - start) * 1000),
            }
        )
    )
    return response


@app.get("/health/live", tags=["health"])
def live() -> dict:
    return {"status": "ok", "phase": 1}


@app.get("/health/ready", tags=["health"])
def ready(request: Request) -> JSONResponse:
    checks = {}
    try:
        with session_factory()() as db:
            db.execute(text("SELECT 1"))
            db.execute(text("SELECT version_num FROM alembic_version"))
        checks["database"] = True
    except Exception:
        checks["database"] = False
    try:
        checks["redis"] = bool(request.app.state.redis.ping())
    except Exception:
        checks["redis"] = False
    try:
        request.app.state.s3.head_bucket(Bucket=get_settings().s3_bucket)
        checks["storage"] = True
    except Exception:
        checks["storage"] = False
    success = all(checks.values())
    return JSONResponse({"ready": success, "checks": checks}, status_code=200 if success else 503)


app.include_router(router)
