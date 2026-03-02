"""Historico routes: GET /historico/{usuario_id}"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import CicloResumo
from app.services.historico_service import HistoricoService

router = APIRouter(prefix="/historico", tags=["Histórico"])
_svc = HistoricoService()


@router.get("/{usuario_id}", response_model=list[CicloResumo])
def get_historico(usuario_id: str, db: Session = Depends(get_db)) -> list[CicloResumo]:
    return _svc.get_historico(db, usuario_id)
