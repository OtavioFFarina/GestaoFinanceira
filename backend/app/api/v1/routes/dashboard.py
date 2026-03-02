"""
Dashboard routes — GET /api/dashboard/{usuario_id}/{ano}/{mes}
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
_service = DashboardService()


@router.get(
    "/{usuario_id}/{ano}/{mes}",
    response_model=DashboardResponse,
    summary="Retorna os dados do dashboard de um ciclo mensal.",
)
def get_dashboard(
    usuario_id: str,
    ano: int,
    mes: int,
    db: Session = Depends(get_db),
) -> DashboardResponse:
    if not (1 <= mes <= 12):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mês deve ser entre 1 e 12.",
        )
    return _service.get_dashboard(db, usuario_id, ano, mes)
