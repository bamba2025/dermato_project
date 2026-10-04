"""Génère .env sans afficher les secrets ; compatible CI/Linux/Windows."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
if target.exists():
    raise SystemExit(".env existe déjà : aucune modification")
pg_secret, redis_secret, storage_secret, jwt_secret, seed_secret = (
    secrets.token_hex(32) for _ in range(5)
)
target.write_text(
    f"""ENVIRONMENT=development
POSTGRES_PASSWORD={pg_secret}
REDIS_PASSWORD={redis_secret}
MINIO_ROOT_USER=derma-local
MINIO_ROOT_PASSWORD={storage_secret}
JWT_SECRET={jwt_secret}
DATABASE_URL=postgresql+psycopg://derma:{pg_secret}@postgres:5432/derma
REDIS_URL=redis://:{redis_secret}@redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_BUCKET=derma-private
S3_ACCESS_KEY=derma-local
S3_SECRET_KEY={storage_secret}
CORS_ORIGINS=["http://localhost:3000"]
MODEL_BACKBONE=mock
MODEL_PATH=/models
MEDGEMMA_ENABLED=false
GPU_DEVICE=cpu
SEED_PASSWORD={seed_secret}
""",
    encoding="utf-8",
)
print(".env créé avec des secrets aléatoires, non affichés.")
