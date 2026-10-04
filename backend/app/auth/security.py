import hashlib
import secrets
import uuid
from datetime import timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.models.identity import User, utcnow

password_hash = PasswordHash.recommended()
# Vérification factice pour réduire la différence de durée entre comptes connus et inconnus.
DUMMY_HASH = password_hash.hash(secrets.token_urlsafe(32))


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_access(user: User) -> str:
    settings = get_settings()
    now = utcnow()
    return jwt.encode(
        {
            "sub": str(user.id),
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "type": "access",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access(token: str) -> uuid.UUID:
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={"require": ["exp", "iat", "sub", "jti", "type", "iss", "aud"]},
    )
    if payload["type"] != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return uuid.UUID(payload["sub"])
