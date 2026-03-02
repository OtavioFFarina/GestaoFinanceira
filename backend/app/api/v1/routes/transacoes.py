"""
Transaction, cycle, category and reserve routes.
Added: GET /transacoes/{ciclo_id}, PATCH /transacoes/{id}, DELETE /transacoes/{id},
       GET /reserva/{usuario_id}
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.transacao import (
    CategoriaPublica,
    CicloCreate,
    CicloResponse,
    ReservaResponse,
    TransacaoCreate,
    TransacaoDetalhe,
    TransacaoResponse,
    TransacaoUpdate,
)
from app.services.transacao_service import TransacaoService

router = APIRouter(tags=["Transações"])
_service = TransacaoService()


# ── Create transaction ────────────────────────────────────────────────────────
@router.post("/transacoes", response_model=TransacaoResponse, status_code=status.HTTP_201_CREATED)
def create_transacao(payload: TransacaoCreate, db: Session = Depends(get_db)) -> TransacaoResponse:
    return _service.create_transacao(db, payload)


# ── List transactions for a cycle ─────────────────────────────────────────────
@router.get("/transacoes/{ciclo_id}", response_model=list[TransacaoDetalhe])
def list_transacoes(ciclo_id: int, db: Session = Depends(get_db)) -> list[TransacaoDetalhe]:
    return _service.list_transacoes(db, ciclo_id)


# ── Update transaction ────────────────────────────────────────────────────────
@router.patch("/transacoes/{transacao_id}", response_model=TransacaoDetalhe)
def update_transacao(
    transacao_id: int, payload: TransacaoUpdate, db: Session = Depends(get_db)
) -> TransacaoDetalhe:
    return _service.update_transacao(db, transacao_id, payload)


# ── Delete transaction ────────────────────────────────────────────────────────
@router.delete("/transacoes/{transacao_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transacao(transacao_id: int, db: Session = Depends(get_db)) -> None:
    _service.delete_transacao(db, transacao_id)


# ── Upsert monthly cycle ──────────────────────────────────────────────────────
@router.post("/ciclos", response_model=CicloResponse, status_code=status.HTTP_200_OK)
def upsert_ciclo(payload: CicloCreate, db: Session = Depends(get_db)) -> CicloResponse:
    return _service.upsert_ciclo(db, payload)


# ── List categories ───────────────────────────────────────────────────────────
@router.get("/categorias", response_model=list[CategoriaPublica])
def list_categorias(
    tipo: str | None = Query(default=None, description="Filtrar por tipo: entrada | saida"),
    db: Session = Depends(get_db),
) -> list[CategoriaPublica]:
    return _service.list_categorias(db, tipo)


# ── Reserva (emergency fund) ──────────────────────────────────────────────────
@router.get("/reserva/{usuario_id}", response_model=ReservaResponse)
def get_reserva(usuario_id: str, db: Session = Depends(get_db)) -> ReservaResponse:
    return _service.get_reserva(db, usuario_id)
