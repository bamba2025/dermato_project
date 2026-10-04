"""Comptes de développement uniquement, mot de passe fourni par l'environnement."""

import os

from sqlalchemy import select

from app.auth.security import password_hash
from app.core.config import get_settings
from app.core.database import session_factory
from app.models import User, UserProfile


def main() -> None:
    if get_settings().environment != "development":
        raise RuntimeError("Seed interdit hors développement")
    password = os.environ.get("SEED_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError("Définissez SEED_PASSWORD (au moins 12 caractères)")
    with session_factory()() as db:
        for email, role in (
            ("patient@example.com", "USER"),
            ("dermatologue@example.com", "DERMATOLOGIST"),
        ):
            if not db.scalar(select(User).where(User.email == email)):
                user = User(email=email, role=role, password_hash=password_hash.hash(password))
                db.add(user)
                db.flush()
                db.add(UserProfile(user_id=user.id, display_name="Compte de démonstration"))
        db.commit()
    print("Seed terminé : comptes fictifs uniquement.")


if __name__ == "__main__":
    main()
