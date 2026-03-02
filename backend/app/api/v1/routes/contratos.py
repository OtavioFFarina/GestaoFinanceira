"""
Contratos Financeiros — Contas a Pagar e Contas a Receber.
Routes:
  POST   /contratos                           → criar contrato + parcelas
  GET    /contratos/{usuario_id}              → listar (query: tipo=pagar|receber)
  GET    /contratos/{usuario_id}/resumo       → totais para cards de resumo
  GET    /contratos/detalhe/{contrato_id}     → detalhe com parcelas
  PATCH  /parcelas/{parcela_id}/baixa         → dar baixa (marcar como paga)
  DELETE /contratos/{contrato_id}             → excluir contrato
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.contratos import (
    BaixaResponse,
    ContratoCreate,
    ContratoListItem,
    ContratoResponse,
    ResumoContratos,
)
from app.services.contratos_service import ContratosService

router = APIRouter(tags=["Contratos Financeiros"])
_svc = ContratosService()


# ── Criar contrato ────────────────────────────────────────────────────────────
@router.post("/contratos", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
def create_contrato(payload: ContratoCreate, db: Session = Depends(get_db)) -> ContratoResponse:
    """Cria um contrato e gera automaticamente as parcelas parceladas."""
    return _svc.create_contrato(db, payload)


# ── Listar parcelas pendentes pagar (para modal do dashboard) ────────────────
@router.get("/contratos/{usuario_id}/parcelas-pendentes")
def list_parcelas_pendentes(usuario_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Retorna parcelas pendentes de contratos 'pagar' para exibir no dropdown do modal."""
    _svc._sync_atrasadas(db, usuario_id)
    return _svc.list_parcelas_pendentes_pagar(db, usuario_id)


# ── Listar contratos de um usuário ────────────────────────────────────────────
@router.get("/contratos/{usuario_id}", response_model=list[ContratoListItem])
def list_contratos(
    usuario_id: str,
    tipo: Optional[str] = Query(default=None, description="Filtrar por tipo: pagar | receber"),
    db: Session = Depends(get_db),
) -> list[ContratoListItem]:
    """Lista contratos com contagem de parcelas por status."""
    _svc._sync_atrasadas(db, usuario_id)
    return _svc.list_contratos(db, usuario_id, tipo)


# ── Resumo para cards de resumo ───────────────────────────────────────────────
@router.get("/contratos/{usuario_id}/resumo", response_model=ResumoContratos)
def get_resumo(usuario_id: str, db: Session = Depends(get_db)) -> ResumoContratos:
    """Retorna totais do mês atual para os cards de Contas a Pagar e a Receber."""
    _svc._sync_atrasadas(db, usuario_id)
    return _svc.get_resumo(db, usuario_id)


# ── Detalhe de um contrato ────────────────────────────────────────────────────
@router.get("/contratos/detalhe/{contrato_id}", response_model=ContratoResponse)
def get_contrato(contrato_id: int, db: Session = Depends(get_db)) -> ContratoResponse:
    """Retorna contrato completo com todas as parcelas."""
    return _svc.get_contrato(db, contrato_id)


# ── Dar baixa em parcela ──────────────────────────────────────────────────────
@router.patch("/parcelas/{parcela_id}/baixa", response_model=BaixaResponse)
def baixar_parcela(parcela_id: int, db: Session = Depends(get_db)) -> BaixaResponse:
    """Marca uma parcela como paga (data_pagamento = hoje)."""
    return _svc.baixar_parcela(db, parcela_id)


# ── Excluir contrato ──────────────────────────────────────────────────────────
@router.delete("/contratos/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrato(contrato_id: int, db: Session = Depends(get_db)) -> None:
    """Exclui um contrato e todas as suas parcelas (CASCADE)."""
    _svc.delete_contrato(db, contrato_id)
