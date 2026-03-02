"""
MetasService — CRUD for financial goals.
"""
import json
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.auth import MetaCreate, MetaResponse, MetaUpdate


class MetasService:

    def _row_to_meta(self, row: dict) -> MetaResponse:
        val_alvo = float(row["valor_alvo"])
        val_atual = float(row["valor_atual"])
        return MetaResponse(
            id=row["id"],
            usuario_id=str(row["usuario_id"]),
            titulo=row["titulo"],
            descricao=row["descricao"],
            valor_alvo=val_alvo,
            valor_atual=val_atual,
            prazo=row["prazo"],
            categoria_id=row["categoria_id"],
            status=row["status"],
            ia_dicas=row["ia_dicas"],
            created_at=row["created_at"],
            percentual=round((val_atual / val_alvo * 100), 2) if val_alvo > 0 else 0.0,
        )

    def list_metas(self, db: Session, usuario_id: str) -> list[MetaResponse]:
        rows = db.execute(
            text("""
                SELECT id, usuario_id, titulo, descricao, valor_alvo, valor_atual,
                       prazo, categoria_id, status, ia_dicas, created_at
                FROM metas
                WHERE usuario_id = :uid
                ORDER BY status = 'ativa' DESC, prazo ASC
            """),
            {"uid": usuario_id},
        ).mappings().all()
        return [self._row_to_meta(dict(r)) for r in rows]

    def create_meta(self, db: Session, usuario_id: str, payload: MetaCreate) -> MetaResponse:
        result = db.execute(
            text("""
                INSERT INTO metas (usuario_id, titulo, descricao, valor_alvo,
                                   valor_atual, prazo, categoria_id)
                VALUES (:uid, :titulo, :descricao, :valor_alvo,
                        :valor_atual, :prazo, :cat_id)
            """),
            {
                "uid": usuario_id,
                "titulo": payload.titulo,
                "descricao": payload.descricao,
                "valor_alvo": float(payload.valor_alvo),
                "valor_atual": float(payload.valor_atual),
                "prazo": payload.prazo.isoformat(),
                "cat_id": payload.categoria_id,
            },
        )
        db.commit()
        new_id = result.lastrowid

        row = db.execute(
            text("SELECT * FROM metas WHERE id = :id"),
            {"id": new_id},
        ).mappings().first()
        return self._row_to_meta(dict(row))

    def update_meta(self, db: Session, meta_id: int, usuario_id: str, payload: MetaUpdate) -> MetaResponse:
        fields: dict = {}
        if payload.titulo is not None: fields["titulo"] = payload.titulo
        if payload.descricao is not None: fields["descricao"] = payload.descricao
        if payload.valor_atual is not None: fields["valor_atual"] = float(payload.valor_atual)
        if payload.prazo is not None: fields["prazo"] = payload.prazo.isoformat()
        if payload.status is not None: fields["status"] = payload.status
        if payload.ia_dicas is not None: fields["ia_dicas"] = payload.ia_dicas

        if fields:
            set_clause = ", ".join(f"{k} = :{k}" for k in fields)
            fields["id"] = meta_id
            fields["uid"] = usuario_id
            db.execute(
                text(f"UPDATE metas SET {set_clause} WHERE id = :id AND usuario_id = :uid"),
                fields,
            )
            db.commit()

        row = db.execute(text("SELECT * FROM metas WHERE id = :id"), {"id": meta_id}).mappings().first()
        return self._row_to_meta(dict(row))

    def delete_meta(self, db: Session, meta_id: int, usuario_id: str):
        db.execute(text("DELETE FROM metas WHERE id = :id AND usuario_id = :uid"), {"id": meta_id, "uid": usuario_id})
        db.commit()
