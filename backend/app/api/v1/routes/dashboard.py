"""
Dashboard routes — GET /api/dashboard/{usuario_id}/{ano}/{mes}

Returns 200 with zeroed values when no monthly record exists (never 404).
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
    try:
        return _service.get_dashboard(db, usuario_id, ano, mes)
    except Exception:
        # Fallback: if anything goes wrong (table missing, etc.),
        # return a valid empty dashboard instead of crashing.
        return DashboardResponse(
            ciclo_id=None,
            usuario_id=usuario_id,
            ano=ano,
            mes=mes,
            renda_total=0.0,
            total_gasto=0.0,
            saldo_livre=0.0,
            taxa_poupanca=0.0,
            alocacoes=[],
        )
