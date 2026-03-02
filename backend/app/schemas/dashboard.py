"""
Pydantic schemas for Dashboard API responses.
Using float instead of Decimal for JSON serialization (numbers, not strings).
"""
from pydantic import BaseModel, ConfigDict


class CategoriaAlocacao(BaseModel):
    categoria_id: int
    categoria: str
    slug: str
    cor_hex: str | None
    valor_planejado: float
    percentual_planejado: float
    valor_realizado: float
    percentual_realizado: float

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    ciclo_id: int | None
    usuario_id: str
    ano: int
    mes: int
    renda_total: float
    total_gasto: float
    saldo_livre: float
    taxa_poupanca: float
    alocacoes: list[CategoriaAlocacao]

    model_config = ConfigDict(from_attributes=True)
