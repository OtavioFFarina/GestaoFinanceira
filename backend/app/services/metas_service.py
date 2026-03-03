"""
MetasService — CRUD for financial goals using ORM.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.schemas.auth import MetaCreate, MetaResponse, MetaUpdate


class MetasService:

    def _goal_to_meta(self, goal: Goal) -> MetaResponse:
        val_alvo = float(goal.target_amount)
        val_atual = float(goal.current_amount)
        return MetaResponse(
            id=goal.id,
            usuario_id=str(goal.user_id),
            titulo=goal.title,
            descricao=goal.description,
            valor_alvo=val_alvo,
            valor_atual=val_atual,
            prazo=goal.deadline,
            categoria_id=goal.category_id,
            status=goal.status.value if goal.status else "ativa",
            ia_dicas=goal.ai_tips,
            created_at=goal.created_at,
            percentual=round((val_atual / val_alvo * 100), 2) if val_alvo > 0 else 0.0,
        )

    def list_metas(self, db: Session, usuario_id: str) -> list[MetaResponse]:
        goals = db.execute(
            select(Goal)
            .where(Goal.user_id == usuario_id)
            .order_by(
                (Goal.status == "ativa").desc(),
                Goal.deadline.asc(),
            )
        ).scalars().all()
        return [self._goal_to_meta(g) for g in goals]

    def create_meta(self, db: Session, usuario_id: str, payload: MetaCreate) -> MetaResponse:
        goal = Goal(
            user_id=usuario_id,
            title=payload.titulo,
            description=payload.descricao,
            target_amount=float(payload.valor_alvo),
            current_amount=float(payload.valor_atual),
            deadline=payload.prazo,
            category_id=payload.categoria_id,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return self._goal_to_meta(goal)

    def update_meta(self, db: Session, meta_id: str, usuario_id: str, payload: MetaUpdate) -> MetaResponse:
        goal = db.execute(
            select(Goal).where(Goal.id == meta_id, Goal.user_id == usuario_id)
        ).scalar_one_or_none()

        if not goal:
            raise ValueError("Meta não encontrada.")

        if payload.titulo is not None:
            goal.title = payload.titulo
        if payload.descricao is not None:
            goal.description = payload.descricao
        if payload.valor_atual is not None:
            goal.current_amount = float(payload.valor_atual)
        if payload.prazo is not None:
            goal.deadline = payload.prazo
        if payload.status is not None:
            goal.status = payload.status
        if payload.ia_dicas is not None:
            goal.ai_tips = payload.ia_dicas

        db.commit()
        db.refresh(goal)
        return self._goal_to_meta(goal)

    def delete_meta(self, db: Session, meta_id: str, usuario_id: str):
        goal = db.execute(
            select(Goal).where(Goal.id == meta_id, Goal.user_id == usuario_id)
        ).scalar_one_or_none()
        if goal:
            db.delete(goal)
            db.commit()
