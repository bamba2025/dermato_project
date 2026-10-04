import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import (
    DUMMY_HASH,
    hash_refresh,
    issue_access,
    password_hash,
    verify_password,
)
from app.core.config import get_settings
from app.models import AuditLog, Consent, RefreshToken, User, UserProfile
from app.models.identity import utcnow
from app.schemas.identity import Credentials, Registration, Tokens


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def token_pair(db: Session, user: User, family_id: uuid.UUID | None = None) -> Tokens:
    raw = secrets.token_urlsafe(48)
    settings = get_settings()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh(raw),
            family_id=family_id or uuid.uuid4(),
            expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        )
    )
    return Tokens(
        access_token=issue_access(user),
        refresh_token=raw,
        expires_in=settings.access_token_minutes * 60,
    )


def register(db: Session, data: Registration) -> Tokens:
    user = User(email=str(data.email).lower(), password_hash=password_hash.hash(data.password))
    try:
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        db.add(Consent(user_id=user.id, kind="APPLICATION_USE", policy_version="1.0"))
        db.add(AuditLog(actor_id=user.id, action="auth.register"))
        tokens = token_pair(db, user)
        db.commit()
        return tokens
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Inscription impossible avec ces informations") from exc


def login(db: Session, data: Credentials) -> Tokens:
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    valid = verify_password(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Identifiants incorrects")
    tokens = token_pair(db, user)
    db.add(AuditLog(actor_id=user.id, action="auth.login"))
    db.commit()
    return tokens


def rotate(db: Session, raw: str) -> Tokens:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh(raw)).with_for_update()
    )
    if not token or token.revoked_at or aware(token.expires_at) <= utcnow():
        raise HTTPException(401, "Session expirée")
    if token.used_at:
        # Réutilisation d'un ancien jeton : invalider toute sa famille.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token.family_id)
            .values(revoked_at=utcnow())
        )
        db.add(AuditLog(actor_id=token.user_id, action="auth.refresh_reuse"))
        db.commit()
        raise HTTPException(401, "Session invalidée, reconnectez-vous")
    user = db.get(User, token.user_id)
    if not user:
        raise HTTPException(401, "Session expirée")
    token.used_at = utcnow()
    tokens = token_pair(db, user, token.family_id)
    db.commit()
    return tokens


def logout(db: Session, raw: str, user: User) -> None:
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh(raw), RefreshToken.user_id == user.id
        )
    )
    if token:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token.family_id)
            .values(revoked_at=utcnow())
        )
        db.add(AuditLog(actor_id=user.id, action="auth.logout"))
        db.commit()
