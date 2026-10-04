import uuid
from datetime import timedelta

import jwt
from sqlalchemy import select

from app.auth.security import hash_refresh
from app.core.config import get_settings
from app.models import Consent, RefreshToken, User
from app.models.identity import utcnow


def headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_validation_does_not_echo_password(client, registration):
    short = "secret123"
    response = client.post("/api/v1/auth/register", json={**registration, "password": short})
    assert response.status_code == 422
    assert short not in response.text
    assert "input" not in response.text


def test_registration_login_and_private_profile(client, db, registration):
    response = client.post("/api/v1/auth/register", json=registration)
    assert response.status_code == 201
    tokens = response.json()
    assert response.headers["cache-control"] == "no-store"
    assert client.get("/api/v1/me").status_code == 401
    me = client.get("/api/v1/me", headers=headers(tokens)).json()
    assert me["role"] == "USER"
    assert "password_hash" not in me
    user = db.get(User, uuid.UUID(me["id"]))
    assert user.password_hash != registration["password"]
    refresh = db.scalar(select(RefreshToken))
    assert refresh.token_hash == hash_refresh(tokens["refresh_token"])
    assert refresh.token_hash != tokens["refresh_token"]
    consents = list(db.scalars(select(Consent)))
    assert [c.kind for c in consents] == ["APPLICATION_USE"]
    credentials = {k: registration[k] for k in ("email", "password")}
    assert client.post("/api/v1/auth/login", json=credentials).status_code == 200
    credentials["password"] = "incorrect-but-long-enough"
    assert client.post("/api/v1/auth/login", json=credentials).status_code == 401


def test_registration_cannot_grant_role_or_research_consent(client, registration):
    assert (
        client.post("/api/v1/auth/register", json={**registration, "role": "ADMIN"}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/auth/register", json={**registration, "application_consent": False}
        ).status_code
        == 422
    )
    assert client.post("/api/v1/auth/register", json=registration).status_code == 201
    assert client.post("/api/v1/auth/register", json=registration).status_code == 409
    assert (
        client.post(
            "/api/v1/auth/register", json={**registration, "email": "PATIENT@example.com"}
        ).status_code
        == 409
    )


def test_rotation_replay_revokes_descendants(client, registration):
    original = client.post("/api/v1/auth/register", json=registration).json()
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != original["refresh_token"]
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": original["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
        ).status_code
        == 401
    )


def test_logout_only_revokes_owned_family(client, registration):
    first = client.post("/api/v1/auth/register", json=registration).json()
    second = client.post(
        "/api/v1/auth/register", json={**registration, "email": "other@example.com"}
    ).json()
    assert (
        client.post(
            "/api/v1/auth/logout",
            headers=headers(second),
            json={"refresh_token": first["refresh_token"]},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/logout",
            headers=headers(second),
            json={"refresh_token": second["refresh_token"]},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
        ).status_code
        == 401
    )


def test_expired_refresh_is_rejected(client, db, registration):
    tokens = client.post("/api/v1/auth/register", json=registration).json()
    token = db.scalar(select(RefreshToken))
    token.expires_at = utcnow() - timedelta(seconds=1)
    db.commit()
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )


def test_rbac_uses_database_role(client, db, registration):
    tokens = client.post("/api/v1/auth/register", json=registration).json()
    assert client.get("/api/v1/dermatologist/access", headers=headers(tokens)).status_code == 403
    user = db.scalar(select(User))
    user.role = "DERMATOLOGIST"
    db.commit()
    assert client.get("/api/v1/dermatologist/access", headers=headers(tokens)).status_code == 200
    user.role = "USER"
    db.commit()
    assert client.get("/api/v1/dermatologist/access", headers=headers(tokens)).status_code == 403


def test_invalid_expired_and_wrong_type_jwt(client, registration):
    tokens = client.post("/api/v1/auth/register", json=registration).json()
    settings = get_settings()
    payload = jwt.decode(
        tokens["access_token"],
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience,
    )
    for patch in ({"exp": 0}, {"type": "refresh"}, {"iss": "other"}, {"sub": "invalid-uuid"}):
        forged = jwt.encode({**payload, **patch}, settings.jwt_secret, algorithm="HS256")
        assert (
            client.get("/api/v1/me", headers={"Authorization": f"Bearer {forged}"}).status_code
            == 401
        )
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_profile_isolation(client, registration):
    first = client.post("/api/v1/auth/register", json=registration).json()
    second = client.post(
        "/api/v1/auth/register", json={**registration, "email": "other@example.com"}
    ).json()
    assert (
        client.patch(
            "/api/v1/me", headers=headers(first), json={"display_name": "Awa", "language": "fr"}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/me/profile", headers=headers(second)).json()["display_name"] == ""
    assert client.get("/api/v1/me/profile", headers=headers(first)).json()["display_name"] == "Awa"
