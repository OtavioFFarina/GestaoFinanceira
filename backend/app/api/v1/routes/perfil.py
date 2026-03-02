"""Perfil routes: GET/PATCH /perfil/{usuario_id}"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import PerfilResponse, PerfilUpdate
from app.services.perfil_service import PerfilService

router = APIRouter(prefix="/perfil", tags=["Perfil"])
_svc = PerfilService()


@router.get("/{usuario_id}", response_model=PerfilResponse)
def get_perfil(usuario_id: str, db: Session = Depends(get_db)) -> PerfilResponse:
    try:
        return _svc.get_perfil(db, usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{usuario_id}", response_model=PerfilResponse)
def update_perfil(usuario_id: str, payload: PerfilUpdate, db: Session = Depends(get_db)) -> PerfilResponse:
    try:
        return _svc.update_perfil(db, usuario_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{usuario_id}/dados", status_code=status.HTTP_204_NO_CONTENT)
def delete_dados(usuario_id: str, db: Session = Depends(get_db)):
    try:
        _svc.delete_dados(db, usuario_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
