"""
Pydantic schemas for Contratos Financeiros (Contas a Pagar / Receber) module.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Parcela ───────────────────────────────────────────────────────────────────

class ParcelaResponse(BaseModel):
    id: str
    contrato_id: str
    numero_parcela: int
    valor_parcela: float
    data_vencimento: date
    data_pagamento: Optional[date]
    status: str

    model_config = ConfigDict(from_attributes=True)


# ── Contrato ──────────────────────────────────────────────────────────────────

class ContratoCreate(BaseModel):
    """Payload para criar um contrato com parcelamento automático."""
    usuario_id: str = Field(..., min_length=36, max_length=36)
    tipo: Literal["pagar", "receber"]
    descricao: str = Field(..., min_length=1, max_length=255)
    valor_total: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    num_parcelas: int = Field(..., ge=1, le=60)
    data_primeiro_vencimento: date
    observacoes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("valor_total")
    @classmethod
    def valor_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("O valor total deve ser maior que zero.")
        return v


class ContratoResponse(BaseModel):
    """Resposta completa de um contrato com suas parcelas."""
    id: str
    usuario_id: str
    tipo: str
    descricao: str
    valor_total: float
    num_parcelas: int
    data_primeiro_vencimento: date
    status: str
    observacoes: Optional[str]
    created_at: datetime
    parcelas: list[ParcelaResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ContratoListItem(BaseModel):
    """Item resumido para listagem de contratos."""
    id: str
    tipo: str
    descricao: str
    valor_total: float
    num_parcelas: int
    status: str
    data_primeiro_vencimento: date
    parcelas_pagas: int
    parcelas_pendentes: int
    parcelas_atrasadas: int
    proximo_vencimento: Optional[date]
    proximo_valor: Optional[float]

    model_config = ConfigDict(from_attributes=True)


# ── Baixa de Parcela ──────────────────────────────────────────────────────────

class BaixaResponse(BaseModel):
    """Retorno após dar baixa em uma parcela."""
    parcela_id: str
    status: str
    data_pagamento: date
    contrato_quitado: bool  # True se todas as parcelas foram pagas


# ── Resumo (Cards do Dashboard) ───────────────────────────────────────────────

class ResumoContratos(BaseModel):
    """Totais para os cards de resumo das páginas de dívidas/receber."""
    # Pagar
    total_pagar_mes: float
    contratos_pagar_ativos: int
    proximo_vencimento_pagar: Optional[date]
    # Receber
    total_receber_mes: float
    contratos_receber_ativos: int
    proximo_vencimento_receber: Optional[date]
