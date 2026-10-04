from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import auth_rate_limit, current_user, require_roles
from app.core.database import get_db
from app.models import AuditLog, User, UserProfile
from app.schemas.identity import (
    Credentials,
    ProfileRead,
    ProfileUpdate,
    RefreshRequest,
    Registration,
    Tokens,
    UserRead,
)
from app.services import auth

router = APIRouter(prefix="/api/v1")
auth_router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(auth_rate_limit)])


@auth_router.post("/register", response_model=Tokens, status_code=201)
def register(data: Registration, db: Session = Depends(get_db)) -> Tokens:
    return auth.register(db, data)


@auth_router.post("/login", response_model=Tokens)
def login(data: Credentials, db: Session = Depends(get_db)) -> Tokens:
    return auth.login(db, data)


@auth_router.post("/refresh", response_model=Tokens)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> Tokens:
    return auth.rotate(db, data.refresh_token)


@auth_router.post("/logout", status_code=204)
def logout(
    data: RefreshRequest, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Response:
    auth.logout(db, data.refresh_token, user)
    return Response(status_code=204)


@router.get("/me", response_model=UserRead, tags=["profile"])
def me(user: User = Depends(current_user)) -> User:
    return user


@router.get("/me/profile", response_model=ProfileRead, tags=["profile"])
def profile(user: User = Depends(current_user), db: Session = Depends(get_db)) -> UserProfile:
    result = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if not result:
        raise HTTPException(404, "Profil absent")
    return result


@router.patch("/me", response_model=ProfileRead, tags=["profile"])
def update_profile(
    data: ProfileUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    result = profile(user, db)
    result.display_name = data.display_name
    result.language = data.language
    db.add(AuditLog(actor_id=user.id, action="profile.update", resource_id=result.id))
    db.commit()
    return result


@router.get("/dermatologist/access", tags=["dermatologist"])
def dermatologist_access(
    user: User = Depends(require_roles("DERMATOLOGIST", "ADMIN")),
) -> dict:
    return {"user_id": str(user.id), "role": user.role}


router.include_router(auth_router)
