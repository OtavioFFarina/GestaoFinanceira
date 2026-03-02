"""Metas routes: GET/POST /metas, PATCH /metas/{id}"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import MetaCreate, MetaResponse, MetaUpdate
from app.services.metas_service import MetasService

router = APIRouter(prefix="/metas", tags=["Metas"])
_svc = MetasService()


@router.get("/{usuario_id}", response_model=list[MetaResponse])
def list_metas(usuario_id: str, db: Session = Depends(get_db)) -> list[MetaResponse]:
    return _svc.list_metas(db, usuario_id)


@router.post("/{usuario_id}", response_model=MetaResponse, status_code=status.HTTP_201_CREATED)
def create_meta(usuario_id: str, payload: MetaCreate, db: Session = Depends(get_db)) -> MetaResponse:
    return _svc.create_meta(db, usuario_id, payload)


@router.patch("/{usuario_id}/{meta_id}", response_model=MetaResponse)
def update_meta(usuario_id: str, meta_id: int, payload: MetaUpdate, db: Session = Depends(get_db)) -> MetaResponse:
    return _svc.update_meta(db, meta_id, usuario_id, payload)

@router.delete("/{usuario_id}/{meta_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meta(usuario_id: str, meta_id: int, db: Session = Depends(get_db)):
    _svc.delete_meta(db, meta_id, usuario_id)
    return None
