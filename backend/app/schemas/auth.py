"""
Pydantic schemas for Authentication, Profile and Goals.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    token: str
    usuario_id: str
    nome_exibicao: str
    tema: str
    email: str


class LogoutRequest(BaseModel):
    token: str


# ── Perfil ────────────────────────────────────────────────────────────────────
class PerfilResponse(BaseModel):
    usuario_id: str
    nome: str
    nome_exibicao: str
    email: str
    foto_url: str | None
    tema: str
    meses_historico: int

    model_config = ConfigDict(from_attributes=True)


class PerfilUpdate(BaseModel):
    nome_exibicao: str | None = Field(default=None, min_length=1, max_length=60)
    foto_url: str | None = None
    tema: Literal["dark", "light"] | None = None
    meses_historico: int | None = Field(default=None, ge=1, le=60)


# ── Histórico ─────────────────────────────────────────────────────────────────
class CicloResumo(BaseModel):
    ciclo_id: int
    ano: int
    mes: int
    renda_total: float
    total_gasto: float
    saldo_livre: float
    taxa_poupanca: float

    model_config = ConfigDict(from_attributes=True)


# ── Metas ─────────────────────────────────────────────────────────────────────
class MetaCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=120)
    descricao: str | None = None
    valor_alvo: Decimal = Field(..., gt=Decimal("0.00"))
    valor_atual: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    prazo: date
    categoria_id: int | None = None


class MetaUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    valor_atual: Decimal | None = None
    prazo: date | None = None
    status: Literal["ativa", "concluida", "cancelada"] | None = None
    ia_dicas: str | None = None


class MetaResponse(BaseModel):
    id: int
    usuario_id: str
    titulo: str
    descricao: str | None
    valor_alvo: float
    valor_atual: float
    prazo: date
    categoria_id: int | None
    status: str
    ia_dicas: str | None
    created_at: datetime
    percentual: float  # valor_atual / valor_alvo * 100

    model_config = ConfigDict(from_attributes=True)
