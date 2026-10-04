from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.auth.security import decode_access
from app.core.config import get_settings
from app.core.database import get_db
from app.models import User

bearer = HTTPBearer(auto_error=False)


def current_user(
    credential: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    error = HTTPException(401, "Authentification requise", headers={"WWW-Authenticate": "Bearer"})
    if credential is None:
        raise error
    try:
        user_id = decode_access(credential.credentials)
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise error from exc
    user = db.get(User, user_id)
    if user is None:
        raise error
    return user


def require_roles(*roles: str) -> Callable:
    def check(user: User = Depends(current_user)) -> User:
        # Le rôle est lu en base, jamais depuis une valeur fournie par le client.
        if user.role not in roles:
            raise HTTPException(403, "Accès refusé")
        return user

    return check


def auth_rate_limit(request: Request) -> None:
    settings = get_settings()
    # Ne pas faire confiance à X-Forwarded-For sans configuration du proxy.
    peer = request.client.host if request.client else "unknown"
    key = f"auth-rate:{peer}"
    try:
        count = request.app.state.redis.eval(
            "local n = redis.call('INCR', KEYS[1]); "
            "if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end; return n",
            1,
            key,
            settings.auth_rate_window_seconds,
        )
    except RedisError as exc:
        raise HTTPException(503, "Authentification temporairement indisponible") from exc
    if count > settings.auth_rate_limit:
        raise HTTPException(
            429,
            "Réessayez plus tard",
            headers={"Retry-After": str(settings.auth_rate_window_seconds)},
        )
