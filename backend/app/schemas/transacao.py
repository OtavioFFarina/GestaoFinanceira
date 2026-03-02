"""
Updated Transacao schemas with meta_id support and full response for list view.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransacaoCreate(BaseModel):
    """Body for POST /api/transacoes"""
    ciclo_id: int = Field(..., gt=0)
    categoria_id: int = Field(..., gt=0)
    meta_id: int | None = None  # Optional: link investment to a goal
    descricao: str = Field(..., min_length=1, max_length=255)
    valor: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    tipo: Literal["entrada", "saida"]
    data_transacao: date
    recorrente: bool = False
    observacoes: str | None = Field(default=None, max_length=2000)

    @field_validator("valor")
    @classmethod
    def valor_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("O valor da transação deve ser maior que zero.")
        return v


class TransacaoUpdate(BaseModel):
    """Body for PATCH /api/transacoes/{id}"""
    descricao: str | None = None
    valor: Decimal | None = None
    data_transacao: date | None = None
    observacoes: str | None = None
    meta_id: int | None = None


class TransacaoDetalhe(BaseModel):
    """Full transaction detail response for list modals."""
    id: int
    ciclo_id: int
    categoria_id: int
    categoria_nome: str
    categoria_cor: str | None
    meta_id: int | None
    meta_titulo: str | None
    descricao: str
    valor: float
    tipo: str
    data_transacao: date
    recorrente: bool
    observacoes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransacaoResponse(BaseModel):
    """Response after creating a transaction."""
    id: int
    ciclo_id: int
    categoria_id: int
    descricao: str
    valor: Decimal
    tipo: str
    data_transacao: date
    recorrente: bool

    model_config = ConfigDict(from_attributes=True)


class CicloCreate(BaseModel):
    """Body for POST /api/ciclos — create or update a monthly cycle."""
    usuario_id: str = Field(..., min_length=36, max_length=36)
    ano: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    renda_total: Decimal = Field(..., ge=Decimal("0.00"), decimal_places=2)
    observacoes: str | None = None


class CicloResponse(BaseModel):
    """Response after creating/updating a monthly cycle."""
    id: int
    usuario_id: str
    ano: int
    mes: int
    renda_total: Decimal
    fechado: bool

    model_config = ConfigDict(from_attributes=True)


class CategoriaPublica(BaseModel):
    """Used to populate category selects in the frontend modals."""
    id: int
    nome: str
    slug: str
    cor_hex: str | None
    icone: str | None
    tipo: str

    model_config = ConfigDict(from_attributes=True)


class ReservaResponse(BaseModel):
    """Emergency reserve summary."""
    saldo_total: float
    total_aportes: int
    ultimo_aporte: date | None
    historico: list[dict]  # [{mes, ano, valor}]
