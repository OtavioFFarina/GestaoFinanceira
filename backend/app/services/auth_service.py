"""
AuthService — handles login (bcrypt verify), session creation and logout.
Uses stateless token stored in DB (sessoes table).
"""
import hashlib
import os
import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.auth import LoginRequest, LoginResponse, PerfilResponse, RegisterRequest


class AuthService:

    def register(self, db: Session, payload: RegisterRequest) -> None:
        # 1. Check if email already exists
        exists = db.execute(
            text("SELECT id FROM usuarios WHERE email = :email"),
            {"email": payload.email}
        ).fetchone()
        
        if exists:
            raise ValueError("Este e-mail já está em uso.")

        # 2. Hash password
        senha_hash = self.hash_password(payload.senha)

        # 3. Create user
        db.execute(
            text("""
                INSERT INTO usuarios (nome, email, senha_hash)
                VALUES (:nome, :email, :senha_hash)
            """),
            {
                "nome": payload.nome.strip(),
                "email": payload.email.lower().strip(),
                "senha_hash": senha_hash
            }
        )
        db.commit()

    def login(self, db: Session, payload: LoginRequest) -> LoginResponse:
        # 1. Find user by email
        user = db.execute(
            text("SELECT id, nome, email, senha_hash, ativo FROM usuarios WHERE email = :email"),
            {"email": payload.email},
        ).mappings().first()

        if not user or not user["ativo"]:
            raise ValueError("Email ou senha inválidos.")

        # 2. Verify password
        if not bcrypt.checkpw(payload.senha.encode(), user["senha_hash"].encode()):
            raise ValueError("Email ou senha inválidos.")

        # 3. Get display profile
        perfil = db.execute(
            text("SELECT nome_exibicao, tema FROM perfil_usuario WHERE usuario_id = :uid"),
            {"uid": user["id"]},
        ).mappings().first()

        nome_exibicao = perfil["nome_exibicao"] if perfil else user["nome"]
        tema = perfil["tema"] if perfil else "dark"

        # 4. Create session token (64-char hex)
        token = secrets.token_hex(32)
        expires_at = datetime.utcnow() + timedelta(days=30)

        db.execute(
            text("""
                INSERT INTO sessoes (usuario_id, token, expires_at)
                VALUES (:uid, :token, :exp)
            """),
            {"uid": user["id"], "token": token, "exp": expires_at},
        )
        db.commit()

        return LoginResponse(
            token=token,
            usuario_id=str(user["id"]),
            nome_exibicao=nome_exibicao,
            tema=tema,
            email=str(user["email"]),
        )

    def logout(self, db: Session, token: str) -> None:
        db.execute(text("DELETE FROM sessoes WHERE token = :token"), {"token": token})
        db.commit()

    def verify_token(self, db: Session, token: str) -> str | None:
        """Returns usuario_id if token is valid and not expired, else None."""
        row = db.execute(
            text("""
                SELECT usuario_id FROM sessoes
                WHERE token = :token AND expires_at > NOW()
            """),
            {"token": token},
        ).mappings().first()
        return str(row["usuario_id"]) if row else None

    @staticmethod
    def hash_password(senha: str) -> str:
        return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(rounds=12)).decode()
