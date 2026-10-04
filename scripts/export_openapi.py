"""Export reproductible du contrat sans connexion aux services ni secret réel."""

import json
import os
import secrets
from pathlib import Path

os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL="sqlite://",
    REDIS_URL="redis://localhost:6379",
    S3_ENDPOINT="http://localhost:9000",
    S3_ACCESS_KEY=secrets.token_hex(16),
    S3_SECRET_KEY=secrets.token_hex(32),
    JWT_SECRET=secrets.token_hex(32),
)
from app.main import app  # noqa: E402

target = Path(__file__).resolve().parents[1] / "docs" / "openapi.json"
target.write_text(
    json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
)
print(f"OpenAPI exporté : {target.name}")
