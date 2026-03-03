"""
AuthService — handles registration, login (bcrypt verify), session creation and logout.
Fully ORM-based, no raw SQL.
"""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_session import UserSession
from app.models.user_profile import UserProfile
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest


class AuthService:

    def register(self, db: Session, payload: RegisterRequest) -> None:
        # 1. Check if email already exists
        existing = db.execute(
            select(User).where(User.email == payload.email.lower().strip())
        ).scalar_one_or_none()

        if existing:
            raise ValueError("Este e-mail já está em uso.")

        # 2. Hash password and create user
        user = User(
            name=payload.nome.strip(),
            email=payload.email.lower().strip(),
            hashed_password=self.hash_password(payload.senha),
        )
        db.add(user)
        db.commit()

    def login(self, db: Session, payload: LoginRequest) -> LoginResponse:
        # 1. Find user by email
        user = db.execute(
            select(User).where(User.email == payload.email)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("Email ou senha inválidos.")

        # 2. Verify password
        if not bcrypt.checkpw(payload.senha.encode(), user.hashed_password.encode()):
            raise ValueError("Email ou senha inválidos.")

        # 3. Get display profile
        profile = db.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        ).scalar_one_or_none()

        display_name = profile.display_name if profile and profile.display_name else user.name
        theme = profile.theme if profile else "dark"

        # 4. Create session token (64-char hex)
        token = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        session = UserSession(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()

        return LoginResponse(
            token=token,
            usuario_id=str(user.id),
            nome_exibicao=display_name,
            tema=theme,
            email=str(user.email),
        )

    def logout(self, db: Session, token: str) -> None:
        session = db.execute(
            select(UserSession).where(UserSession.token == token)
        ).scalar_one_or_none()
        if session:
            db.delete(session)
            db.commit()

    def verify_token(self, db: Session, token: str) -> str | None:
        """Returns user_id if token is valid and not expired, else None."""
        session = db.execute(
            select(UserSession).where(
                UserSession.token == token,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        ).scalar_one_or_none()
        return str(session.user_id) if session else None

    @staticmethod
    def hash_password(senha: str) -> str:
        return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()
