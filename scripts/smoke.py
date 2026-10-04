"""Vérifie le système Compose démarré, sur des comptes fictifs uniquement."""

import json
import os
import secrets
from urllib.error import HTTPError
from urllib.request import Request, urlopen

base = os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:8000")


def call(
    path: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    expected: int = 200,
) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        base + path,
        method=method,
        headers=headers,
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        if response.status != expected:
            raise RuntimeError(
                f"{method} {path}: HTTP {response.status}, attendu {expected}"
            )
        raw = response.read()
        return json.loads(raw) if raw else {}


def main() -> None:
    ready = call("/health/ready")
    assert all(ready["checks"].values())
    call("/openapi.json")
    call("/api/v1/me", expected=401)
    credentials = {
        "email": f"smoke-{secrets.token_hex(8)}@example.com",
        "password": secrets.token_urlsafe(24),
        "application_consent": True,
    }
    tokens = call(
        "/api/v1/auth/register", method="POST", body=credentials, expected=201
    )
    token = tokens["access_token"]
    assert call("/api/v1/me", token=token)["role"] == "USER"
    call("/api/v1/dermatologist/access", token=token, expected=403)
    new = call(
        "/api/v1/auth/refresh",
        method="POST",
        body={"refresh_token": tokens["refresh_token"]},
    )
    call(
        "/api/v1/auth/logout",
        method="POST",
        token=new["access_token"],
        body={"refresh_token": new["refresh_token"]},
        expected=204,
    )
    call(
        "/api/v1/auth/refresh",
        method="POST",
        body={"refresh_token": new["refresh_token"]},
        expected=401,
    )
    print("Smoke OK : PostgreSQL migré, Redis, bucket privé, API et authentification.")


if __name__ == "__main__":
    main()
